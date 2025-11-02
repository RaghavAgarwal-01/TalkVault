import React, { useEffect, useState } from "react";
import api from "../services/api";
import "./History.css";
import { useAuth } from "../context/AuthContext";

function History() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      try {
        const params = {};
        if (user?.username) params.username = user.username;
        const res = await api.get("/api/summarizer/history", { params });
        setItems(res.data.items || []);
      } catch (err) {
        console.error("Failed to fetch history", err);
        setError("Failed to load history. Check console.");
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [user]);

  const openItem = async (id) => {
    try {
      const res = await api.get(`/api/summarizer/history/${id}`);
      setSelected(res.data);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      console.error("Failed to fetch item", err);
    }
  };

  const downloadText = (text, filename) => {
    const blob = new Blob([text || ""], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="history-container">
      <h2>Summary History</h2>
      {loading && <div>Loading...</div>}
      {error && <div style={{ color: "red" }}>{error}</div>}

      <div className="history-layout">
        <div className="history-list">
          {items.length === 0 && !loading && <div>No history found.</div>}
          <ul className="history-ul">
            {items.map((it) => (
              <li
                key={it.id}
                className="history-item"
                onClick={() => openItem(it.id)}
              >
                <div className="history-header">
                  {it.username || "anonymous"} —{" "}
                  {new Date(it.created_at).toLocaleString()}
                </div>
                <div className="history-preview">
                  {it.summary_text?.slice(0, 200)}
                  {it.summary_text?.length > 200 ? "…" : ""}
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="history-detail">
          {selected ? (
            <div className="history-summary">
              <div className="history-summary-header">
                <div>
                  <strong>{selected.username}</strong>
                  <div className="history-date">
                    {new Date(selected.created_at).toLocaleString()}
                  </div>
                </div>
                <button
                  className="download-btn"
                  onClick={() =>
                    downloadText(selected.summary_text, `summary-${selected.id}.txt`)
                  }
                >
                  Download
                </button>
              </div>

              <h4>Summary</h4>
              <pre className="summary-text">{selected.summary_text}</pre>

              <h4>Original Transcript</h4>
              <pre className="original-text">{selected.original_text}</pre>
            </div>
          ) : (
            <div className="placeholder-text">
              Select a summary on the left to view full details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default History;
