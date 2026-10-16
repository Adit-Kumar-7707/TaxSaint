// TaxSaint Results & Analytics Page
// Displays tax results, financial summaries, charts and fraud alerts.

import React, { useCallback, useEffect, useState } from "react";

import TaxResult from "../components/TaxResult";
import FinancialSummary from "../components/FinancialSummary";
import FraudAlerts from "../components/FraudAlerts";
import AnalyticsChart from "../components/AnalyticsChart";

import {
  getFinancialSummary,
  getTaxResult,
  getFraudAlerts,
  updateFraudAlertStatus,
} from "../services/api";

function ResultsAnalytics({ user = null }) {
  // Support both common user ID field names.
  const userId = user?.id ?? user?.user_id ?? null;

  const [taxResult, setTaxResult] = useState(null);
  const [financialSummary, setFinancialSummary] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [fraudAlerts, setFraudAlerts] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load tax results, financial summaries and fraud alerts.
  const loadResultsAndAnalytics = useCallback(async () => {
    // A missing user should not crash the page.
    if (userId === null || userId === undefined || userId === "") {
      setTaxResult(null);
      setFinancialSummary(null);
      setAnalyticsData(null);
      setFraudAlerts([]);
      setError(
        new Error(
          "No user is selected. Create or select a user to view financial results."
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

      // Accept common response names from the financial summary API.
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

      // Support either a direct array or an object containing alerts.
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

  // Update the status of a potential financial irregularity.
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

  // Reload data when the page opens or the user changes.
  useEffect(() => {
    loadResultsAndAnalytics();
  }, [loadResultsAndAnalytics]);

  return (
    <main id="taxsaint-results-analytics">
      <header id="results-analytics-header">
        <h1>Results &amp; Analytics</h1>

        <p>
          Review your tax results, financial position and potential
          financial alerts.
        </p>

        <button
          type="button"
          onClick={loadResultsAndAnalytics}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh Results"}
        </button>
      </header>

      {/* Display page-level errors without crashing the page. */}
      {error && (
        <div role="alert" aria-live="polite">
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
    </main>
  );
}

export default ResultsAnalytics;