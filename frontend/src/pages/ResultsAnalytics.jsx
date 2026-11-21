// TaxSaint Results & Analytics Page
// Displays tax results, financial summaries, charts, fraud alerts, and allows official computation sheet PDF export.

import React, { useCallback, useEffect, useState } from "react";

import TaxResult from "../components/TaxResult";
import FinancialSummary from "../components/FinancialSummary";
import FraudAlerts from "../components/FraudAlerts";
import AnalyticsChart from "../components/AnalyticsChart";
import TaxSummaryReport from "../components/TaxSummaryReport";

import {
  getFinancialSummary,
  getTaxResult,
  getFraudAlerts,
  updateFraudAlertStatus,
} from "../services/api";

function ResultsAnalytics({ user = null }) {
  const userId = user?.id ?? user?.user_id ?? null;

  const [taxResult, setTaxResult] = useState(null);
  const [financialSummary, setFinancialSummary] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [fraudAlerts, setFraudAlerts] = useState([]);
  const [showReportModal, setShowReportModal] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadResultsAndAnalytics = useCallback(async () => {
    if (userId === null || userId === undefined || userId === "") {
      setTaxResult(null);
      setFinancialSummary(null);
      setAnalyticsData(null);
      setFraudAlerts([]);
      setError(
        new Error(
          "No user is selected. Create, sign in, or select a user to view financial results."
        )
      );
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [taxResponse, summaryResponse, fraudResponse] =
        await Promise.all([
          getTaxResult(userId),
          getFinancialSummary(userId),
          getFraudAlerts(userId),
        ]);

      setTaxResult(taxResponse);
      setFinancialSummary(summaryResponse);

      const income =
        summaryResponse?.income ??
        summaryResponse?.total_income ??
        summaryResponse?.totalIncome ??
        0;

      const expenses =
        summaryResponse?.expenses ??
        summaryResponse?.total_expenses ??
        summaryResponse?.totalExpenses ??
        0;

      setAnalyticsData({
        income: Number(income) || 0,
        expenses: Number(expenses) || 0,
      });

      const receivedAlerts = Array.isArray(fraudResponse)
        ? fraudResponse
        : fraudResponse?.alerts ?? fraudResponse?.data ?? [];

      setFraudAlerts(
        Array.isArray(receivedAlerts) ? receivedAlerts : []
      );
    } catch (requestError) {
      console.error("Failed to load Results & Analytics:", requestError);
      setError(
        requestError instanceof Error
          ? requestError
          : new Error("Unable to load financial results.")
      );
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const handleFraudAlertStatusChange = useCallback(
    async (alertId, status) => {
      if (alertId === null || alertId === undefined || alertId === "") {
        setError(new Error("The selected fraud alert has no valid ID."));
        return;
      }

      const allowedStatuses = [
        "NEEDS_VERIFICATION",
        "VERIFIED",
        "DISMISSED",
      ];

      if (!allowedStatuses.includes(status)) {
        setError(new Error("Invalid fraud alert status."));
        return;
      }

      try {
        setError(null);
        await updateFraudAlertStatus(alertId, status);
        await loadResultsAndAnalytics();
      } catch (requestError) {
        console.error("Failed to update fraud alert:", requestError);
        setError(
          requestError instanceof Error
            ? requestError
            : new Error("Unable to update fraud alert status.")
        );
      }
    },
    [loadResultsAndAnalytics]
  );

  useEffect(() => {
    loadResultsAndAnalytics();
  }, [loadResultsAndAnalytics]);

  return (
    <main id="taxsaint-results-analytics">
      <header id="results-analytics-header">
        <div>
          <h1>Results &amp; Analytics</h1>
          <p>
            Review your tax results, financial position and potential financial alerts.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {taxResult && (
            <button
              type="button"
              onClick={() => setShowReportModal(true)}
              style={{
                backgroundColor: "#2563eb",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                padding: "10px 18px",
                fontWeight: "600",
                fontSize: "14px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                boxShadow: "0 2px 4px rgba(37, 99, 235, 0.3)",
              }}
            >
              <span>📄</span> Export / Print Tax PDF
            </button>
          )}

          <button
            type="button"
            onClick={loadResultsAndAnalytics}
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh Results"}
          </button>
        </div>
      </header>

      {error && (
        <div role="alert" aria-live="polite" className="error-banner">
          <strong>Unable to load all results</strong>
          <p>{error.message}</p>
        </div>
      )}

      <section id="results-analytics-tax">
        <TaxResult
          result={taxResult}
          loading={loading}
          error={error}
        />
      </section>

      <section id="results-analytics-summary">
        <FinancialSummary
          summary={financialSummary}
          loading={loading}
          error={error}
        />
      </section>

      <section id="results-analytics-chart">
        <AnalyticsChart
          data={analyticsData}
          loading={loading}
          error={error}
        />
      </section>

      <section id="results-analytics-fraud">
        <FraudAlerts
          alerts={fraudAlerts}
          loading={loading}
          error={error}
          onStatusChange={handleFraudAlertStatusChange}
        />
      </section>

      {showReportModal && (
        <TaxSummaryReport
          user={user}
          taxResult={taxResult}
          summary={financialSummary}
          alerts={fraudAlerts}
          onClose={() => setShowReportModal(false)}
        />
      )}
    </main>
  );
}

export default ResultsAnalytics;
