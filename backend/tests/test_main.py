
from fastapi.testclient import TestClient

from app.main import app
from app.services.document_service import chunk_text


def test_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "running"


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


def test_chunk_text_preserves_content():
    chunks = chunk_text("abcdefghij", chunk_size=6, overlap=2)

    assert chunks == ["abcdef", "efghij"]


def test_chunk_text_rejects_invalid_overlap():
    try:
        chunk_text("example", chunk_size=5, overlap=5)
        assert False, "Expected ValueError"
    except ValueError:
        pass
