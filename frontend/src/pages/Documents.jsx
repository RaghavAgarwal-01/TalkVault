import React, { useState } from "react";
import "./Documents.css";
import { useAuth } from "../context/AuthContext";
import api from "../services/api"; // ✅ your configured Axios instance

function Documents() {
  const { user } = useAuth();
  const [file, setFile] = useState(null);
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!file && !text.trim()) {
      setError("Please provide text or upload an audio file");
      return;
    }

    setLoading(true);
    setError("");
    setSummary("");

    try {
      const formData = new FormData();

      if (file) {
        formData.append("audio_file", file);
      } else {
        formData.append("transcript", text);
      }

      const response = await api.post("/api/summarizer/generate", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      console.log("🧾 Full response:", response.data);

      const summaryText =
        response.data.summary || response.data.data?.summary || "";

      if (summaryText) {
        setSummary(summaryText);
      } else {
        console.warn("⚠️ No summary found in response:", response.data);
        setError("No summary returned from server.");
      }
    } catch (err) {
      console.error("Summary generation error:", err);
      setError("Failed to generate summary. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setText("");
    setSummary("");
    setError("");
  };

  return (
    <div className="documents">
      <h2>Meeting Summarizer</h2>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste or upload meeting audio..."
        style={{
          width: "100%",
          height: "150px",
          padding: "10px",
          borderRadius: "8px",
          border: "1px solid #ccc",
          backgroundColor: "#fff",
          color: "#000",
          fontSize: "16px",
          marginBottom: "10px",
        }}
      />

      <input
        type="file"
        accept="audio/*"
        onChange={(e) => setFile(e.target.files[0])}
        style={{ marginBottom: "10px" }}
      />

      <div style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
        <button
          onClick={handleGenerate}
          disabled={loading}
          style={{
            backgroundColor: "#00bcd4",
            color: "#fff",
            padding: "8px 16px",
            borderRadius: "6px",
            border: "none",
            cursor: "pointer",
          }}
        >
          {loading ? "Generating..." : "Generate Summary"}
        </button>
        <button
          onClick={handleReset}
          style={{
            backgroundColor: "#555",
            color: "#fff",
            padding: "8px 16px",
            borderRadius: "6px",
            border: "none",
            cursor: "pointer",
          }}
        >
          Reset
        </button>
      </div>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <div className="summary-box">
        <h3>Generated Summary:</h3>
        {loading ? (
          <p>Generating summary...</p>
        ) : summary ? (
          <textarea
            readOnly
            value={summary}
            style={{
              width: "100%",
              height: "200px",
              padding: "10px",
              borderRadius: "8px",
              border: "1px solid #ccc",
              backgroundColor: "#fff",
              color: "#000",
              fontSize: "16px",
            }}
          />
        ) : (
          <p style={{ color: "#888" }}>Your summary will appear here...</p>
        )}
      </div>
    </div>
  );
}

export default Documents;
