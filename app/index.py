"""Corpus loading, index building, and querying.

The :class:`SearchIndex` ties a corpus of documents to an :class:`Embedder`
backend. Documents are embedded once at build time; queries are embedded on the
fly and ranked against the corpus by cosine similarity.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
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


def _make_snippet(text: str, max_chars: int = 200) -> str:
    """Build a short single-line preview of a document."""
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_chars:
        return collapsed
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
                    snippet=_make_snippet(doc.text),
                )
            )
        return results
