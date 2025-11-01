// frontend/src/services/api.js
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 600000, // 10 minutes
  headers: { "Content-Type": "application/json" },
});

// token attach etc...
export default api;
