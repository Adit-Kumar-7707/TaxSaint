// TaxSaint main application.
// Connects UI pages with FastAPI backend and computational engines.
import React, { useState, useEffect, useCallback } from "react";

// Components
import Navbar from "./components/Navbar.jsx";
import Sidebar from "./components/Sidebar.jsx";

// Pages
import Dashboard from "./pages/Dashboard.jsx";
import Profile from "./pages/Profile.jsx";
import Salaried from "./pages/Salaried.jsx";
import Business from "./pages/Business.jsx";
import ResultsAnalytics from "./pages/ResultsAnalytics.jsx";

// API Client Services
import {
  getUser,
  createUser,
  updateUser,
  createIncome,
  createExpense,
  calculateTax,
  getFinancialSummary,
  getTaxResult,
  getFraudAlerts,
  updateFraudAlertStatus,
  runFraudScan
} from "./services/api.js";

const APP_PAGES = {
  DASHBOARD: "dashboard",
  PROFILE: "profile",
  SALARIED: "salaried",
  BUSINESS: "business",
  RESULTS_ANALYTICS: "results-analytics",
};

function App() {
  const [currentPage, setCurrentPage] = useState(APP_PAGES.DASHBOARD);
  const [user, setUser] = useState(null);
  const [summary, setSummary] = useState(null);
  const [taxResult, setTaxResult] = useState(null);
  const [alerts, setAlerts] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");

  const handlePageChange = (page) => {
    setCurrentPage(page);
    setError(null);
    setSuccessMessage("");
  };

  const handleDismissSuccess = () => {
    setSuccessMessage("");
  };

  // Helper to execute asynchronous API actions with loading and error tracking
  const runAction = async (actionFn, successMsg = "") => {
    setLoading(true);
    setError(null);
    try {
      const result = await actionFn();
      if (successMsg) setSuccessMessage(successMsg);
      return result;
    } catch (err) {
      console.error("Action error:", err);
      setError(err instanceof Error ? err.message : String(err));
      return null;
    } finally {
      setLoading(false);
    }
  };

  // Refresh financial summary, latest tax result, and fraud alerts for active user
  const refreshUserData = useCallback(async (userId) => {
    if (!userId) return;
    try {
      const [sumRes, taxRes, alertRes] = await Promise.all([
        getFinancialSummary(userId).catch(() => null),
        getTaxResult(userId).catch(() => null),
        getFraudAlerts(userId).catch(() => ({ alerts: [] }))
      ]);

      setSummary(sumRes);
      setTaxResult(taxRes);
      const rawAlerts = Array.isArray(alertRes) ? alertRes : (alertRes?.alerts || []);
      setAlerts(rawAlerts);
    } catch (err) {
      console.warn("Could not load supplementary financial data:", err);
    }
  }, []);

  // Quick Persona Selector for live evaluation
  const handleSelectDemoUser = async (userId) => {
    const loadedUser = await runAction(
      () => getUser(userId),
      `Switched to demo persona: User ID ${userId}`
    );
    if (loadedUser) {
      setUser(loadedUser);
      await refreshUserData(loadedUser.id ?? loadedUser.user_id);
    }
  };

  // Save / Update profile in database
  const handleSaveProfile = async (profileData) => {
    const userId = user?.id ?? user?.user_id;
    if (userId) {
      const updated = await runAction(
        () => updateUser(userId, profileData),
        "Profile successfully updated in database."
      );
      if (updated) setUser(updated);
    } else {
      const created = await runAction(
        () => createUser(profileData),
        "Profile created successfully! You can now record transactions."
      );
      if (created) {
        setUser(created);
        await refreshUserData(created.id ?? created.user_id);
      }
    }
  };

  // Record income entry
  const handleIncomeSubmit = async (incomeData) => {
    const userId = user?.id ?? user?.user_id;
    if (!userId) {
      setError("Please select or create a profile first from the Profile page.");
      setCurrentPage(APP_PAGES.PROFILE);
      return;
    }
    const result = await runAction(
      () => createIncome({ ...incomeData, userId }),
      "Income transaction saved to database."
    );
    if (result) await refreshUserData(userId);
  };

  // Record expense entry
  const handleExpenseSubmit = async (expenseData) => {
    const userId = user?.id ?? user?.user_id;
    if (!userId) {
      setError("Please select or create a profile first from the Profile page.");
      setCurrentPage(APP_PAGES.PROFILE);
      return;
    }
    const result = await runAction(
      () => createExpense({ ...expenseData, userId }),
      "Expense transaction saved to database."
    );
    if (result) await refreshUserData(userId);
  };

  // Run C++ tax engine calculation
  const handleCalculateTax = async (taxData) => {
    const userId = user?.id ?? user?.user_id;
    if (!userId) {
      setError("Please select or create a profile first from the Profile page.");
      setCurrentPage(APP_PAGES.PROFILE);
      return;
    }
    const result = await runAction(
      () => calculateTax({ ...taxData, userId }),
      "Tax calculated using C++ progressive engine!"
    );
    if (result) {
      setTaxResult(result);
      setCurrentPage(APP_PAGES.RESULTS_ANALYTICS);
    }
  };

  // Run deterministic fraud anomaly scan
  const handleRunFraudCheck = async () => {
    const userId = user?.id ?? user?.user_id;
    if (!userId) {
      setError("Please select or create a profile first from the Profile page.");
      setCurrentPage(APP_PAGES.PROFILE);
      return;
    }
    const result = await runAction(
      () => runFraudScan(userId),
      "Transaction anomaly scan complete. Review potential issues in Results & Analytics."
    );
    if (result) await refreshUserData(userId);
  };

  // Handle alert status update
  const handleAlertStatusChange = async (alertId, newStatus) => {
    const updated = await runAction(
      () => updateFraudAlertStatus(alertId, newStatus),
      `Alert marked as ${newStatus}.`
    );
    if (updated) {
      const userId = user?.id ?? user?.user_id;
      if (userId) await refreshUserData(userId);
    }
  };

  // Callback when a statement is uploaded via CSV/Excel
  const handleUploadSuccess = async () => {
    setSuccessMessage("Statement processed and records imported into ledger!");
    const userId = user?.id ?? user?.user_id;
    if (userId) await refreshUserData(userId);
  };

  // Auto-attempt to load user ID 1 on startup if available
  useEffect(() => {
    getUser(1)
      .then((u) => {
        if (u) {
          setUser(u);
          refreshUserData(1);
        }
      })
      .catch(() => {
        // Normal if database not seeded yet
      });
  }, [refreshUserData]);

  const activeAlertsCount = alerts.filter(
    (a) => a.status === "NEEDS_VERIFICATION" || !a.status
  ).length;

  const renderPage = () => {
    const sharedProps = {
      user,
      loading,
      error,
      successMessage,
      onRetry: () => {
        const uid = user?.id ?? user?.user_id;
        if (uid) refreshUserData(uid);
      },
      onDismissSuccess: handleDismissSuccess
    };

    switch (currentPage) {
      case APP_PAGES.DASHBOARD:
        return (
          <Dashboard
            {...sharedProps}
            summary={summary}
            taxResult={taxResult}
            alerts={alerts}
            onNavigate={handlePageChange}
          />
        );

      case APP_PAGES.PROFILE:
        return (
          <Profile
            {...sharedProps}
            onSave={handleSaveProfile}
          />
        );

      case APP_PAGES.SALARIED:
        return (
          <Salaried
            {...sharedProps}
            taxResult={taxResult}
            onIncomeSubmit={handleIncomeSubmit}
            onCalculateTax={handleCalculateTax}
            onUploadSuccess={handleUploadSuccess}
          />
        );

      case APP_PAGES.BUSINESS:
        return (
          <Business
            {...sharedProps}
            taxResult={taxResult}
            alerts={alerts}
            onIncomeSubmit={handleIncomeSubmit}
            onExpenseSubmit={handleExpenseSubmit}
            onCalculateTax={handleCalculateTax}
            onRunFraudCheck={handleRunFraudCheck}
            onAlertStatusChange={handleAlertStatusChange}
            onUploadSuccess={handleUploadSuccess}
          />
        );

      case APP_PAGES.RESULTS_ANALYTICS:
        return (
          <ResultsAnalytics user={user} />
        );

      default:
        return (
          <Dashboard
            {...sharedProps}
            summary={summary}
            taxResult={taxResult}
            alerts={alerts}
            onNavigate={handlePageChange}
          />
        );
    }
  };

  return (
    <div id="taxsaint-app">
      <Navbar
        title="TaxSaint"
        user={user}
        onProfileClick={() => handlePageChange(APP_PAGES.PROFILE)}
        onSelectDemoUser={handleSelectDemoUser}
      />

      <div className="taxsaint-layout-body">
        <Sidebar
          currentPage={currentPage}
          onPageChange={handlePageChange}
          alertCount={activeAlertsCount}
        />

        <main id="taxsaint-content">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

export default App;