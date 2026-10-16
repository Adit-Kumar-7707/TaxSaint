// TaxSaint modern tax result component with slab-by-slab breakdown
import React from "react";

function TaxResult({
  result = null,
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
    <div className="content-card" style={{ textAlign: "center", padding: "2.5rem" }}>
      <p style={{ color: "var(--text-muted)" }}>Calculating tax using C++ progressive engine...</p>
    </div>
  );

  const renderError = () => {
    const errorMessage =
      error instanceof Error ? error.message : String(error || "Unable to load tax results.");
    return (
      <div className="taxsaint-banner error" role="alert">
        <span>{errorMessage}</span>
      </div>
    );
  };

  const renderEmpty = () => (
    <div className="content-card" style={{ textAlign: "center", padding: "2.5rem" }}>
      <h3>No Tax Calculation Yet</h3>
      <p style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
        Enter your income and expenses or select a demo profile to view your progressive tax calculation and slab breakdown.
      </p>
    </div>
  );

  const renderResult = () => {
    const totalTax = Number(result.totalTax ?? result.total_tax) || 0;
    const taxableIncome = Number(result.taxableIncome ?? result.taxable_income) || 0;
    const grossIncome = Number(result.income ?? result.gross_income) || 0;
    const expenses = Number(result.expenses) || 0;
    const taxBeforeCess = Number(result.tax ?? result.tax_before_cess) || 0;
    const cess = Number(result.cess) || 0;
    const slabs = result.slabBreakdown || result.slab_breakdown || [];

    const isRebateApplied = taxableIncome <= 1200000 && grossIncome > 0;

    return (
      <div className="tax-result-container">
        {/* Hero Card */}
        <div className="tax-summary-hero">
          <span className="hero-label">Net Tax Liability (FY 2026-27 New Regime)</span>
          <div className="hero-tax">{formatCurrency(totalTax)}</div>
          
          {isRebateApplied && (
            <div style={{ background: "rgba(255,255,255,0.2)", display: "inline-block", padding: "0.25rem 0.75rem", borderRadius: "6px", fontSize: "0.85rem", fontWeight: "600" }}>
              🎉 Section 87A Rebate Applied (Taxable Income ≤ ₹12,00,000)
            </div>
          )}

          <div className="hero-grid">
            <div className="hero-metric">
              <small>Gross Income</small>
              <strong>{formatCurrency(grossIncome)}</strong>
            </div>
            <div className="hero-metric">
              <small>Expenses / Deductions</small>
              <strong>{formatCurrency(expenses)}</strong>
            </div>
            <div className="hero-metric">
              <small>Taxable Income</small>
              <strong>{formatCurrency(taxableIncome)}</strong>
            </div>
            <div className="hero-metric">
              <small>Tax before Cess</small>
              <strong>{formatCurrency(taxBeforeCess)}</strong>
            </div>
            <div className="hero-metric">
              <small>Health & Ed Cess (4%)</small>
              <strong>{formatCurrency(cess)}</strong>
            </div>
          </div>
        </div>

        {/* Detailed Progressive Slab Breakdown Table */}
        {slabs.length > 0 && (
          <div className="content-card">
            <h3>Progressive Tax Slab Breakdown</h3>
            <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", marginBottom: "1rem" }}>
              Calculation breakdown determined by the C++ engine based on FY 2026-27 tax brackets:
            </p>

            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Income Slab (INR)</th>
                    <th>Rate</th>
                    <th>Taxable in Bracket</th>
                    <th>Computed Tax</th>
                  </tr>
                </thead>
                <tbody>
                  {slabs.map((slab, index) => {
                    const lower = Number(slab.lower) || 0;
                    const upper = slab.upper !== null && slab.upper !== undefined ? Number(slab.upper) : null;
                    const rate = Number(slab.rate) || 0;
                    const inSlab = Number(slab.taxable_in_slab ?? slab.taxableInSlab) || 0;
                    const taxInSlab = Number(slab.tax_in_slab ?? slab.taxInSlab) || 0;

                    const rangeText = upper !== null
                      ? `₹${(lower / 100000).toFixed(1)}L – ₹${(upper / 100000).toFixed(1)}L`
                      : `Above ₹${(lower / 100000).toFixed(1)}L`;

                    return (
                      <tr key={index} style={{ backgroundColor: inSlab > 0 ? "rgba(59, 130, 246, 0.04)" : "transparent" }}>
                        <td><strong>{rangeText}</strong></td>
                        <td>{rate}%</td>
                        <td>{formatCurrency(inSlab)}</td>
                        <td><strong>{formatCurrency(taxInSlab)}</strong></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <section id="taxsaint-tax-result">
      {loading ? renderLoading() : error ? renderError() : !result ? renderEmpty() : renderResult()}
    </section>
  );
}

export default TaxResult;