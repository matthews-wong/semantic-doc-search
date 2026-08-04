"""Corpus loading, index building, and querying.

The :class:`SearchIndex` ties a corpus of documents to an :class:`Embedder`
backend. Documents are embedded once at build time; queries are embedded on the
fly and ranked against the corpus by cosine similarity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

from app.embedder import Embedder, TfidfEmbedder


@dataclass(frozen=True)
class Document:
    """A single indexed document.

    Attributes:
        doc_id: Stable identifier (the source file stem).
        title: Human-readable title (first Markdown H1, or the doc_id).
        text: Full document text used for embedding.
    """

    doc_id: str
    title: str
    text: str


@dataclass(frozen=True)
class SearchResult:
    """One ranked hit for a query."""

    doc_id: str
    title: str
    score: float
    snippet: str


def _extract_title(doc_id: str, text: str) -> str:
    """Return the first Markdown H1 heading, falling back to ``doc_id``."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return doc_id


_TERM_RE = re.compile(r"[a-z0-9]+")


def extract_query_terms(query: str) -> list[str]:
    """Return the distinct lowercase word tokens of ``query`` worth matching.

    Single-character tokens and English stop words are dropped so the terms
    that survive are the ones the TF-IDF backend actually ranks on -- the same
    words worth centring a passage on and highlighting. Order is preserved so
    the UI highlights predictably.
    """
    seen: dict[str, None] = {}
    for token in _TERM_RE.findall(query.lower()):
        if len(token) > 1 and token not in ENGLISH_STOP_WORDS:
            seen.setdefault(token, None)
    return list(seen)


def _passage_window(text: str, pos: int, max_chars: int) -> str:
    """Extract a ``max_chars`` window of ``text`` centred on ``pos``.

    Boundaries snap to whitespace so words are not cut mid-token, and ellipses
    mark where text was trimmed from either side.
    """
    start = max(0, pos - max_chars // 2)
    end = min(len(text), start + max_chars)
    start = max(0, end - max_chars)
    if start > 0:
        nxt = text.find(" ", start)
        if 0 <= nxt <= pos:
            start = nxt + 1
    if end < len(text):
        prev = text.rfind(" ", 0, end)
        if prev > pos:
            end = prev
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "... " + snippet
    if end < len(text):
        snippet = snippet + " ..."
    return snippet


def _make_snippet(text: str, query: str | None = None, max_chars: int = 200) -> str:
    """Build a short single-line preview of a document.

    When ``query`` matches text in the document, the preview is centred on the
    first matching passage rather than the document head, so results show *why*
    they matched. Falls back to the document head when nothing matches.
    """
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_chars:
        return collapsed

    if query:
        lowered = collapsed.lower()
        first = min(
            (idx for idx in (lowered.find(t) for t in extract_query_terms(query)) if idx != -1),
            default=-1,
        )
        if first != -1:
            return _passage_window(collapsed, first, max_chars)

    return collapsed[:max_chars].rstrip() + "..."


def load_corpus(docs_dir: str | Path) -> list[Document]:
    """Load all Markdown documents from ``docs_dir``.

    Args:
        docs_dir: Directory containing ``*.md`` files.

    Returns:
        Documents sorted by ``doc_id`` for deterministic ordering.

    Raises:
        FileNotFoundError: If ``docs_dir`` does not exist.
        ValueError: If no ``*.md`` files are found.
    """
    directory = Path(docs_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"Docs directory not found: {directory}")

    documents: list[Document] = []
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        documents.append(
            Document(
                doc_id=path.stem,
                title=_extract_title(path.stem, text),
                text=text,
            )
        )

    if not documents:
        raise ValueError(f"No Markdown documents found in {directory}")
    return documents


class SearchIndex:
    """An in-memory semantic search index over a document corpus."""

    def __init__(self, documents: list[Document], embedder: Embedder | None = None) -> None:
        """Create an index.

        Args:
            documents: Corpus to index. Must be non-empty.
            embedder: Embedding backend. Defaults to :class:`TfidfEmbedder`.

        Raises:
            ValueError: If ``documents`` is empty.
        """
        if not documents:
            raise ValueError("Cannot build a SearchIndex from an empty corpus.")
        self.documents = documents
        self.embedder: Embedder = embedder or TfidfEmbedder()
        self._matrix: np.ndarray | None = None

    @classmethod
    def from_dir(
        cls, docs_dir: str | Path, embedder: Embedder | None = None
    ) -> SearchIndex:
        """Load a corpus from ``docs_dir`` and build the index."""
        index = cls(load_corpus(docs_dir), embedder=embedder)
        return index.build()

    def build(self) -> SearchIndex:
        """Fit the embedder on the corpus and precompute document vectors."""
        texts = [doc.text for doc in self.documents]
        self.embedder.fit(texts)
        self._matrix = self.embedder.encode(texts)
        return self

    def query(self, text: str, k: int = 5) -> list[SearchResult]:
        """Return the ``k`` documents most similar to ``text``.

        Args:
            text: The free-text query.
            k: Maximum number of results to return.

        Returns:
            Results sorted by descending cosine similarity. Empty if the query
            is blank.

        Raises:
            RuntimeError: If the index has not been built.
        """
        if self._matrix is None:
            raise RuntimeError("SearchIndex.query called before build().")
        if not text.strip():
            return []

        k = max(1, min(k, len(self.documents)))
        query_vec = self.embedder.encode([text])
        scores = cosine_similarity(query_vec, self._matrix)[0]

        top_indices = np.argsort(scores)[::-1][:k]
        results: list[SearchResult] = []
        for idx in top_indices:
            doc = self.documents[int(idx)]
            results.append(
                SearchResult(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    score=float(scores[idx]),
                    snippet=_make_snippet(doc.text, query=text),
                )
            )
        return results
