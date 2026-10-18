
import { useState } from "react";
import "./App.css";
import { uploadPdf, searchDocuments } from "./api";
import type { SearchResult, UploadResponse } from "./api";

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [documentInfo, setDocumentInfo] =
    useState<UploadResponse | null>(null);
  const [question, setQuestion] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  function handleFileChange(selectedFile?: File) {
    setFile(selectedFile ?? null);
    setDocumentInfo(null);
    setResults([]);
    setMessage("");
  }

  async function handleUpload() {
    if (!file) {
      setMessage("Please choose a PDF document first.");
      return;
    }

    setLoading(true);
    setMessage("");
    setResults([]);

    try {
      const data = await uploadPdf(file);
      setDocumentInfo(data);

      setMessage(
        `Successfully indexed ${data.filename}: ${data.chunks_indexed} chunks.`
      );
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "PDF upload failed."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!question.trim()) {
      setMessage("Please enter a question.");
      return;
    }

    setLoading(true);
    setMessage("");
    setResults([]);

    try {
      const data = await searchDocuments(question);
      setResults(data);

      if (data.length === 0) {
        setMessage("No indexed passages found. Upload a PDF first.");
      } else {
        setMessage(`Found ${data.length} relevant passages.`);
      }
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Document search failed."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">A</div>
          <div>
            <strong>AskDoc AI</strong>
            <span>Document intelligence</span>
          </div>
        </div>

        <p className="nav-label">WORKSPACE</p>
        <button className="nav-item active" type="button">
          <span>▤</span> Document Assistant
        </button>
        <button className="nav-item" type="button">
          <span>◷</span> Recent activity
        </button>

        <div className="sidebar-bottom">
          <div className="status-dot" />
          <div>
            <strong>Local environment</strong>
            <span>Development mode</span>
          </div>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <span>Workspace / Document Assistant</span>
          <span className="environment-badge">LOCAL DEV</span>
        </header>

        <div className="content-container">
          <section className="hero">
            <span className="eyebrow">YOUR AI RESEARCH WORKSPACE</span>
            <h1>Chat with your documents.</h1>
            <p>
              Upload a PDF, explore its contents, and find the information
              that matters — without searching every page manually.
            </p>
          </section>

          <div className="dashboard-grid">
            <section className="panel upload-panel">
              <div className="panel-heading">
                <div>
                  <span className="step-label">STEP 01</span>
                  <h2>Upload a document</h2>
                </div>
                <span className="heading-icon">↑</span>
              </div>

              <label className="drop-zone">
                <input
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={(event) =>
                    handleFileChange(event.target.files?.[0])
                  }
                />
                <span className="file-icon">PDF</span>
                <strong>
                  {file ? file.name : "Choose a PDF to get started"}
                </strong>
                <span>
                  {file
                    ? `${(file.size / 1024 / 1024).toFixed(2)} MB`
                    : "Select a file from your computer"}
                </span>
                <span className="browse-button">Browse files</span>
              </label>

              <p className="helper-text">PDF format · Maximum 10 MB</p>

              <button
                className="primary-button"
                type="button"
                disabled={loading}
                onClick={handleUpload}
              >
                Index document <span>→</span>
              </button>

              {documentInfo && (
                <div className="document-card">
                  <span className="file-icon small">PDF</span>
                  <div>
                    <strong>{documentInfo.filename}</strong>
                    <span>
                      {documentInfo.pages_processed} pages ·{" "}
                      {documentInfo.chunks_indexed} chunks indexed
                    </span>
                  </div>
                </div>
              )}
            </section>

            <section className="panel search-panel">
              <div className="panel-heading">
                <div>
                  <span className="step-label">STEP 02</span>
                  <h2>Ask a question</h2>
                </div>
                <span className="heading-icon">⌕</span>
              </div>

              <form onSubmit={handleSearch}>
                <label htmlFor="question">What would you like to know?</label>
                <textarea
                  id="question"
                  rows={5}
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="e.g. What are the main findings in this document?"
                />
                <div className="search-hint">
                  <span>✳</span>
                  Ask a question about the uploaded document.
                </div>
                <button className="primary-button" type="submit">
                  Find relevant passages <span>→</span>
                </button>
              </form>
            </section>
          </div>

          {message && (
            <div className="notice" role="status">
              {message}
            </div>
          )}

          <section className="results-section">
            <div className="results-heading">
              <div>
                <span className="step-label">STEP 03</span>
                <h2>Research results</h2>
              </div>
              <span className="result-count">
                {results.length} passages
              </span>
            </div>

            {results.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">⌕</div>
                <h3>Your answers will appear here</h3>
                <p>
                  Upload a document and ask a question to discover relevant
                  passages with page references.
                </p>
              </div>
            ) : (
              <div className="results-list">
                {results.map((result, index) => (
                  <article
                    className="result-card"
                    key={`${result.filename}-${result.page}-${index}`}
                  >
                    <div className="result-card-heading">
                      <strong>{result.filename}</strong>
                      <span>Page {result.page}</span>
                    </div>

                    <p>{result.text}</p>

                    <small>
                      Similarity score: {result.score.toFixed(3)}
                    </small>
                  </article>
                ))}
              </div>
            )}
          </section>

          <footer>
            <span>AskDoc AI · AI + DevOps Portfolio Project</span>
            <span>Built with React, FastAPI and AWS</span>
          </footer>
        </div>
      </section>
    </main>
  );
}

export default App;
