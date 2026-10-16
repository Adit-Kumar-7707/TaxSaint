// TaxSaint fraud alerts component
import React from "react";

function FraudAlerts({
  alerts = [],
  loading = false,
  error = null,
  onStatusChange = null
}) {
  const formatCurrency = (value) => {
    const numericValue = Number(value) || 0;
    return `₹${numericValue.toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  };

  const formatAlertType = (alertType) => {
    if (!alertType) return "Financial Anomaly";
    return String(alertType)
      .toLowerCase()
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const renderLoading = () => (
    <div className="content-card" style={{ textAlign: "center", padding: "2rem" }}>
      <p style={{ color: "var(--text-muted)" }}>Scanning transactions for anomalies...</p>
    </div>
  );

  const renderError = () => {
    const errorMessage =
      error instanceof Error ? error.message : String(error || "Unable to load fraud alerts.");
    return (
      <div className="taxsaint-banner error" role="alert">
        <span>{errorMessage}</span>
      </div>
    );
  };

  const renderEmpty = () => (
    <div className="content-card" style={{ textAlign: "center", padding: "2rem" }}>
      <h3 style={{ color: "var(--success)" }}>✅ Clean Financial Record</h3>
      <p style={{ color: "var(--text-muted)", marginTop: "0.4rem" }}>
        No duplicate expenses or income mismatches detected. All records reconcile cleanly.
      </p>
    </div>
  );

  const renderStatus = (status) => {
    const normalized = String(status || "NEEDS_VERIFICATION").toUpperCase();
    switch (normalized) {
      case "VERIFIED":
        return <span className="badge badge-success">Verified</span>;
      case "DISMISSED":
        return <span className="badge badge-muted">Dismissed</span>;
      case "NEEDS_VERIFICATION":
      default:
        return <span className="badge badge-warning">Needs Review</span>;
    }
  };

  const handleStatusChange = (alertId, status) => {
    if (typeof onStatusChange === "function" && alertId) {
      onStatusChange(alertId, status);
    }
  };

  const renderAlert = (alert) => {
    const alertId = alert.id ?? alert.alert_id;
    return (
      <article
        key={alertId}
        className="content-card"
        style={{
          borderLeft: alert.status === "VERIFIED" ? "4px solid var(--success)" : alert.status === "DISMISSED" ? "4px solid var(--text-muted)" : "4px solid var(--warning)",
          marginBottom: "1rem"
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <h4 style={{ fontSize: "1.05rem", fontWeight: "600", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span>⚠️</span>
            <span>{formatAlertType(alert.alertType ?? alert.fraud_type)}</span>
          </h4>
          {renderStatus(alert.status)}
        </div>

        <p style={{ fontSize: "0.92rem", color: "var(--text-main)", marginBottom: "1rem" }}>
          {alert.message || alert.reason || "This transaction requires verification."}
        </p>

        <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
          {alert.partyName && (
            <div>
              <span>Counterparty: </span>
              <strong style={{ color: "var(--text-main)" }}>{alert.partyName}</strong>
            </div>
          )}
          {(alert.amount !== undefined || alert.difference_amount !== undefined) && (
            <div>
              <span>Discrepancy / Amount: </span>
              <strong style={{ color: "var(--danger)" }}>
                {formatCurrency(alert.amount ?? alert.difference_amount)}
              </strong>
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: "0.35rem 0.85rem", fontSize: "0.82rem" }}
            onClick={() => handleStatusChange(alertId, "VERIFIED")}
            disabled={alert.status === "VERIFIED"}
          >
            Mark Verified
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: "0.35rem 0.85rem", fontSize: "0.82rem" }}
            onClick={() => handleStatusChange(alertId, "DISMISSED")}
            disabled={alert.status === "DISMISSED"}
          >
            Dismiss Alert
          </button>
        </div>
      </article>
    );
  };

  const renderAlerts = () => {
    if (!Array.isArray(alerts) || alerts.length === 0) {
      return renderEmpty();
    }
    return (
      <div id="fraud-alerts-list">
        {alerts.map((alert) => renderAlert(alert))}
      </div>
    );
  };

  return (
    <section id="taxsaint-fraud-alerts">
      <header style={{ marginBottom: "1.25rem" }}>
        <h2>Potential Financial Discrepancies</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.88rem" }}>
          Algorithmic anomaly flags requiring accountant or user verification before tax filing.
        </p>
      </header>

      <div id="fraud-alerts-content">
        {loading ? renderLoading() : error ? renderError() : renderAlerts()}
      </div>
    </section>
  );
}

export default FraudAlerts;