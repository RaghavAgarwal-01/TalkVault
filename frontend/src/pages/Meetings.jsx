// frontend/src/pages/Meetings.jsx

import React, { useState, useEffect } from 'react'
import api from '../services/api'

const Meetings = () => {
  const [meetings, setMeetings] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    scheduled_time: '',
    duration_minutes: 60,
    tags: ''
  })

  useEffect(() => {
    fetchMeetings()
  }, [])

  const fetchMeetings = async () => {
    try {
      const response = await api.get('/meetings')
      setMeetings(response.data)
    } catch (error) {
      console.error('Failed to fetch meetings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const meetingData = {
        ...formData,
        tags: formData.tags.split(',').map(tag => tag.trim()).filter(Boolean)
      }
      await api.post('/meetings', meetingData)
      setShowCreateForm(false)
      setFormData({
        title: '',
        description: '',
        scheduled_time: '',
        duration_minutes: 60,
        tags: ''
      })
      fetchMeetings()
    } catch (error) {
      console.error('Failed to create meeting:', error)
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  if (loading) {
    return <div className="loading">Loading meetings...</div>
  }

  return (
    <div className="meetings-page">
      <div className="page-header">
        <h1>Meetings</h1>
        <button 
          onClick={() => setShowCreateForm(true)}
          className="primary-button"
        >
          Create Meeting
        </button>
      </div>

      {showCreateForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Create New Meeting</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="title">Title</label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="scheduled_time">Scheduled Time</label>
                <input
                  type="datetime-local"
                  id="scheduled_time"
                  name="scheduled_time"
                  value={formData.scheduled_time}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="duration_minutes">Duration (minutes)</label>
                <input
                  type="number"
                  id="duration_minutes"
                  name="duration_minutes"
                  value={formData.duration_minutes}
                  onChange={handleChange}
                  min="15"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="tags">Tags (comma-separated)</label>
                <input
                  type="text"
                  id="tags"
                  name="tags"
                  value={formData.tags}
                  onChange={handleChange}
                  placeholder="important, team, planning"
                />
              </div>
              
              <div className="modal-actions">
                <button type="submit" className="primary-button">
                  Create Meeting
                </button>
                <button 
                  type="button" 
                  onClick={() => setShowCreateForm(false)}
                  className="secondary-button"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="meetings-grid">
        {meetings.length > 0 ? (
          meetings.map((meeting) => (
            <div key={meeting.id} className="meeting-card">
              <h3>{meeting.title}</h3>
              <p>{meeting.description}</p>
              <div className="meeting-info">
                <span>Date: {new Date(meeting.scheduled_time).toLocaleDateString()}</span>
                <span>Time: {new Date(meeting.scheduled_time).toLocaleTimeString()}</span>
                <span>Duration: {meeting.duration_minutes} min</span>
              </div>
              <div className="meeting-status">
                <span className={`status ${meeting.status}`}>
                  {meeting.status}
                </span>
              </div>
              {meeting.tags.length > 0 && (
                <div className="meeting-tags">
                  {meeting.tags.map((tag, index) => (
                    <span key={index} className="tag">{tag}</span>
                  ))}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="no-meetings">
            <p>No meetings yet. Create your first meeting!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Meetings
