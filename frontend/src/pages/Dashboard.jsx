// TaxSaint modern dashboard page
import React from "react";
import PageContainer from "../components/PageContainer.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import SuccessMessage from "../components/SuccessMessage.jsx";

function Dashboard({
  user = null,
  summary = null,
  taxResult = null,
  alerts = [],
  loading = false,
  error = null,
  successMessage = "",
  onRetry,
  onDismissSuccess,
  onNavigate
}) {
  const formatCurrency = (value) => {
    const num = Number(value) || 0;
    return `₹${num.toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  };

  const income = Number(summary?.income ?? summary?.totalIncome ?? 0);
  const expenses = Number(summary?.expenses ?? summary?.totalExpenses ?? 0);
  const netPosition = Number(summary?.netPosition ?? summary?.netIncome ?? (income - expenses));
  const totalTax = Number(taxResult?.totalTax ?? taxResult?.total_tax ?? 0);
  const pendingAlerts = alerts.filter(a => a.status === "NEEDS_VERIFICATION" || !a.status);

  return (
    <PageContainer
      title="Financial Dashboard"
      subtitle="Overview of your financial positions, tax calculations, and algorithmic verification alerts."
    >
      {loading && <Loading message="Refreshing financial positions..." />}
      {error && <ErrorMessage message={error} onRetry={onRetry} />}
      {successMessage && <SuccessMessage message={successMessage} onDismiss={onDismissSuccess} />}

      {/* User Welcome Notice */}
      <div className="notice-box">
        <strong>
          {user ? `Welcome back, ${user.name}` : "Welcome to TaxSaint"}
        </strong>
        <span>
          {user
            ? `Active Persona: ${user.worker_type || user.userType || "User"} (FY 2026-27 New Tax Regime). All calculations follow the latest rebate and progressive slab updates.`
            : "No user is currently selected. Select a demo persona in the top right or create a profile to begin."}
        </span>
      </div>

      {/* 4 Metric Cards */}
      <div className="dashboard-grid">
        <div className="stat-card">
          <span className="label">Total Recorded Income</span>
          <div className="value income">{formatCurrency(income)}</div>
          <span className="subtext">From all verified sources</span>
        </div>

        <div className="stat-card">
          <span className="label">Total Expenses</span>
          <div className="value expenses">{formatCurrency(expenses)}</div>
          <span className="subtext">Deductible & operating costs</span>
        </div>

        <div className="stat-card">
          <span className="label">Net Position</span>
          <div className={`value ${netPosition >= 0 ? "income" : "danger"}`}>
            {formatCurrency(netPosition)}
          </div>
          <span className="subtext">{netPosition >= 0 ? "Net Surplus" : "Net Deficit"}</span>
        </div>

        <div className="stat-card">
          <span className="label">Estimated Net Tax</span>
          <div className="value tax">{formatCurrency(totalTax)}</div>
          <span className="subtext">
            {taxResult ? "Calculated via C++ Engine" : "Not yet computed"}
          </span>
        </div>
      </div>

      {/* Quick Action Hub */}
      <div className="content-card">
        <h3>Quick Action Workflows</h3>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "1.25rem" }}>
          Select an action to input financial data, run simulations, or reconcile anomalies:
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: "1.25rem", flexDirection: "column", gap: "0.35rem", alignItems: "flex-start", textAlign: "left" }}
            onClick={() => onNavigate("salaried")}
          >
            <span style={{ fontSize: "1.25rem" }}>💼</span>
            <strong>Salaried Employee</strong>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Salary input & ₹75k standard deduction
            </span>
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: "1.25rem", flexDirection: "column", gap: "0.35rem", alignItems: "flex-start", textAlign: "left" }}
            onClick={() => onNavigate("business")}
          >
            <span style={{ fontSize: "1.25rem" }}>🏢</span>
            <strong>Business Owner</strong>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Revenue, vendor expenses & statements
            </span>
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: "1.25rem", flexDirection: "column", gap: "0.35rem", alignItems: "flex-start", textAlign: "left" }}
            onClick={() => onNavigate("results-analytics")}
          >
            <span style={{ fontSize: "1.25rem" }}>📈</span>
            <strong>Results & Analytics</strong>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Slab breakdown & {pendingAlerts.length} pending alert(s)
            </span>
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: "1.25rem", flexDirection: "column", gap: "0.35rem", alignItems: "flex-start", textAlign: "left" }}
            onClick={() => onNavigate("profile")}
          >
            <span style={{ fontSize: "1.25rem" }}>👤</span>
            <strong>Profile Settings</strong>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Manage name, email & worker type
            </span>
          </button>
        </div>
      </div>

      {/* Active Anomaly Alerts Preview */}
      {alerts && alerts.length > 0 && (
        <div className="content-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h3>Algorithmic Anomaly Flags ({pendingAlerts.length} Pending Review)</h3>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ fontSize: "0.82rem", padding: "0.3rem 0.75rem" }}
              onClick={() => onNavigate("results-analytics")}
            >
              Review All Alerts →
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {alerts.slice(0, 3).map((alert, index) => (
              <div
                key={alert.id || index}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "0.75rem 1rem",
                  background: "#f8fafc",
                  borderLeft: "4px solid var(--warning)",
                  borderRadius: "6px"
                }}
              >
                <div>
                  <strong style={{ fontSize: "0.9rem" }}>{alert.reason || alert.message}</strong>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    Source: {alert.transaction_source || "Transaction"} • Discrepancy: ₹{alert.difference_amount || alert.amount || 0}
                  </div>
                </div>
                <span className="badge badge-warning">{alert.status || "NEEDS_VERIFICATION"}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </PageContainer>
  );
}

export default Dashboard;