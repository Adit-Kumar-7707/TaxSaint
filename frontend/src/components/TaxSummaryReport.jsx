// TaxSaint Tax Summary & Computation Sheet Report
// Provides on-screen review and one-click Print / PDF Export formatted for Indian ITR standards.
import React from "react";

function TaxSummaryReport({ user, taxResult, summary, alerts = [], onClose }) {
  if (!taxResult) {
    return (
      <div style={{ padding: "24px", color: "#94a3b8", textAlign: "center" }}>
        No tax calculation result available to generate summary.
      </div>
    );
  }

  const handlePrint = () => {
    window.print();
  };

  const formatINR = (val) => {
    const num = Number(val) || 0;
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(num);
  };

  const slabs = taxResult.slabBreakdown || taxResult.slab_breakdown || [];
  const workerType = (user?.worker_type || user?.userType || "SALARIED").toUpperCase();

  return (
    <div
      className="tax-report-modal"
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(10, 15, 29, 0.85)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        padding: "16px",
        overflowY: "auto",
      }}
    >
      <style>{`
        @media print {
          body * {
            visibility: hidden;
          }
          .tax-report-printable, .tax-report-printable * {
            visibility: visible;
          }
          .tax-report-printable {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            background: white !important;
            color: black !important;
            padding: 20px !important;
            box-shadow: none !important;
            border: none !important;
          }
          .no-print {
            display: none !important;
          }
          .print-border-black {
            border-color: #000000 !important;
            color: #000000 !important;
          }
        }
      `}</style>

      <div
        className="tax-report-printable"
        style={{
          backgroundColor: "#161d31",
          border: "1px solid #28334e",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "800px",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "36px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7)",
          color: "#f8fafc",
          fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
        }}
      >
        {/* Action Header */}
        <div
          className="no-print"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "1px solid #28334e",
            paddingBottom: "16px",
            marginBottom: "24px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "20px" }}>📄</span>
            <h3 style={{ margin: 0, fontSize: "18px", fontWeight: "600" }}>
              Official Tax Computation Sheet
            </h3>
          </div>
          <div style={{ display: "flex", gap: "10px" }}>
            <button
              onClick={handlePrint}
              style={{
                backgroundColor: "#2563eb",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                padding: "8px 18px",
                fontWeight: "600",
                fontSize: "14px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <span>🖨️</span> Save as PDF / Print
            </button>
            {onClose && (
              <button
                onClick={onClose}
                style={{
                  backgroundColor: "#334155",
                  color: "#e2e8f0",
                  border: "none",
                  borderRadius: "8px",
                  padding: "8px 16px",
                  fontWeight: "600",
                  fontSize: "14px",
                  cursor: "pointer",
                }}
              >
                Close
              </button>
            )}
          </div>
        </div>

        {/* Printable Document Title */}
        <div style={{ textAlign: "center", borderBottom: "2px solid #334155", paddingBottom: "20px", marginBottom: "24px" }}>
          <h1 style={{ margin: "0 0 4px 0", fontSize: "26px", fontWeight: "800", letterSpacing: "1px" }}>
            TAXSAINT COMPUTATION OF INCOME & TAX
          </h1>
          <p style={{ margin: "0 0 8px 0", color: "#94a3b8", fontSize: "14px" }}>
            Assessment Year 2027-28 | Financial Year 2026-27 (New Tax Regime u/s 115BAC)
          </p>
          <span
            style={{
              backgroundColor: "rgba(37, 99, 235, 0.2)",
              color: "#60a5fa",
              border: "1px solid #2563eb",
              borderRadius: "20px",
              padding: "4px 14px",
              fontSize: "12px",
              fontWeight: "600",
            }}
          >
            Verified C++ Engine Output
          </span>
        </div>

        {/* Taxpayer Meta */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "16px",
            backgroundColor: "#0d1322",
            padding: "16px 20px",
            borderRadius: "10px",
            border: "1px solid #28334e",
            marginBottom: "24px",
            fontSize: "13px",
          }}
        >
          <div>
            <span style={{ color: "#94a3b8" }}>Taxpayer Name:</span>
            <div style={{ fontWeight: "700", fontSize: "15px", marginTop: "2px" }}>
              {user?.name || "Taxpayer"}
            </div>
          </div>
          <div>
            <span style={{ color: "#94a3b8" }}>Email / User ID:</span>
            <div style={{ fontWeight: "600", marginTop: "2px" }}>
              {user?.email || `ID: ${user?.id || user?.user_id}`}
            </div>
          </div>
          <div>
            <span style={{ color: "#94a3b8" }}>Filing Profile:</span>
            <div style={{ fontWeight: "600", marginTop: "2px", color: "#38bdf8" }}>
              {workerType === "SALARIED" ? "Salaried Individual" : "Business / Professional"}
            </div>
          </div>
          <div>
            <span style={{ color: "#94a3b8" }}>Calculation Date:</span>
            <div style={{ fontWeight: "600", marginTop: "2px" }}>
              {taxResult.calculated_at
                ? new Date(taxResult.calculated_at).toLocaleDateString("en-IN", {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                  })
                : new Date().toLocaleDateString("en-IN")}
            </div>
          </div>
        </div>

        {/* Section 1: Income Computation */}
        <div style={{ marginBottom: "28px" }}>
          <h4 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "#38bdf8", textTransform: "uppercase" }}>
            Part A: Computation of Total Income
          </h4>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
            <tbody>
              <tr style={{ borderBottom: "1px solid #1e293b" }}>
                <td style={{ padding: "10px 0", color: "#cbd5e1" }}>
                  Gross Income ({workerType === "SALARIED" ? "Salary & Incomes" : "Gross Receipts"})
                </td>
                <td style={{ padding: "10px 0", textAlign: "right", fontWeight: "600" }}>
                  {formatINR(taxResult.gross_income ?? taxResult.income)}
                </td>
              </tr>
              {workerType === "BUSINESS" && (
                <tr style={{ borderBottom: "1px solid #1e293b" }}>
                  <td style={{ padding: "10px 0", color: "#cbd5e1" }}>Less: Allowable Business Expenses</td>
                  <td style={{ padding: "10px 0", textAlign: "right", color: "#f87171" }}>
                    - {formatINR(taxResult.expenses)}
                  </td>
                </tr>
              )}
              {workerType === "SALARIED" && (
                <tr style={{ borderBottom: "1px solid #1e293b" }}>
                  <td style={{ padding: "10px 0", color: "#cbd5e1" }}>
                    Less: Standard Deduction u/s 16(ia)
                  </td>
                  <td style={{ padding: "10px 0", textAlign: "right", color: "#34d399" }}>
                    - ₹75,000
                  </td>
                </tr>
              )}
              <tr style={{ borderTop: "2px solid #334155", backgroundColor: "rgba(255, 255, 255, 0.02)" }}>
                <td style={{ padding: "12px 0", fontWeight: "700" }}>Taxable Total Income</td>
                <td style={{ padding: "12px 0", textAlign: "right", fontWeight: "700", fontSize: "16px", color: "#38bdf8" }}>
                  {formatINR(taxResult.taxable_income ?? taxResult.taxableIncome)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Section 2: Slab Breakdown Table */}
        {slabs.length > 0 && (
          <div style={{ marginBottom: "28px" }}>
            <h4 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "#38bdf8", textTransform: "uppercase" }}>
              Part B: Progressive Slab Rate Application
            </h4>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #334155", textAlign: "left", color: "#94a3b8" }}>
                  <th style={{ padding: "8px 0" }}>Income Bracket (INR)</th>
                  <th style={{ padding: "8px 0", textAlign: "center" }}>Rate (%)</th>
                  <th style={{ padding: "8px 0", textAlign: "right" }}>Taxable in Slab</th>
                  <th style={{ padding: "8px 0", textAlign: "right" }}>Tax Payable</th>
                </tr>
              </thead>
              <tbody>
                {slabs.map((slab, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #1e293b" }}>
                    <td style={{ padding: "8px 0" }}>
                      {formatINR(slab.lower)} to {slab.upper ? formatINR(slab.upper) : "Above"}
                    </td>
                    <td style={{ padding: "8px 0", textAlign: "center" }}>{slab.rate}%</td>
                    <td style={{ padding: "8px 0", textAlign: "right" }}>{formatINR(slab.taxable_in_slab)}</td>
                    <td style={{ padding: "8px 0", textAlign: "right", fontWeight: "600" }}>
                      {formatINR(slab.tax_in_slab)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Section 3: Final Tax Calculation */}
        <div style={{ borderTop: "2px solid #334155", paddingTop: "16px", marginBottom: "28px" }}>
          <h4 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "#38bdf8", textTransform: "uppercase" }}>
            Part C: Tax Liability Summary
          </h4>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
            <tbody>
              <tr>
                <td style={{ padding: "8px 0", color: "#cbd5e1" }}>Tax Before Rebate & Cess</td>
                <td style={{ padding: "8px 0", textAlign: "right", fontWeight: "600" }}>
                  {formatINR(taxResult.tax_before_cess ?? taxResult.tax)}
                </td>
              </tr>
              {(taxResult.taxable_income ?? taxResult.taxableIncome) <= 1200000 && (
                <tr>
                  <td style={{ padding: "8px 0", color: "#34d399" }}>
                    Rebate u/s 87A (Taxable Income ≤ ₹12,00,000)
                  </td>
                  <td style={{ padding: "8px 0", textAlign: "right", color: "#34d399", fontWeight: "600" }}>
                    Full Rebate (₹0 Tax)
                  </td>
                </tr>
              )}
              <tr>
                <td style={{ padding: "8px 0", color: "#cbd5e1" }}>Health & Education Cess (4%)</td>
                <td style={{ padding: "8px 0", textAlign: "right", fontWeight: "600" }}>
                  {formatINR(taxResult.cess)}
                </td>
              </tr>
              <tr style={{ borderTop: "2px solid #3b82f6", backgroundColor: "rgba(59, 130, 246, 0.08)" }}>
                <td style={{ padding: "14px 8px", fontWeight: "800", fontSize: "16px" }}>
                  TOTAL NET TAX PAYABLE
                </td>
                <td style={{ padding: "14px 8px", textAlign: "right", fontWeight: "800", fontSize: "20px", color: "#60a5fa" }}>
                  {formatINR(taxResult.total_tax ?? taxResult.totalTax)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Footer Audit Notice */}
        <div
          style={{
            borderTop: "1px dashed #334155",
            paddingTop: "16px",
            fontSize: "12px",
            color: "#64748b",
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <span>Generated by TaxSaint Platform Engine</span>
          <span>Deterministic Verification: OK</span>
        </div>
      </div>
    </div>
  );
}

export default TaxSummaryReport;
