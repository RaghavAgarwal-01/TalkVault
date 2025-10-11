// frontend/src/pages/Profile.jsx

import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'

const Profile = () => {
  const { user, logout } = useAuth()
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState({
    username: user?.username || '',
    full_name: user?.full_name || '',
    email: user?.email || ''
  })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      await api.put('/users/me', formData)
      setMessage('Profile updated successfully!')
      setEditing(false)
    } catch (error) {
      setMessage('Failed to update profile')
      console.error('Failed to update profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setFormData({
      username: user?.username || '',
      full_name: user?.full_name || '',
      email: user?.email || ''
    })
    setEditing(false)
    setMessage('')
  }

  return (
    <div className="profile-page">
      <div className="profile-header">
        <h1>Profile Settings</h1>
      </div>

      {message && (
        <div className={`message ${message.includes('success') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}

      <div className="profile-card">
        <div className="profile-info">
          <div className="profile-avatar">
            <div className="avatar-placeholder">
              {(user?.full_name || user?.username || user?.email)?.charAt(0)?.toUpperCase()}
            </div>
          </div>
          
          <div className="profile-details">
            {editing ? (
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="full_name">Full Name</label>
                  <input
                    type="text"
                    id="full_name"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="username">Username</label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                </div>
                
                <div className="form-actions">
                  <button type="submit" disabled={loading} className="primary-button">
                    {loading ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button type="button" onClick={handleCancel} className="secondary-button">
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="profile-display">
                <div className="profile-field">
                  <label>Full Name</label>
                  <span>{user?.full_name || 'Not provided'}</span>
                </div>
                
                <div className="profile-field">
                  <label>Username</label>
                  <span>{user?.username}</span>
                </div>
                
                <div className="profile-field">
                  <label>Email</label>
                  <span>{user?.email}</span>
                </div>
                
                <div className="profile-field">
                  <label>Account Status</label>
                  <span className={`status ${user?.is_active ? 'active' : 'inactive'}`}>
                    {user?.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                
                <div className="profile-field">
                  <label>Member Since</label>
                  <span>{new Date(user?.created_at).toLocaleDateString()}</span>
                </div>
                
                <button onClick={() => setEditing(true)} className="primary-button">
                  Edit Profile
                </button>
              </div>
            )}
          </div>
        </div>
        
        <div className="profile-actions">
          <button onClick={logout} className="danger-button">
            Sign Out
          </button>
        </div>
      </div>
    </div>
  )
}

export default Profile
