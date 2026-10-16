// TaxSaint financial summary component
import React from "react";

function FinancialSummary({
  summary = null,
  loading = false,
  error = null
}) {
  const formatCurrency = (value) => {
    const numericValue = Number(value) || 0;
    return `₹${numericValue.toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  };

  const renderLoading = () => (
    <div className="content-card" style={{ textAlign: "center", padding: "1.5rem" }}>
      <p style={{ color: "var(--text-muted)" }}>Loading financial summary...</p>
    </div>
  );

  const renderError = () => {
    const errorMessage =
      error instanceof Error ? error.message : String(error || "Unable to load financial summary.");
    return (
      <div className="taxsaint-banner error" role="alert">
        <span>{errorMessage}</span>
      </div>
    );
  };

  const renderEmpty = () => (
    <div className="content-card" style={{ textAlign: "center", padding: "1.5rem" }}>
      <p style={{ color: "var(--text-muted)" }}>
        No financial records recorded yet. Add income or upload a statement to view summary totals.
      </p>
    </div>
  );

  const renderSummary = () => {
    const income = Number(summary.income ?? summary.total_income ?? summary.totalIncome) || 0;
    const expenses = Number(summary.expenses ?? summary.total_expenses ?? summary.totalExpenses) || 0;
    const net = Number(summary.netPosition ?? summary.net_position) || (income - expenses);

    return (
      <div className="dashboard-grid">
        <div className="stat-card">
          <span className="label">Total Recorded Income</span>
          <div className="value income">{formatCurrency(income)}</div>
          <span className="subtext">Invoices, Salary & Credits</span>
        </div>

        <div className="stat-card">
          <span className="label">Total Expenses</span>
          <div className="value expenses">{formatCurrency(expenses)}</div>
          <span className="subtext">Vendor Payments & Deductions</span>
        </div>

        <div className="stat-card">
          <span className="label">Net Position</span>
          <div className={`value ${net >= 0 ? "income" : "danger"}`}>
            {formatCurrency(net)}
          </div>
          <span className="subtext">{net >= 0 ? "Surplus" : "Deficit"}</span>
        </div>
      </div>
    );
  };

  return (
    <section id="taxsaint-financial-summary">
      <header style={{ marginBottom: "1rem" }}>
        <h2>Financial Position</h2>
      </header>

      <div id="financial-summary-content">
        {loading ? renderLoading() : error ? renderError() : !summary ? renderEmpty() : renderSummary()}
      </div>
    </section>
  );
}

export default FinancialSummary;