// frontend/src/pages/Documents.jsx

import React, { useState, useEffect } from 'react'
import api from '../services/api'

const Documents = () => {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadForm, setUploadForm] = useState({
    title: '',
    description: '',
    tags: ''
  })

  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/documents')
      setDocuments(response.data)
    } catch (error) {
      console.error('Failed to fetch documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (e) => {
    setSelectedFile(e.target.files[0])
  }

  const handleUploadFormChange = (e) => {
    setUploadForm({
      ...uploadForm,
      [e.target.name]: e.target.value
    })
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!selectedFile) return

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      if (uploadForm.title) formData.append('title', uploadForm.title)
      if (uploadForm.description) formData.append('description', uploadForm.description)
      if (uploadForm.tags) formData.append('tags', uploadForm.tags)

      await api.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setSelectedFile(null)
      setUploadForm({ title: '', description: '', tags: '' })
      fetchDocuments()
    } catch (error) {
      console.error('Failed to upload document:', error)
    } finally {
      setUploading(false)
    }
  }

  const handleDownload = async (documentId, filename) => {
    try {
      const response = await api.get(`/documents/${documentId}/download`, {
        responseType: 'blob',
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to download document:', error)
    }
  }

  if (loading) {
    return <div className="loading">Loading documents...</div>
  }

  return (
    <div className="documents-page">
      <div className="page-header">
        <h1>Documents</h1>
      </div>

      <div className="upload-section">
        <h2>Upload Document</h2>
        <form onSubmit={handleUpload} className="upload-form">
          <div className="form-group">
            <label htmlFor="file">Choose File</label>
            <input
              type="file"
              id="file"
              onChange={handleFileSelect}
              accept=".pdf,.doc,.docx,.txt,.mp3,.wav,.mp4"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="title">Title (optional)</label>
            <input
              type="text"
              id="title"
              name="title"
              value={uploadForm.title}
              onChange={handleUploadFormChange}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="description">Description (optional)</label>
            <textarea
              id="description"
              name="description"
              value={uploadForm.description}
              onChange={handleUploadFormChange}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="tags">Tags (comma-separated)</label>
            <input
              type="text"
              id="tags"
              name="tags"
              value={uploadForm.tags}
              onChange={handleUploadFormChange}
              placeholder="important, meeting, notes"
            />
          </div>
          
          <button type="submit" disabled={uploading} className="primary-button">
            {uploading ? 'Uploading...' : 'Upload Document'}
          </button>
        </form>
      </div>

      <div className="documents-grid">
        {documents.length > 0 ? (
          documents.map((document) => (
            <div key={document.id} className="document-card">
              <h3>{document.title || document.original_filename}</h3>
              <p>{document.description}</p>
              <div className="document-info">
                <span>Type: {document.file_type}</span>
                <span>Size: {Math.round(document.file_size / 1024)} KB</span>
                <span>Uploaded: {new Date(document.created_at).toLocaleDateString()}</span>
              </div>
              <div className="document-status">
                <span className={`status ${document.processing_status}`}>
                  {document.processing_status}
                </span>
              </div>
              {document.tags.length > 0 && (
                <div className="document-tags">
                  {document.tags.map((tag, index) => (
                    <span key={index} className="tag">{tag}</span>
                  ))}
                </div>
              )}
              <div className="document-actions">
                <button
                  onClick={() => handleDownload(document.id, document.original_filename)}
                  className="secondary-button"
                >
                  Download
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="no-documents">
            <p>No documents yet. Upload your first document!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Documents
