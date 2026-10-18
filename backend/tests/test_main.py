
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.document_service import chunk_text

import fitz
from app.services.document_service import extract_pdf_pages


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
    with pytest.raises(ValueError, match="overlap"):
        chunk_text("example", chunk_size=5, overlap=5)


def test_chunk_text_rejects_nonpositive_chunk_size():
    with pytest.raises(ValueError, match="chunk_size"):
        chunk_text("example", chunk_size=0, overlap=0)


def test_chunk_text_rejects_negative_overlap():
    with pytest.raises(ValueError, match="overlap"):
        chunk_text("example", chunk_size=5, overlap=-1)


def test_chunk_text_normalizes_whitespace():
    chunks = chunk_text("  hello \n world   ", chunk_size=50, overlap=5)

    assert chunks == ["hello world"]


def test_chunk_text_empty_input():
    assert chunk_text("") == []
    assert chunk_text("   ") == []

def test_extract_pdf_pages():
    pdf = fitz.open()

    page1 = pdf.new_page()
    page1.insert_text((72, 72), "AskDoc AI first page")

    page2 = pdf.new_page()
    page2.insert_text((72, 72), "AskDoc AI second page")

    pdf_bytes = pdf.tobytes()
    pdf.close()

    pages = extract_pdf_pages(pdf_bytes)

    assert len(pages) == 2
    assert pages[0]["page"] == 1
    assert "AskDoc AI first page" in pages[0]["text"]
    assert pages[1]["page"] == 2
    assert "AskDoc AI second page" in pages[1]["text"]


def test_extract_pdf_pages_skips_empty_pages():
    pdf = fitz.open()
    pdf.new_page()
    page = pdf.new_page()
    page.insert_text((72, 72), "Page with text")

    pdf_bytes = pdf.tobytes()
    pdf.close()

    pages = extract_pdf_pages(pdf_bytes)

    assert len(pages) == 1
    assert pages[0]["page"] == 2
    assert pages[0]["text"] == "Page with text"


def test_search_returns_matching_chunks(monkeypatch):
    class FakeRAGService:
        def search(self, question: str, top_k: int = 3):
            assert question == "What is AskDoc AI?"
            assert top_k == 2

            return [
                {
                    "text": "AskDoc AI searches uploaded documents.",
                    "score": 0.92,
                    "filename": "guide.pdf",
                    "page": 1,
                }
            ]

    with TestClient(app) as client:
        monkeypatch.setattr(app.state, "rag", FakeRAGService(), raising=False)

        response = client.post(
            "/search",
            json={"question": "What is AskDoc AI?", "top_k": 2},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["text"] == "AskDoc AI searches uploaded documents."
    assert data["results"][0]["filename"] == "guide.pdf"


def test_search_rejects_empty_question():
    with TestClient(app) as client:
        response = client.post(
            "/search",
            json={"question": "", "top_k": 3},
        )

    assert response.status_code == 422


def test_search_rejects_top_k_out_of_range():
    with TestClient(app) as client:
        response = client.post(
            "/search",
            json={"question": "What is in this document?", "top_k": 11},
        )

    assert response.status_code == 422
