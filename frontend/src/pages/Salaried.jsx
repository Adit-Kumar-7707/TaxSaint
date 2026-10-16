// TaxSaint salaried employee page
import React, { useState } from "react";
import PageContainer from "../components/PageContainer.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import SuccessMessage from "../components/SuccessMessage.jsx";
import IncomeForm from "../components/forms/IncomeForm.jsx";
import TaxResult from "../components/TaxResult.jsx";
import FileUpload from "../components/FileUpload.jsx";

function Salaried({
  user = null,
  taxResult = null,
  loading = false,
  error = null,
  successMessage = "",
  onIncomeSubmit,
  onCalculateTax,
  onUploadSuccess,
  onRetry,
  onDismissSuccess
}) {
  const [financialData, setFinancialData] = useState({
    salary: "",
    deductions: "",
    otherIncome: ""
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

  const handleTaxCalculation = (event) => {
    event.preventDefault();
    const taxData = {
      userId: user?.id ?? user?.user_id ?? null,
      userType: "salaried",
      salary: Number(financialData.salary) || 0,
      deductions: Number(financialData.deductions) || 0,
      otherIncome: Number(financialData.otherIncome) || 0
    };

    if (typeof onCalculateTax === "function") {
      onCalculateTax(taxData);
    }
  };

  return (
    <PageContainer
      title="Salaried Employee Tax Filing"
      subtitle="Input salary, claim standard deduction, upload payslips, and calculate New Regime tax liability."
    >
      {loading && <Loading message="Processing tax information..." />}
      {error && <ErrorMessage message={error} onRetry={onRetry} />}
      {successMessage && <SuccessMessage message={successMessage} onDismiss={onDismissSuccess} />}

      {/* Regime Guidance Banner */}
      <div className="notice-box">
        <strong>💡 FY 2026-27 New Tax Regime Highlights</strong>
        <span>
          Salaried individuals receive an automatic <strong>₹75,000 standard deduction</strong>. 
          Additionally, taxable income up to <strong>₹12,00,000</strong> pays <strong>₹0 tax</strong> thanks to the enhanced Section 87A rebate!
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.75rem", marginBottom: "1.75rem" }}>
        {/* Quick Tax Simulation Card */}
        <div className="content-card">
          <h3>Quick Tax Calculation</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", marginBottom: "1.25rem" }}>
            Enter your annual figures below to simulate instant tax:
          </p>

          <form onSubmit={handleTaxCalculation}>
            <div className="form-field" style={{ marginBottom: "1rem" }}>
              <label htmlFor="salaried-salary">Annual Gross Salary (₹)</label>
              <input
                id="salaried-salary"
                name="salary"
                type="number"
                value={financialData.salary}
                onChange={handleChange}
                placeholder="e.g. 1500000"
                min="0"
                step="0.01"
              />
            </div>

            <div className="form-field" style={{ marginBottom: "1rem" }}>
              <label htmlFor="salaried-other-income">Other Income (Interest / Freelance) (₹)</label>
              <input
                id="salaried-other-income"
                name="otherIncome"
                type="number"
                value={financialData.otherIncome}
                onChange={handleChange}
                placeholder="e.g. 45000"
                min="0"
                step="0.01"
              />
            </div>

            <div className="form-field" style={{ marginBottom: "1.5rem" }}>
              <label htmlFor="salaried-deductions">
                Additional Deductions (₹)
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginLeft: "0.5rem" }}>
                  (Note: New regime applies ₹75k standard deduction)
                </span>
              </label>
              <input
                id="salaried-deductions"
                name="deductions"
                type="number"
                value={financialData.deductions}
                onChange={handleChange}
                placeholder="Optional"
                min="0"
                step="0.01"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: "100%" }}
              disabled={loading}
            >
              Calculate Tax with C++ Engine
            </button>
          </form>
        </div>

        {/* Statement Import Card */}
        <div className="content-card">
          <h3>Upload Statement or Payslip</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", marginBottom: "1.25rem" }}>
            Batch import monthly salary entries and bank credits from a CSV statement:
          </p>

          <FileUpload
            userId={user?.id ?? user?.user_id}
            onUploadSuccess={onUploadSuccess}
            disabled={loading}
          />
        </div>
      </div>

      {/* Manual Income Entry */}
      <div className="content-card">
        <h3>Record Individual Income Item</h3>
        <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", marginBottom: "1rem" }}>
          Add one-off compensation or consulting income entries:
        </p>
        <IncomeForm onSubmit={handleIncomeSubmit} loading={loading} />
      </div>

      {/* Render Tax Calculation Result */}
      {taxResult && (
        <div style={{ marginTop: "2rem" }}>
          <TaxResult result={taxResult} loading={loading} />
        </div>
      )}
    </PageContainer>
  );
}

export default Salaried;