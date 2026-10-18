
const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface UploadResponse {
  filename: string;
  pages_processed: number;
  chunks_indexed: number;
}

export interface SearchResult {
  text: string;
  score: number;
  filename: string;
  page: number;
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "PDF upload failed");
  }

  return response.json();
}

export async function searchDocuments(
  question: string,
): Promise<SearchResult[]> {
  const response = await fetch(`${API_URL}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      top_k: 3,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Document search failed");
  }

  const data = await response.json();
  return data.results;
}
