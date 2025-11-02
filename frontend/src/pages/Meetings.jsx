import React, { useState, useEffect } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import "./Meetings.css";
import api from "../services/api";

function Meetings() {
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [date, setDate] = useState(new Date());
  const [time, setTime] = useState("00:00");
  const [duration, setDuration] = useState("");
  const [participants, setParticipants] = useState("");
  const [summary, setSummary] = useState("");
  const [meetings, setMeetings] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // ✅ Fetch all meetings
  const fetchMeetings = async () => {
    try {
      const res = await api.get("/api/meetings");
      const data = res.data;

      if (Array.isArray(data)) {
        setMeetings(data);
      } else if (data && Array.isArray(data.meetings)) {
        setMeetings(data.meetings);
      } else {
        console.warn("Unexpected meetings response:", data);
        setMeetings([]);
      }
    } catch (err) {
      console.error("Error fetching meetings:", err);
      setError("Failed to load meetings.");
      setMeetings([]);
    }
  };

  useEffect(() => {
    fetchMeetings();
  }, []);

  // ✅ Create a new meeting
  const createMeeting = async (e) => {
    e.preventDefault();
    try {
      setError("");
      setLoading(true);

      const meetingDateTime = new Date(
        `${date.toISOString().split("T")[0]}T${time}`
      ).toISOString();

      await api.post("/api/meetings", {
        title,
        datetime: meetingDateTime,
        duration: parseInt(duration),
        participants: parseInt(participants),
        summary,
      });

      // Reset form
      setTitle("");
      setDate(new Date());
      setTime("00:00");
      setDuration("");
      setParticipants("");
      setSummary("");
      setShowForm(false);

      fetchMeetings();
    } catch (err) {
      console.error("createMeeting:", err);
      setError("Error creating meeting. Please check backend connection.");
    } finally {
      setLoading(false);
    }
  };

  // ✅ Mark meeting as done
  const markAsDone = async (id) => {
    try {
      await api.put(`/api/meetings/${id}/done`);
      fetchMeetings();
    } catch (err) {
      console.error("Error marking done:", err);
      setError("Failed to update meeting status.");
    }
  };

  // ✅ Delete meeting
  const deleteMeeting = async (id) => {
    const confirmDelete = window.confirm("Are you sure you want to delete this meeting?");
    if (!confirmDelete) return;

    try {
      await api.delete(`/api/meetings/${id}`);
      setMeetings(meetings.filter((m) => m._id !== id && m.id !== id));
    } catch (err) {
      console.error("Error deleting meeting:", err);
      alert("Failed to delete meeting.");
    }
  };

  return (
    <div className="meetings-container">
      <h2>Schedule & Manage Meetings</h2>

      {!showForm && (
        <button className="create-btn" onClick={() => setShowForm(true)}>
          Add New Meeting
        </button>
      )}

      {showForm && (
        <form className="meeting-form" onSubmit={createMeeting}>
          <button
            type="button"
            className="close-btn"
            onClick={() => setShowForm(false)}
          >
            Close
          </button>

          <input
            type="text"
            placeholder="Meeting Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />

          <label>Date</label>
          <DatePicker
            selected={date}
            onChange={(d) => setDate(d)}
            dateFormat="yyyy-MM-dd"
            className="date-picker"
            required
          />

          <label>Time</label>
          <input
            type="time"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            required
          />

          <input
            type="number"
            placeholder="Duration (minutes)"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            required
          />

          <input
            type="number"
            placeholder="Participants"
            value={participants}
            onChange={(e) => setParticipants(e.target.value)}
            required
          />

          <textarea
            placeholder="Summary"
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
          />

          {error && <p className="error">{error}</p>}

          <div className="btn-row">
            <button type="submit" className="create-btn" disabled={loading}>
              {loading ? "Creating..." : "Create"}
            </button>
            <button
              type="button"
              className="cancel-btn"
              onClick={() => setShowForm(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="meeting-list">
        {meetings.length === 0 ? (
          <p>No meetings yet. Create one using Add new meeting.</p>
        ) : (
          meetings.map((m) => (
            <div key={m._id || m.id} className="meeting-card">
              <div className="meeting-info">
                <h3>{m.title}</h3>
                <p>
                  <b>Date:</b> {new Date(m.datetime).toLocaleString()}
                </p>
                <p>
                  <b>Duration:</b> {m.duration} mins |{" "}
                  <b>Participants:</b> {m.participants}
                </p>
                <p>
                  <b>Status:</b>{" "}
                  {m.is_done ? (
                    <span className="done">Done</span>
                  ) : (
                    <button
                      onClick={() => markAsDone(m._id || m.id)}
                      className="done-btn"
                    >
                      Mark as Done
                    </button>
                  )}
                </p>
              </div>
              <button
                className="delete-btn"
                onClick={() => deleteMeeting(m._id || m.id)}
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Meetings;
