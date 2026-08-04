"""Tests for corpus loading, index building, and querying."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.embedder import TfidfEmbedder
from app.index import Document, SearchIndex, load_corpus

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "docs"


@pytest.fixture(scope="module")
def index() -> SearchIndex:
    """A built index over the shipped documentation corpus."""
    return SearchIndex.from_dir(DOCS_DIR)


def test_load_corpus_reads_all_markdown() -> None:
    docs = load_corpus(DOCS_DIR)
    assert len(docs) >= 6
    assert all(isinstance(d, Document) for d in docs)
    assert all(d.text.strip() for d in docs)
    # Titles come from the first H1 heading.
    titles = {d.title for d in docs}
    assert "Kubernetes Health Probes" in titles


def test_load_corpus_missing_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_corpus(tmp_path / "does-not-exist")


def test_load_corpus_empty_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        load_corpus(tmp_path)


def test_empty_corpus_rejected() -> None:
    with pytest.raises(ValueError):
        SearchIndex([])


def test_query_before_build_raises() -> None:
    idx = SearchIndex(load_corpus(DOCS_DIR))
    with pytest.raises(RuntimeError):
        idx.query("anything")


def test_encode_before_fit_raises() -> None:
    with pytest.raises(RuntimeError):
        TfidfEmbedder().encode(["not fitted yet"])


def test_query_returns_semantically_closest_doc(index: SearchIndex) -> None:
    """A topical query should rank its matching doc first."""
    results = index.query("how do I keep a pod healthy and restart it", k=3)
    assert results, "expected at least one result"
    assert results[0].doc_id == "kubernetes-probes"
    # Scores must be sorted descending.
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.parametrize(
    ("query", "expected_doc"),
    [
        ("lock terraform state file in s3 and dynamodb", "terraform-state-locking"),
        ("firing alert rules and alertmanager routing", "prometheus-alerting"),
        ("nearest neighbor embedding similarity search store", "vector-databases-101"),
        ("switch traffic between two identical environments", "blue-green-deploys"),
        ("least privilege permissions for a role", "iam-least-privilege"),
    ],
)
def test_topical_queries_match_expected_doc(
    index: SearchIndex, query: str, expected_doc: str
) -> None:
    results = index.query(query, k=1)
    assert results[0].doc_id == expected_doc


def test_k_is_clamped_to_corpus_size(index: SearchIndex) -> None:
    results = index.query("deployment", k=1000)
    assert len(results) == len(index.documents)


def test_blank_query_returns_empty(index: SearchIndex) -> None:
    assert index.query("   ") == []
