"""Pluggable embedding backends.

The :class:`Embedder` protocol defines the seam between the search index and
whatever turns text into vectors. The shipped default, :class:`TfidfEmbedder`,
uses scikit-learn's TF-IDF vectorizer so the demo runs fully offline with no
model downloads. A real transformer backend (e.g. sentence-transformers) can be
dropped in by implementing the same protocol -- see the README roadmap.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


@runtime_checkable
class Embedder(Protocol):
    """Turns text into dense/sparse numeric vectors for similarity search.

    Implementations must be *fit* on the corpus once (learning any vocabulary
    or state) and then able to *encode* both the corpus and arbitrary queries
    into the same vector space.
    """

    def fit(self, documents: list[str]) -> Embedder:
        """Learn any state (vocabulary, IDF weights, ...) from ``documents``."""
        ...

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode ``texts`` into a 2D float array of shape ``(len(texts), dim)``."""
        ...


class TfidfEmbedder:
    """TF-IDF embedding backend built on scikit-learn.

    This is intentionally simple and dependency-light: it captures lexical
    similarity (shared/related terms) rather than deep semantics, but it is
    reproducible, fast, and requires no network access -- ideal for a demo.
    """

    def __init__(self, **vectorizer_kwargs: object) -> None:
        """Create the embedder.

        Args:
            **vectorizer_kwargs: Forwarded to
                :class:`sklearn.feature_extraction.text.TfidfVectorizer`.
                Sensible defaults (English stop words, 1-2 grams) are applied
                unless overridden.
        """
        defaults: dict[str, object] = {
            "stop_words": "english",
            "ngram_range": (1, 2),
            "sublinear_tf": True,
        }
        defaults.update(vectorizer_kwargs)
        self._vectorizer = TfidfVectorizer(**defaults)
        self._fitted = False

    def fit(self, documents: list[str]) -> TfidfEmbedder:
        """Learn the vocabulary and IDF weights from ``documents``."""
        self._vectorizer.fit(documents)
        self._fitted = True
        return self

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode ``texts`` into an L2-normalized dense matrix.

        Raises:
            RuntimeError: If called before :meth:`fit`.
        """
        if not self._fitted:
            raise RuntimeError("TfidfEmbedder.encode called before fit().")
        matrix = self._vectorizer.transform(texts)
        return matrix.toarray().astype(np.float32)
