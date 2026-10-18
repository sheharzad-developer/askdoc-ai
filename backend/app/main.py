from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.document_service import chunk_text, extract_pdf_pages
from app.services.rag_service import RAGService

from fastapi.middleware.cors import CORSMiddleware

MAX_PDF_BYTES = 10 * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rag = RAGService()
    yield


app = FastAPI(
    title="AI RAG Document Assistant",
    description="Upload PDF documents and retrieve relevant passages",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class SearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)


@app.get("/")
def root():
    return {
        "message": "AI RAG Document Assistant API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=415,
            detail="Please upload a PDF file",
        )

    content = await file.read(MAX_PDF_BYTES + 1)

    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(
            status_code=413,
            detail="PDF must be 10 MB or smaller",
        )

    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    try:
        pages = extract_pdf_pages(content)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not read PDF document",
        ) from exc

    chunks = []
    metadata = []

    for page in pages:
        for chunk in chunk_text(page["text"]):
            chunks.append(chunk)
            metadata.append({
                "filename": file.filename or "document.pdf",
                "page": page["page"],
            })

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in PDF",
        )

    try:
        count = app.state.rag.add_documents(chunks, metadata)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not process document embeddings",
        ) from exc

    return {
        "filename": file.filename or "document.pdf",
        "pages_processed": len(pages),
        "chunks_indexed": count,
    }


@app.post("/search")
def search_documents(request: SearchRequest):
    try:
        results = app.state.rag.search(
            request.question,
            request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "question": request.question,
        "results": results,
    }
