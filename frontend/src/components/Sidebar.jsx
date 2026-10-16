// TaxSaint application sidebar
import React from "react";

function Sidebar({
  currentPage = "dashboard",
  onPageChange,
  alertCount = 0
}) {
  const navigationItems = [
    { id: "dashboard", label: "Dashboard", icon: "📊" },
    { id: "salaried", label: "Salaried Employee", icon: "💼" },
    { id: "business", label: "Business Owner", icon: "🏢" },
    { id: "results-analytics", label: "Results & Analytics", icon: "📈", badge: alertCount },
    { id: "profile", label: "Profile Settings", icon: "👤" }
  ];

  return (
    <aside id="taxsaint-sidebar" aria-label="Main sidebar navigation">
      <span className="sidebar-heading">Navigation</span>
      <nav style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
        {navigationItems.map((item) => {
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`sidebar-btn ${isActive ? "active" : ""}`}
              onClick={() => onPageChange(item.id)}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
              {Boolean(item.badge) && item.badge > 0 && (
                <span className="sidebar-badge">{item.badge}</span>
              )}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}

export default Sidebar;