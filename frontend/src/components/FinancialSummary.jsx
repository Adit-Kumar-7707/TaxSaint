// TaxSaint financial summary component

import React from "react";

// financial summary component
function FinancialSummary({
  summary = null,
  loading = false,
  error = null
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

 // render loading state
const renderLoading = () => {
  // return loading state
  return (
    <div
      id="financial-summary-loading"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <p>Loading financial summary...</p>
    </div>
  );
};

// render error state
const renderError = () => {
  // determine readable error message
  const errorMessage =
    error instanceof Error
      ? error.message
      : String(error || "Unable to load financial summary.");

  // return error state
  return (
    <div
      id="financial-summary-error"
      role="alert"
      aria-live="assertive"
    >
      <h3>Unable to load financial summary</h3>

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
      id="financial-summary-empty"
      role="status"
      aria-live="polite"
    >
      <h3>No Financial Summary Available</h3>

      <p>
        Add income and expense data to view your financial summary.
      </p>
    </div>
  );
};

// render financial summary
const renderSummary = () => {
  // return financial summary cards
  return (
    <div id="financial-summary-grid">

      {/* total income */}
      <article className="financial-summary-card">
        <span className="financial-summary-label">
          Income
        </span>

        <strong className="financial-summary-value">
          {formatCurrency(summary.income)}
        </strong>
      </article>

      {/* total expenses */}
      <article className="financial-summary-card">
        <span className="financial-summary-label">
          Expenses
        </span>

        <strong className="financial-summary-value">
          {formatCurrency(summary.expenses)}
        </strong>
      </article>

      {/* net position */}
      <article className="financial-summary-card financial-summary-net">
        <span className="financial-summary-label">
          Net Position
        </span>

        <strong className="financial-summary-value">
          {formatCurrency(summary.netPosition)}
        </strong>
      </article>

    </div>
  );
};

  // financial summary component layout
  return (
    <section id="taxsaint-financial-summary">

      {/* component heading */}
      <header id="financial-summary-header">
        <h2>Financial Summary</h2>

        <p>
          Summary of your income, expenses and net position.
        </p>
      </header>

{/* component content */}
<div id="financial-summary-content">

  {loading
    ? renderLoading()
    : error
      ? renderError()
      : !summary
        ? renderEmpty()
        : renderSummary()
  }

</div>

    </section>
  );
}

// export financial summary component
export default FinancialSummary;