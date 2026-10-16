// TaxSaint top navigation bar
import React from "react";

function Navbar({
  title = "TaxSaint",
  user = null,
  onProfileClick,
  onSelectDemoUser,
}) {
  const userName = user?.name || "Guest";
  const userInitial = userName.charAt(0).toUpperCase();

  return (
    <header id="taxsaint-navbar">
      <div className="navbar-brand">
        <h1>{title}</h1>
        <span className="navbar-badge">FY 2026-27</span>
      </div>

      <div className="navbar-actions">
        {onSelectDemoUser && (
          <div className="demo-selector-group">
            <span>Demo Persona:</span>
            <select
              aria-label="Demo Persona"
              onChange={(e) => onSelectDemoUser(e.target.value)}
              defaultValue=""
            >
              <option value="" disabled>Select Demo Profile...</option>
              <option value="1">Rahul Sharma (Salaried - ₹15L)</option>
              <option value="2">Priya Patel (Business - Anomaly Demo)</option>
            </select>
          </div>
        )}

        <div
          className="user-chip"
          onClick={onProfileClick}
          title="View profile"
          role="button"
          tabIndex={0}
        >
          <div className="user-avatar">{userInitial}</div>
          <span>{userName}</span>
        </div>
      </div>
    </header>
  );
}

export default Navbar;