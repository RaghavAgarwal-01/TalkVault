import axios from 'axios'

// Keep API_BASE_URL pointed at /api for auth, documents, etc.
const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Keep these single-line, no newline inside template string
const generateSummary = (documentId) => api.post(`/documents/${documentId}/summarize`)
const getSummaries = (documentId) => api.get(`/documents/${documentId}/summaries`)

export default Object.assign(api, { generateSummary, getSummaries })
