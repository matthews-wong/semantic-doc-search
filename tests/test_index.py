"""Tests for corpus loading, index building, and querying."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.embedder import TfidfEmbedder
from app.index import (
    Document,
    SearchIndex,
    _make_snippet,
    extract_query_terms,
    load_corpus,
)

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


def test_min_score_drops_weak_matches(index: SearchIndex) -> None:
    query = "how do I keep a pod healthy and restart it"
    unfiltered = index.query(query, k=5)
    assert len(unfiltered) >= 2, "need multiple hits to exercise the threshold"

    # A threshold just above the weakest hit drops it while keeping the top hit.
    weakest = unfiltered[-1].score
    threshold = weakest + 1e-6
    filtered = index.query(query, k=5, min_score=threshold)

    assert filtered, "the top match should survive the threshold"
    assert all(r.score >= threshold for r in filtered)
    assert len(filtered) < len(unfiltered)


def test_min_score_above_one_returns_nothing(index: SearchIndex) -> None:
    # Cosine similarity is bounded by 1.0, so nothing clears a threshold above it.
    assert index.query("deployment", k=5, min_score=1.01) == []


def test_min_score_zero_matches_default_behavior(index: SearchIndex) -> None:
    query = "deployment"
    assert index.query(query, k=5) == index.query(query, k=5, min_score=0.0)


def test_extract_query_terms_drops_stopwords_and_single_chars() -> None:
    terms = extract_query_terms("How do I lock the Terraform state in S3?")
    # Stop words ("how", "do", "the", "in") and the single char "i" are removed.
    assert "the" not in terms
    assert "in" not in terms
    assert "i" not in terms
    # Meaningful tokens survive, lowercased, in first-seen order.
    assert terms == ["lock", "terraform", "state", "s3"]


def test_extract_query_terms_deduplicates_preserving_order() -> None:
    assert extract_query_terms("cache cache miss cache") == ["cache", "miss"]


def test_snippet_short_text_returned_whole() -> None:
    assert _make_snippet("just a few words", query="words") == "just a few words"


def test_snippet_centers_on_matching_passage() -> None:
    text = "alpha " * 60 + "UNIQUEMARKER lives here " + "omega " * 60
    snippet = _make_snippet(text, query="uniquemarker", max_chars=80)
    assert "UNIQUEMARKER" in snippet
    # A hit deep in the doc is trimmed on both sides, not shown from the head.
    assert snippet.startswith("...")
    assert snippet.endswith("...")
    assert len(snippet) < len(text)


def test_snippet_falls_back_to_head_when_query_absent() -> None:
    text = "alpha " * 100
    snippet = _make_snippet(text, query="nomatchhere", max_chars=50)
    assert snippet.startswith("alpha")
    assert snippet.endswith("...")


def test_query_snippet_contains_a_matched_term(index: SearchIndex) -> None:
    query = "lock terraform state file"
    result = index.query(query, k=1)[0]
    terms = extract_query_terms(query)
    lowered = result.snippet.lower()
    assert any(term in lowered for term in terms)
