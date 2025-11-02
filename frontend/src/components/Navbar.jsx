// frontend/src/components/Navbar.jsx

import React from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const Navbar = () => {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (path) => location.pathname === path

  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          TalkVault
        </Link>
        
        <div className="nav-links">
          <Link 
            to="/" 
            className={`nav-link ${isActive('/') ? 'active' : ''}`}
          >
            Dashboard
          </Link>
          <Link 
            to="/meetings" 
            className={`nav-link ${isActive('/meetings') ? 'active' : ''}`}
          >
            Meetings
          </Link>
          <Link 
            to="/documents" 
            className={`nav-link ${isActive('/documents') ? 'active' : ''}`}
          >
            Documents
          </Link>
          <Link 
              to="/history" 
              className={`nav-link ${isActive('/history') ? 'active' : ''}`}
              style={{ marginLeft: 8 }}
            >
              History
            </Link>
        </div>
        
        <div className="nav-user">
          <Link 
            to="/profile" 
            className={`nav-link ${isActive('/profile') ? 'active' : ''}`}
          >
            {user?.username || user?.email}
          </Link>
          <button onClick={handleLogout} className="nav-logout">
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
