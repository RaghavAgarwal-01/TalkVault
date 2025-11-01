import React, { createContext, useContext, useState, useEffect } from "react";
import api from "../services/api";

const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (token) {
      // ✅ Ensure Authorization header is set globally for axios
      api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      fetchUser(); // get user info from backend
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await api.get("/api/auth/me");
      setUser(response.data);
    } catch (error) {
      console.error("Failed to fetch user:", error.response?.data || error.message);

      // ✅ If token is invalid or expired, clear it completely
      localStorage.removeItem("token");
      delete api.defaults.headers.common["Authorization"];
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await api.post("/api/auth/login", { email, password });

      // ✅ Adjust to match your FastAPI response keys
      const { access_token, user: userData } = response.data;

      // Save token & setup axios header
      localStorage.setItem("token", access_token);
      api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;

      setUser(userData);
      return { success: true };
    } catch (error) {
      console.error("Login failed:", error.response?.data || error.message);
      return { success: false, error: error.response?.data?.detail || "Login failed" };
    }
  };

  const register = async (userData) => {
    try {
      await api.post("/api/auth/register", userData);
      return { success: true };
    } catch (error) {
      console.error("Registration failed:", error.response?.data || error.message);
      return { success: false, error: error.response?.data?.detail || "Registration failed" };
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    delete api.defaults.headers.common["Authorization"];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
