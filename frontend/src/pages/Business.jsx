// TaxSaint business owner page
import React, { useState } from "react";
import PageContainer from "../components/PageContainer.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import SuccessMessage from "../components/SuccessMessage.jsx";
import IncomeForm from "../components/forms/IncomeForm.jsx";
import ExpenseForm from "../components/forms/ExpenseForm.jsx";
import TaxResult from "../components/TaxResult.jsx";
import FraudAlerts from "../components/FraudAlerts.jsx";
import FileUpload from "../components/FileUpload.jsx";

function Business({
  user = null,
  taxResult = null,
  alerts = [],
  loading = false,
  error = null,
  successMessage = "",
  onIncomeSubmit,
  onExpenseSubmit,
  onCalculateTax,
  onRunFraudCheck,
  onAlertStatusChange,
  onUploadSuccess,
  onRetry,
  onDismissSuccess
}) {
  const [financialData, setFinancialData] = useState({
    businessIncome: "",
    businessExpenses: "",
    deductions: ""
  });

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFinancialData((previous) => ({
      ...previous,
      [name]: value
    }));
  };

  const handleIncomeSubmit = (incomeData) => {
    if (typeof onIncomeSubmit === "function") {
      onIncomeSubmit(incomeData);
    }
  };

  const handleExpenseSubmit = (expenseData) => {
    if (typeof onExpenseSubmit === "function") {
      onExpenseSubmit(expenseData);
    }
  };

  const handleTaxCalculation = (event) => {
    event.preventDefault();
    const taxData = {
      userId: user?.id ?? user?.user_id ?? null,
      userType: "business",
      businessIncome: Number(financialData.businessIncome) || 0,
      businessExpenses: Number(financialData.businessExpenses) || 0,
      deductions: Number(financialData.deductions) || 0
    };

    if (typeof onCalculateTax === "function") {
      onCalculateTax(taxData);
    }
  };

  const handleFraudCheck = () => {
    if (typeof onRunFraudCheck === "function") {
      onRunFraudCheck();
    }
  };

  return (
    <PageContainer
      title="Business Financial Ledger & Tax"
      subtitle="Track revenue, claim operational vendor expenses, upload bank statements, and screen for anomalies."
    >
      {loading && <Loading message="Processing business financial data..." />}
      {error && <ErrorMessage message={error} onRetry={onRetry} />}
      {successMessage && <SuccessMessage message={successMessage} onDismiss={onDismissSuccess} />}

      {/* Grid: Quick Calculation + Statement Upload */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.75rem", marginBottom: "1.75rem" }}>
        {/* Quick Tax Simulation */}
        <div className="content-card">
          <h3>Business Tax Calculation</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", marginBottom: "1.25rem" }}>
            Compute net taxable profit and slab tax based on revenue less deductible expenses:
          </p>

          <form onSubmit={handleTaxCalculation}>
            <div className="form-field" style={{ marginBottom: "1rem" }}>
              <label htmlFor="business-income">Total Business Revenue / Receipts (₹)</label>
              <input
                id="business-income"
                name="businessIncome"
                type="number"
                value={financialData.businessIncome}
                onChange={handleChange}
                placeholder="e.g. 1050000"
                min="0"
                step="0.01"
              />
            </div>

            <div className="form-field" style={{ marginBottom: "1rem" }}>
              <label htmlFor="business-expenses">Deductible Operating Expenses (₹)</label>
              <input
                id="business-expenses"
                name="businessExpenses"
                type="number"
                value={financialData.businessExpenses}
                onChange={handleChange}
                placeholder="e.g. 51500"
                min="0"
                step="0.01"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: "100%", marginTop: "0.5rem" }}
              disabled={loading}
            >
              Calculate Business Tax
            </button>
          </form>
        </div>

        {/* Statement Import */}
        <div className="content-card">
          <h3>Upload Statement or Expense Sheet</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", marginBottom: "1.25rem" }}>
            Drag and drop an Excel or CSV statement to batch ingest client revenue or vendor bills:
          </p>

          <FileUpload
            userId={user?.id ?? user?.user_id}
            onUploadSuccess={onUploadSuccess}
            disabled={loading}
          />
        </div>
      </div>

      {/* Anomaly Detection Trigger Panel */}
      <div className="content-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3>Deterministic Anomaly & Fraud Screening</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.88rem" }}>
            Runs rules against user ledger to catch 7-day duplicate vendor expenses or bank-income discrepancies.
          </p>
        </div>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleFraudCheck}
          disabled={loading}
        >
          🔍 Run Anomaly Scan
        </button>
      </div>

      {/* Manual Entry Sections */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.75rem", marginBottom: "1.75rem" }}>
        <div className="content-card">
          <h3>Add Business Revenue</h3>
          <IncomeForm onSubmit={handleIncomeSubmit} loading={loading} />
        </div>

        <div className="content-card">
          <h3>Add Business Expense</h3>
          <ExpenseForm onSubmit={handleExpenseSubmit} loading={loading} />
        </div>
      </div>

      {/* Tax Result Preview */}
      {taxResult && (
        <div style={{ marginBottom: "2rem" }}>
          <TaxResult result={taxResult} loading={loading} />
        </div>
      )}

      {/* Fraud Alerts List */}
      <div className="content-card">
        <FraudAlerts
          alerts={alerts}
          loading={loading}
          onStatusChange={onAlertStatusChange}
        />
      </div>
    </PageContainer>
  );
}

export default Business;