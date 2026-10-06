// TaxSaint fraud alerts component

import React from "react";

// fraud alerts component
function FraudAlerts({
  alerts = [],
  loading = false,
  error = null,
  onStatusChange = null
}) {

// format currency value
const formatCurrency = (value) => {
  // convert value into a number
  const numericValue = Number(value) || 0;

  // format value using Indian currency notation
  return `₹${numericValue.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
};

// format alert type
const formatAlertType = (alertType) => {
  // handle missing alert type
  if (!alertType) {
    return "Financial Alert";
  }

  // convert alert type into readable text
  return String(alertType)
    .toLowerCase()
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

// render loading state
const renderLoading = () => {
  // return loading state
  return (
    <div
      id="fraud-alerts-loading"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <p>Loading fraud alerts...</p>
    </div>
  );
};

// render error state
const renderError = () => {
  // determine readable error message
  const errorMessage =
    error instanceof Error
      ? error.message
      : String(error || "Unable to load fraud alerts.");

  // return error state
  return (
    <div
      id="fraud-alerts-error"
      role="alert"
      aria-live="assertive"
    >
      <h3>Unable to load fraud alerts</h3>

      <p>
        {errorMessage}
      </p>
    </div>
  );
};

// render empty state
const renderEmpty = () => {
  // return empty state
  return (
    <div
      id="fraud-alerts-empty"
      role="status"
      aria-live="polite"
    >
      <h3>No Fraud Alerts</h3>

      <p>
        No potential financial issues require verification.
      </p>
    </div>
  );
};

// render alert status
const renderStatus = (status) => {
  // normalize status value
  const normalizedStatus = String(
    status || "NEEDS_VERIFICATION"
  ).toUpperCase();

  // return readable status
  switch (normalizedStatus) {
    case "VERIFIED":
      return (
        <span className="fraud-alert-status fraud-alert-status-verified">
          VERIFIED
        </span>
      );

    case "DISMISSED":
      return (
        <span className="fraud-alert-status fraud-alert-status-dismissed">
          DISMISSED
        </span>
      );

    case "NEEDS_VERIFICATION":
    default:
      return (
        <span className="fraud-alert-status fraud-alert-status-pending">
          NEEDS VERIFICATION
        </span>
      );
  }
};

// handle alert status change
const handleStatusChange = (alertId, status) => {
  // validate callback
  if (typeof onStatusChange !== "function") {
    return;
  }

  // validate alert identifier
  if (!alertId) {
    return;
  }

  // normalize status
  const normalizedStatus = String(status || "").toUpperCase();

  // allow only supported statuses
  const allowedStatuses = [
    "NEEDS_VERIFICATION",
    "VERIFIED",
    "DISMISSED"
  ];

  if (!allowedStatuses.includes(normalizedStatus)) {
    return;
  }

  // send status change to parent component
  onStatusChange(alertId, normalizedStatus);
};

// render individual alert
const renderAlert = (alert) => {
  // return alert card
  return (
    <article
      key={alert.id}
      className="fraud-alert-card"
    >

      {/* alert header */}
      <div className="fraud-alert-header">

        <h3>
          {formatAlertType(alert.alertType)}
        </h3>

        {renderStatus(alert.status)}

      </div>

      {/* alert message */}
      <p className="fraud-alert-message">
        {alert.message || "This transaction requires verification."}
      </p>

      {/* alert amount */}
      {alert.amount !== undefined &&
        alert.amount !== null && (
          <div className="fraud-alert-detail">

            <span>
              Amount
            </span>

            <strong>
              {formatCurrency(alert.amount)}
            </strong>

          </div>
        )}

      {/* alert party */}
      {alert.partyName && (
        <div className="fraud-alert-detail">

          <span>
            Party
          </span>

          <strong>
            {alert.partyName}
          </strong>

        </div>
      )}

      {/* alert actions */}
      <div className="fraud-alert-actions">

        <button
          type="button"
          onClick={() =>
            handleStatusChange(
              alert.id,
              "VERIFIED"
            )
          }
        >
          Verify
        </button>

        <button
          type="button"
          onClick={() =>
            handleStatusChange(
              alert.id,
              "DISMISSED"
            )
          }
        >
          Dismiss
        </button>

      </div>

    </article>
  );
};

// render all fraud alerts
const renderAlerts = () => {
  // validate alert collection
  if (!Array.isArray(alerts) || alerts.length === 0) {
    return renderEmpty();
  }

  // return alert collection
  return (
    <div id="fraud-alerts-list">
      {alerts.map((alert) => renderAlert(alert))}
    </div>
  );
};

  // fraud alerts component layout
  return (
    <section id="taxsaint-fraud-alerts">

      {/* component heading */}
      <header id="fraud-alerts-header">
        <h2>Fraud Alerts</h2>

        <p>
          Review financial records that may require verification.
        </p>
      </header>

// component content
<div id="fraud-alerts-content">

  {loading
    ? renderLoading()
    : error
      ? renderError()
      : renderAlerts()
  }

</div>

    </section>
  );
}

// export fraud alerts component
export default FraudAlerts;