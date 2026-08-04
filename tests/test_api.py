"""API-level tests for the FastAPI app.

These exercise the HTTP contract in-process via Starlette's ``TestClient`` (no
network, no running server) so the response shape stays stable for the web UI.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import __version__
from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """A test client sharing one warmed index across the module."""
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_document_count(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
    assert body["documents"] >= 6


def test_search_exposes_matched_terms(client: TestClient) -> None:
    response = client.get("/search", params={"q": "how do I keep a pod healthy", "k": 3})
    assert response.status_code == 200
    body = response.json()
    # Stop words are stripped; the meaningful terms remain for UI highlighting.
    assert body["terms"] == ["pod", "healthy"]
    assert body["count"] == len(body["results"]) == 3
    assert body["results"][0]["doc_id"] == "kubernetes-probes"


def test_search_result_snippet_reflects_the_query(client: TestClient) -> None:
    response = client.get("/search", params={"q": "lock terraform state file", "k": 1})
    top = response.json()["results"][0]
    assert "terraform" in top["snippet"].lower()


def test_blank_query_returns_no_results(client: TestClient) -> None:
    body = client.get("/search", params={"q": "   "}).json()
    assert body["count"] == 0
    assert body["results"] == []
    assert body["terms"] == []


def test_k_out_of_range_is_rejected(client: TestClient) -> None:
    assert client.get("/search", params={"q": "deploy", "k": 0}).status_code == 422
    assert client.get("/search", params={"q": "deploy", "k": 999}).status_code == 422
