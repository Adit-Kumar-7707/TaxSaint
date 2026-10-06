// TaxSaint analytics chart component

import React from "react";

// analytics chart component
function AnalyticsChart({
  data = null,
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
      id="analytics-chart-loading"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <p>Loading financial analytics...</p>
    </div>
  );
};

// render error state
const renderError = () => {
  // determine readable error message
  const errorMessage =
    error instanceof Error
      ? error.message
      : String(error || "Unable to load financial analytics.");

  // return error state
  return (
    <div
      id="analytics-chart-error"
      role="alert"
      aria-live="assertive"
    >
      <h3>Unable to load financial analytics</h3>

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
      id="analytics-chart-empty"
      role="status"
      aria-live="polite"
    >
      <h3>No Analytics Available</h3>

      <p>
        Add income and expense data to view your financial analytics.
      </p>
    </div>
  );
};

// render chart
const renderChart = () => {
  // read income value
  const income = Number(data.income) || 0;

  // read expense value
  const expenses = Number(data.expenses) || 0;

  // determine largest value for proportional bars
  const maximumValue = Math.max(income, expenses, 1);

  // calculate income bar width
  const incomeWidth = (income / maximumValue) * 100;

  // calculate expense bar width
  const expenseWidth = (expenses / maximumValue) * 100;

  // return financial comparison chart
  return (
    <div id="financial-analytics-chart">

      {/* income */}
      <div className="analytics-chart-row">

        <div className="analytics-chart-label">
          <span>Income</span>

          <strong>
            {formatCurrency(income)}
          </strong>
        </div>

        <div className="analytics-chart-track">
          <div
            className="analytics-chart-bar analytics-chart-income"
            style={{
              width: `${incomeWidth}%`
            }}
          />
        </div>

      </div>

      {/* expenses */}
      <div className="analytics-chart-row">

        <div className="analytics-chart-label">
          <span>Expenses</span>

          <strong>
            {formatCurrency(expenses)}
          </strong>
        </div>

        <div className="analytics-chart-track">
          <div
            className="analytics-chart-bar analytics-chart-expenses"
            style={{
              width: `${expenseWidth}%`
            }}
          />
        </div>

      </div>

    </div>
  );
};

  // analytics chart component layout
  return (
    <section id="taxsaint-analytics-chart">

      {/* component heading */}
      <header id="analytics-chart-header">
        <h2>Financial Analytics</h2>

        <p>
          Visual comparison of your income and expenses.
        </p>
      </header>

{/* component content */}
<div id="analytics-chart-content">

  {loading
    ? renderLoading()
    : error
      ? renderError()
      : !data
        ? renderEmpty()
        : renderChart()
  }

</div>

    </section>
  );
}

// export analytics chart component
export default AnalyticsChart;