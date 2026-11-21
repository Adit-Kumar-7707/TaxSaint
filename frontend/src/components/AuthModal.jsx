// TaxSaint Authentication Modal (Login / Sign Up)
import React, { useState } from "react";
import { loginUser, createUser } from "../services/api";

function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    userType: "salaried",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isLogin) {
        // --- Login Flow ---
        const res = await loginUser({
          email: formData.email.trim(),
          password: formData.password,
        });
        if (typeof onAuthSuccess === "function") {
          onAuthSuccess(res.user);
        }
      } else {
        // --- Registration Flow ---
        if (formData.password.length < 6) {
          throw new Error("Password must be at least 6 characters long.");
        }
        const res = await createUser({
          name: formData.name.trim(),
          email: formData.email.trim(),
          phone: formData.phone.trim() || null,
          userType: formData.userType,
          password: formData.password,
        });
        if (typeof onAuthSuccess === "function") {
          onAuthSuccess(res);
        }
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(10, 15, 29, 0.75)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        padding: "16px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          backgroundColor: "#161d31",
          border: "1px solid #28334e",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "460px",
          padding: "32px",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.6)",
          color: "#ffffff",
          position: "relative",
        }}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            background: "none",
            border: "none",
            color: "#94a3b8",
            fontSize: "20px",
            cursor: "pointer",
            padding: "4px 8px",
          }}
          aria-label="Close modal"
        >
          ✕
        </button>

        {/* Header Tabs */}
        <div style={{ textAlign: "center", marginBottom: "24px" }}>
          <h2 style={{ margin: "0 0 8px 0", fontSize: "24px", fontWeight: "700" }}>
            {isLogin ? "Welcome Back to TaxSaint" : "Create TaxSaint Account"}
          </h2>
          <p style={{ margin: 0, color: "#94a3b8", fontSize: "14px" }}>
            {isLogin
              ? "Sign in to securely access your tax calculations and filing."
              : "Register to manage personal or business financial tax records."}
          </p>
        </div>

        <div
          style={{
            display: "flex",
            backgroundColor: "#0d1322",
            borderRadius: "10px",
            padding: "4px",
            marginBottom: "24px",
          }}
        >
          <button
            type="button"
            onClick={() => {
              setIsLogin(true);
              setError(null);
            }}
            style={{
              flex: 1,
              padding: "8px 16px",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              fontWeight: "600",
              fontSize: "14px",
              backgroundColor: isLogin ? "#3b82f6" : "transparent",
              color: isLogin ? "#ffffff" : "#94a3b8",
              transition: "all 0.2s ease",
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setIsLogin(false);
              setError(null);
            }}
            style={{
              flex: 1,
              padding: "8px 16px",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              fontWeight: "600",
              fontSize: "14px",
              backgroundColor: !isLogin ? "#3b82f6" : "transparent",
              color: !isLogin ? "#ffffff" : "#94a3b8",
              transition: "all 0.2s ease",
            }}
          >
            Register
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            style={{
              backgroundColor: "rgba(239, 68, 68, 0.15)",
              border: "1px solid #ef4444",
              color: "#fca5a5",
              borderRadius: "8px",
              padding: "10px 14px",
              marginBottom: "16px",
              fontSize: "13px",
            }}
          >
            {error}
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {!isLogin && (
            <div>
              <label style={{ display: "block", fontSize: "13px", marginBottom: "6px", color: "#cbd5e1" }}>
                Full Name *
              </label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                placeholder="e.g. Rahul Sharma"
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  borderRadius: "8px",
                  border: "1px solid #334155",
                  backgroundColor: "#0d1322",
                  color: "#ffffff",
                  fontSize: "14px",
                  boxSizing: "border-box",
                }}
              />
            </div>
          )}

          <div>
            <label style={{ display: "block", fontSize: "13px", marginBottom: "6px", color: "#cbd5e1" }}>
              Email Address *
            </label>
            <input
              type="email"
              name="email"
              required
              value={formData.email}
              onChange={handleChange}
              placeholder="you@example.com"
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: "8px",
                border: "1px solid #334155",
                backgroundColor: "#0d1322",
                color: "#ffffff",
                fontSize: "14px",
                boxSizing: "border-box",
              }}
            />
          </div>

          {!isLogin && (
            <div style={{ display: "flex", gap: "12px" }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "6px", color: "#cbd5e1" }}>
                  Phone Number
                </label>
                <input
                  type="text"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="9876543210"
                  style={{
                    width: "100%",
                    padding: "10px 14px",
                    borderRadius: "8px",
                    border: "1px solid #334155",
                    backgroundColor: "#0d1322",
                    color: "#ffffff",
                    fontSize: "14px",
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "6px", color: "#cbd5e1" }}>
                  Worker Profile *
                </label>
                <select
                  name="userType"
                  value={formData.userType}
                  onChange={handleChange}
                  style={{
                    width: "100%",
                    padding: "10px 14px",
                    borderRadius: "8px",
                    border: "1px solid #334155",
                    backgroundColor: "#0d1322",
                    color: "#ffffff",
                    fontSize: "14px",
                    boxSizing: "border-box",
                  }}
                >
                  <option value="salaried">Salaried Employee</option>
                  <option value="business">Business Owner</option>
                </select>
              </div>
            </div>
          )}

          <div>
            <label style={{ display: "block", fontSize: "13px", marginBottom: "6px", color: "#cbd5e1" }}>
              Password *
            </label>
            <input
              type="password"
              name="password"
              required
              value={formData.password}
              onChange={handleChange}
              placeholder={isLogin ? "Enter password" : "At least 6 characters"}
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: "8px",
                border: "1px solid #334155",
                backgroundColor: "#0d1322",
                color: "#ffffff",
                fontSize: "14px",
                boxSizing: "border-box",
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: "8px",
              padding: "12px",
              borderRadius: "8px",
              border: "none",
              backgroundColor: "#2563eb",
              color: "#ffffff",
              fontWeight: "600",
              fontSize: "15px",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.7 : 1,
              transition: "background-color 0.2s",
            }}
          >
            {loading ? "Processing..." : isLogin ? "Sign In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default AuthModal;
