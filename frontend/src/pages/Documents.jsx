import React, { useState, useEffect } from "react";
import axios from "axios";
import "./Documents.css";
import { useAuth } from "../context/AuthContext";

const API_URL = "http://127.0.0.1:8000/summarizer";

function Documents() {
  const { user } = useAuth();
  const username = user?.username || localStorage.getItem("username");

  const [file, setFile] = useState(null);
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(false);

  // --- Upload or summarize text ---
  const handleUpload = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    if (file) formData.append("file", file);
    if (text) formData.append("text", text);
    formData.append("username", username || "");

    try {
      setLoading(true);
      const resp = await fetch(`${API_URL}/generate`, {
        method: "POST",
        body: formData,
      });
      const data = await resp.json();

      if (!resp.ok) throw new Error(data.detail || JSON.stringify(data));
      setSummary(data.summary);
    } catch (err) {
      console.error("❌ Summarization failed:", err);
      alert("Summarization failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // --- Fetch previous summaries for the user ---
  useEffect(() => {
    if (!username) return;
    fetch(`${API_URL}/previous/${username}`)
      .then((r) => r.json())
      .then((data) => {
        // Handle both possible shapes
        if (Array.isArray(data)) {
          setSummaries(data);
        } else if (data && Array.isArray(data.summaries)) {
          setSummaries(data.summaries);
        } else {
          setSummaries([]);
        }
      })
      .catch((err) => {
        console.error("❌ Error fetching summaries:", err);
        setSummaries([]);
      });
  }, [username]);

  return (
    <div className="documents-container">
      <h1>Meeting Summarizer</h1>

      {/* Upload & Text Input Section */}
      <div className="upload-box">
        <textarea
          placeholder="Paste meeting text here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        ></textarea>

        <div className="file-upload">
          <label>Or upload audio/text file:</label>
          <input
            type="file"
            accept=".txt,.docx,.mp3,.wav"
            onChange={(e) => setFile(e.target.files[0])}
          />
        </div>

        <button onClick={handleUpload} disabled={loading}>
          {loading ? "Summarizing..." : "Generate Summary"}
        </button>
      </div>

      {/* Generated Summary */}
      {summary && (
        <div className="summary-box">
          <h2>Generated Summary</h2>
          <p>{summary}</p>
        </div>
      )}

      {/* Previous Summaries */}
      <div className="previous-summaries">
        <h2>Previous Summaries</h2>
        {Array.isArray(summaries) && summaries.length > 0 ? (
          summaries.map((s) => (
            <div key={s._id} className="summary-card">
              <p>{s.summary}</p>
              <small>
                {s.created_at
                  ? new Date(s.created_at).toLocaleString()
                  : "Unknown time"}
              </small>
            </div>
          ))
        ) : (
          <p>No previous summaries found.</p>
        )}
      </div>
    </div>
  );
}

export default Documents;
