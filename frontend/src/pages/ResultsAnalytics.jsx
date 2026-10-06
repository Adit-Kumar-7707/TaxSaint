// TaxSaint results and analytics page

import React from "react";

import TaxResult from "../components/TaxResult";
import FinancialSummary from "../components/FinancialSummary";
import FraudAlerts from "../components/FraudAlerts";
import AnalyticsChart from "../components/AnalyticsChart";

// API service functions
import {
  getFinancialSummary,
  getTaxResult,
  getFraudAlerts,
  updateFraudAlertStatus
} from "../services/api";

// results and analytics page
function ResultsAnalytics({ user = null }) {
  // current user identifier
const userId = user?.id || null;

  // tax result state
  const [taxResult, setTaxResult] = React.useState(null);

  // financial summary state
  const [financialSummary, setFinancialSummary] = React.useState(null);

  // analytics data state
  const [analyticsData, setAnalyticsData] = React.useState(null);

  // fraud alerts state
  const [fraudAlerts, setFraudAlerts] = React.useState([]);

  // page loading state
  const [loading, setLoading] = React.useState(false);

  // page error state
  const [error, setError] = React.useState(null);


// load results and analytics
const loadResultsAndAnalytics = async () => {
  // start loading state
  setLoading(true);

  // clear previous error
  setError(null);

  try {
    // validate user identifier
    if (!userId) {
      throw new Error("User ID is required to load results.");
    }

    // request all results in parallel
    const [
      taxResponse,
      summaryResponse,
      fraudResponse
    ] = await Promise.all([
      getTaxResult(userId),
      getFinancialSummary(userId),
      getFraudAlerts(userId)
    ]);

    // store tax result
    setTaxResult(taxResponse);

    // store financial summary
    setFinancialSummary(summaryResponse);

    // build analytics data from financial summary
    setAnalyticsData({
      income: summaryResponse?.income ?? 0,
      expenses: summaryResponse?.expenses ?? 0
    });

    // store fraud alerts
    setFraudAlerts(
      Array.isArray(fraudResponse)
        ? fraudResponse
        : fraudResponse?.alerts || []
    );

  } catch (requestError) {

    // normalize request error
    const normalizedError =
      requestError instanceof Error
        ? requestError
        : new Error("Unable to load results and analytics.");

    // store error
    setError(normalizedError);

  } finally {

    // finish loading state
    setLoading(false);
  }
};

 // load page data when component mounts
React.useEffect(() => {
  // load results and analytics
  loadResultsAndAnalytics();
}, []);

  // results and analytics page layout
  return (
    <main id="taxsaint-results-analytics">

      {/* page header */}
      <header id="results-analytics-header">

        <h1>
          Results & Analytics
        </h1>

        <p>
          Review your tax results, financial position
          and potential financial alerts.
        </p>

      </header>

      {/* tax result */}
      <section id="results-analytics-tax">

        <TaxResult
          result={taxResult}
          loading={loading}
          error={error}
        />

      </section>

      {/* financial summary */}
      <section id="results-analytics-summary">

        <FinancialSummary
          summary={financialSummary}
          loading={loading}
          error={error}
        />

      </section>

      {/* financial analytics */}
      <section id="results-analytics-chart">

        <AnalyticsChart
          data={analyticsData}
          loading={loading}
          error={error}
        />

      </section>

      {/* fraud alerts */}
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

// export results and analytics page
export default ResultsAnalytics;
