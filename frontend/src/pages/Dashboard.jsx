// TaxSaint dashboard page

import React from "react";

import PageContainer from "../components/PageContainer.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import SuccessMessage from "../components/SuccessMessage.jsx";


// dashboard page component
function Dashboard({
  user = null,
  summary = null,
  loading = false,
  error = null,
  successMessage = "",
  onRetry,
  onDismissSuccess,
  onNavigate
}) {

  // handle navigation
  const handleNavigation = (page) => {
    // call parent navigation
    if (typeof onNavigate === "function") {
      onNavigate(page);
    }
  };


  // dashboard content
  return (
    <PageContainer
      title="Dashboard"
      subtitle="Overview of your tax and financial information."
    >

      {/* loading state */}
      {loading && (
        <Loading message="Loading dashboard..." />
      )}


      {/* error state */}
      {error && (
        <ErrorMessage
          message={error}
          onRetry={onRetry}
        />
      )}


      {/* success state */}
      {successMessage && (
        <SuccessMessage
          message={successMessage}
          onDismiss={onDismissSuccess}
        />
      )}


      {/* user overview */}
      <section id="dashboard-user-overview">
        <h2>Welcome</h2>

        {user ? (
          <>
            <p>
              Welcome, {user.name || "User"}.
            </p>

            {user.userType && (
              <p>
                Account Type: {user.userType}
              </p>
            )}
          </>
        ) : (
          <p>
            No user information is available.
          </p>
        )}
      </section>


      {/* financial summary */}
      <section id="dashboard-financial-summary">
        <h2>Financial Summary</h2>

        {summary ? (
          <div>
            <p>
              Total Income: ₹
              {Number(summary.totalIncome || 0).toLocaleString("en-IN")}
            </p>

            <p>
              Total Expenses: ₹
              {Number(summary.totalExpenses || 0).toLocaleString("en-IN")}
            </p>

            <p>
              Net Income: ₹
              {Number(summary.netIncome || 0).toLocaleString("en-IN")}
            </p>
          </div>
        ) : (
          <p>
            Financial summary is not available yet.
          </p>
        )}
      </section>


      {/* tax summary */}
      <section id="dashboard-tax-summary">
        <h2>Tax Summary</h2>

        {summary?.tax ? (
          <div>
            <p>
              Taxable Income: ₹
              {Number(summary.tax.taxableIncome || 0).toLocaleString("en-IN")}
            </p>

            <p>
              Estimated Tax: ₹
              {Number(summary.tax.taxAmount || 0).toLocaleString("en-IN")}
            </p>
          </div>
        ) : (
          <p>
            Calculate your tax to view your tax summary.
          </p>
        )}
      </section>


      {/* alerts */}
      <section id="dashboard-alerts">
        <h2>Alerts</h2>

        {summary?.alerts?.length > 0 ? (
          <ul>
            {summary.alerts.map((alert, index) => (
              <li key={alert.id || index}>
                {alert.message || "Financial alert requires attention."}
              </li>
            ))}
          </ul>
        ) : (
          <p>
            No financial alerts at the moment.
          </p>
        )}
      </section>


      {/* workflow navigation */}
      <section id="dashboard-actions">
        <h2>Continue</h2>

        <button
          type="button"
          onClick={() => handleNavigation("salaried")}
        >
          Salaried Employee
        </button>

        <button
          type="button"
          onClick={() => handleNavigation("business")}
        >
          Business Owner
        </button>
      </section>

    </PageContainer>
  );
}


// export dashboard page
export default Dashboard;