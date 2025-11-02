import React, { useState } from "react";
import "./Documents.css";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

function Documents() {
  const { user } = useAuth();
  const [file, setFile] = useState(null);
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [inProgress, setInProgress] = useState(false);

  const handleGenerate = async () => {
    if (!file && !text.trim()) {
      setError("Please provide text or upload an audio file");
      return;
    }

    setError("");
    setSummary("");
    setLoading(true);
    setInProgress(true);

    try {
      const formData = new FormData();
      if (file) formData.append("audio_file", file);
      else formData.append("transcript", text);
      if (user?.username) formData.append("username", user.username);

      const res = await api.post("/api/summarizer/generate", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const data = res.data;
      setSummary(data?.summary || data?.data?.summary || "");
      if (!data?.summary && !data?.data?.summary)
        setError("No summary returned from server.");
    } catch (err) {
      console.error(err);
      setError("Failed to generate summary. Check console for details.");
    } finally {
      setLoading(false);
      setInProgress(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setText("");
    setSummary("");
    setError("");
  };

  const handleDownload = () => {
    if (!summary) return;
    const blob = new Blob([summary], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `summary_${new Date().toISOString().replace(/[:.]/g, "-")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="documents-container">
      <h2>Meeting Summarizer</h2>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste or upload meeting audio..."
        rows={6}
      />

      <label className="file-upload">
        <input
          type="file"
          accept="audio/*"
          onChange={(e) => setFile(e.target.files[0])}
        />
        {file ? file.name : "Choose File"}
      </label>

      <div className="button-row">
        <button onClick={handleGenerate} disabled={loading}>
          {loading ? "Generating..." : "Generate Summary"}
        </button>
        <button onClick={handleReset}>Reset</button>
        {summary && (
          <button onClick={handleDownload}>Download Summary</button>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      <div
        className={`summary-box ${!summary ? "empty" : ""}`}
        style={{
          transition: "all 0.3s ease",
          opacity: loading ? 0.6 : 1,
        }}
      >
        {summary ? (
          <pre className="summary-text">{summary}</pre>
        ) : (
          <div className="placeholder">No summary yet.</div>
        )}
      </div>

      {inProgress && (
        <div className="progress-bar">
          <div className="bar"></div>
        </div>
      )}
    </div>
  );
}

export default Documents;
