import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./Dashboard.css";

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_meetings: 0,
    total_summaries: 0,
    upcoming_meetings: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await api.get("/api/analytics");
        setStats(res.data || {});
      } catch (e) {
        console.error(e);
        setError(
          e?.response?.data?.detail || e.message || "Failed to load analytics"
        );
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user]);

  const goToSummaries = () => navigate("/history");
  const goToMeetings = () => navigate("/meetings");

  if (loading) return <div className="dashboard">Loading analytics...</div>;
  if (error) return <div className="dashboard error">Error: {error}</div>;

  return (
    <div className="dashboard">
      <h2>Analytics & Insights</h2>
      <div className="cards">
        <div
          className="card"
          onClick={goToMeetings}
          style={{ cursor: "pointer" }}
        >
          <h3>Total meetings</h3>
          <p className="big-number">{stats.total_meetings ?? 0}</p>
          <small>Click to view all meetings</small>
        </div>

        <div
          className="card"
          onClick={goToSummaries}
          style={{ cursor: "pointer" }}
        >
          <h3>Total summaries</h3>
          <p className="big-number">{stats.total_summaries ?? 0}</p>
          <small>Click to open history</small>
        </div>

        <div className="card">
          <h3>Upcoming meetings</h3>
          {stats.upcoming_meetings && stats.upcoming_meetings.length ? (
            <ul className="upcoming-list">
              {stats.upcoming_meetings.map((m) => (
                <li
                  key={m.id}
                  onClick={() => navigate(`/meetings?open=${m.id}`)}
                  style={{ cursor: "pointer" }}
                >
                  <strong>{m.title}</strong>
                  <div className="muted">
                    {m.datetime
                      ? new Date(m.datetime).toLocaleString()
                      : "No date"}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div>No upcoming meetings</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
