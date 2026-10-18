
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class RAGService:
    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.index = None
        self.chunks = []
        self.metadata = []

    def add_documents(
        self,
        chunks: list[str],
        metadata: list[dict],
    ) -> int:
        if len(chunks) != len(metadata):
            raise ValueError("Each chunk must have matching metadata")

        if not chunks:
            return 0

        embeddings = self.model.encode(
            chunks,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        embeddings = np.asarray(embeddings, dtype=np.float32)

        if self.index is None:
            self.index = faiss.IndexFlatIP(embeddings.shape[1])

        self.index.add(embeddings)
        self.chunks.extend(chunks)
        self.metadata.extend(metadata)

        return len(chunks)

    def search(self, question: str, top_k: int = 3) -> list[dict]:
        if not question.strip():
            raise ValueError("Question cannot be empty")

        if top_k <= 0:
            raise ValueError("top_k must be positive")

        if self.index is None or not self.chunks:
            return []

        query_embedding = self.model.encode(
            [question],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        query_embedding = np.asarray(
            query_embedding,
            dtype=np.float32,
        )

        count = min(top_k, len(self.chunks))
        scores, indices = self.index.search(query_embedding, count)

        results = []
        seen_chunks = set()

        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue

            chunk_index = int(index)
            text = self.chunks[chunk_index]
            normalized_text = " ".join(text.lower().split())

            # Skip identical passages returned more than once.
            if normalized_text in seen_chunks:
                continue

            seen_chunks.add(normalized_text)

            results.append({
                "text": text,
                "score": float(score),
                **self.metadata[chunk_index],
            })

        return results
