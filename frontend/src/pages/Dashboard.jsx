// frontend/src/pages/Dashboard.jsx

import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'

const Dashboard = () => {
  const { user } = useAuth()
  const [stats, setStats] = useState({
    meetings: 0,
    documents: 0,
    recentMeetings: [],
    recentDocuments: []
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [meetingsRes, documentsRes] = await Promise.all([
        api.get('/meetings?limit=5'),
        api.get('/documents?limit=5')
      ])
      
      setStats({
        meetings: meetingsRes.data.length,
        documents: documentsRes.data.length,
        recentMeetings: meetingsRes.data,
        recentDocuments: documentsRes.data
      })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading dashboard...</div>
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Welcome back, {user?.full_name || user?.username}!</h1>
        <p>Here's what's happening with your meetings and documents.</p>
      </div>

      <div className="dashboard-stats">
        <div className="stat-card">
          <h3>Total Meetings</h3>
          <div className="stat-number">{stats.meetings}</div>
        </div>
        <div className="stat-card">
          <h3>Total Documents</h3>
          <div className="stat-number">{stats.documents}</div>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="dashboard-section">
          <h2>Recent Meetings</h2>
          {stats.recentMeetings.length > 0 ? (
            <div className="items-list">
              {stats.recentMeetings.map((meeting) => (
                <div key={meeting.id} className="item-card">
                  <h4>{meeting.title}</h4>
                  <p>{meeting.description}</p>
                  <span className="item-date">
                    {new Date(meeting.scheduled_time).toLocaleDateString()}
                  </span>
                  <span className={`status ${meeting.status}`}>
                    {meeting.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-items">No recent meetings</p>
          )}
        </div>

        <div className="dashboard-section">
          <h2>Recent Documents</h2>
          {stats.recentDocuments.length > 0 ? (
            <div className="items-list">
              {stats.recentDocuments.map((document) => (
                <div key={document.id} className="item-card">
                  <h4>{document.title || document.original_filename}</h4>
                  <p>{document.description}</p>
                  <span className="item-date">
                    {new Date(document.created_at).toLocaleDateString()}
                  </span>
                  <span className={`status ${document.processing_status}`}>
                    {document.processing_status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-items">No recent documents</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
