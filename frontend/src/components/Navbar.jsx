// TaxSaint top navigation bar
// Handles branding, fiscal year badge, user session state, and persona switching.
import React from "react";

function Navbar({
  title = "TaxSaint",
  user = null,
  onProfileClick,
  onSelectDemoUser,
  onOpenAuthModal,
  onLogout,
}) {
  const isLoggedIn = Boolean(user?.id || user?.user_id);
  const userName = user?.name || "Guest";
  const userInitial = userName.charAt(0).toUpperCase();
  const workerType = user?.worker_type || user?.userType || "";

  return (
    <header id="taxsaint-navbar">
      <div className="navbar-brand">
        <h1>{title}</h1>
        <span className="navbar-badge">FY 2026-27 (New Regime)</span>
      </div>

      <div className="navbar-actions">
        {onSelectDemoUser && (
          <div className="demo-selector-group">
            <span>Demo Persona:</span>
            <select
              aria-label="Demo Persona"
              onChange={(e) => onSelectDemoUser(e.target.value)}
              value={user?.id || user?.user_id || ""}
            >
              <option value="" disabled>Switch Persona...</option>
              <option value="1">Rahul Sharma (Salaried - ₹15L)</option>
              <option value="2">Priya Patel (Business - Anomaly Demo)</option>
            </select>
          </div>
        )}

        {isLoggedIn ? (
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              className="user-chip"
              onClick={onProfileClick}
              title="View profile details"
              role="button"
              tabIndex={0}
            >
              <div className="user-avatar">{userInitial}</div>
              <div style={{ display: "flex", flexDirection: "column", textAlign: "left" }}>
                <span style={{ fontWeight: "600", fontSize: "13px" }}>{userName}</span>
                {workerType && (
                  <span
                    style={{
                      fontSize: "10px",
                      color: workerType.toUpperCase() === "SALARIED" ? "#38bdf8" : "#fbbf24",
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                    }}
                  >
                    {workerType}
                  </span>
                )}
              </div>
            </div>

            {onLogout && (
              <button
                onClick={onLogout}
                title="Log out from current account"
                style={{
                  backgroundColor: "rgba(239, 68, 68, 0.15)",
                  color: "#fca5a5",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  borderRadius: "8px",
                  padding: "6px 12px",
                  fontSize: "12px",
                  fontWeight: "600",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                }}
              >
                Logout
              </button>
            )}
          </div>
        ) : (
          <button
            onClick={onOpenAuthModal}
            style={{
              backgroundColor: "#2563eb",
              color: "#ffffff",
              border: "none",
              borderRadius: "8px",
              padding: "8px 18px",
              fontSize: "13px",
              fontWeight: "600",
              cursor: "pointer",
              boxShadow: "0 2px 4px rgba(37, 99, 235, 0.3)",
              transition: "background-color 0.2s ease",
            }}
          >
            Sign In / Register
          </button>
        )}
      </div>
    </header>
  );
}

export default Navbar;
