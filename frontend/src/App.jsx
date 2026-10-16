// TaxSaint main application: connects the page components to the FastAPI backend.
import React, { useCallback, useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import Profile from "./pages/Profile.jsx";
import Salaried from "./pages/Salaried.jsx";
import Business from "./pages/Business.jsx";
import ResultsAnalytics from "./pages/ResultsAnalytics.jsx";
import {
  calculateTax,
  createExpense,
  createIncome,
  createUser,
  getFinancialSummary,
  getFraudAlerts,
  getTaxResult,
  getUser,
  runFraudScan,
  updateUser,
} from "./services/api.js";

const APP_PAGES = {
  DASHBOARD: "dashboard",
  PROFILE: "profile",
  SALARIED: "salaried",
  BUSINESS: "business",
  RESULTS_ANALYTICS: "results-analytics",
};
const STORAGE_KEY = "taxsaint.user";

function readStoredUser() {
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "null");
  } catch {
    return null;
  }
}

function App() {
  const [currentPage, setCurrentPage] = useState(APP_PAGES.DASHBOARD);
  const [user, setUser] = useState(readStoredUser);
  const [summary, setSummary] = useState(null);
  const [taxResult, setTaxResult] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const saveUserLocally = (nextUser) => {
    setUser(nextUser);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser));
  };

  const refreshFinancialData = useCallback(async (userId) => {
    if (!userId) return;
    const [nextSummary, nextTaxResult, nextFraudResponse] = await Promise.all([
      getFinancialSummary(userId),
      getTaxResult(userId),
      getFraudAlerts(userId),
    ]);
    setSummary(nextSummary);
    setTaxResult(nextTaxResult);
    setAlerts(Array.isArray(nextFraudResponse) ? nextFraudResponse : (nextFraudResponse?.alerts || []));
  }, []);

  // Rehydrate the stored profile and fetch persisted results when the app opens.
  useEffect(() => {
    let cancelled = false;
    async function loadUser() {
      if (!user?.id) return;
      try {
        const savedUser = await getUser(user.id);
        if (cancelled) return;
        saveUserLocally(savedUser);
        await refreshFinancialData(savedUser.id);
      } catch (requestError) {
        if (!cancelled) setError(requestError instanceof Error ? requestError.message : "Unable to load saved user data.");
      }
    }
    loadUser();
    return () => { cancelled = true; };
    // Only the saved user ID controls this initial hydration.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, refreshFinancialData]);

  const runAction = async (action, successText) => {
    setLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      const result = await action();
      if (user?.id) await refreshFinancialData(user.id);
      if (successText) setSuccessMessage(successText);
      return result;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The request could not be completed.");
      return null;
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async (profileData) => {
    const saved = await runAction(
      () => user?.id ? updateUser(user.id, profileData) : createUser(profileData),
      user?.id ? "Profile updated successfully." : "Your TaxSaint profile has been created."
    );
    if (saved) {
      saveUserLocally(saved);
      setCurrentPage(saved.userType === "business" ? APP_PAGES.BUSINESS : APP_PAGES.SALARIED);
      await refreshFinancialData(saved.id);
    }
  };

  const handleIncomeSubmit = async (incomeData) => {
    if (!user?.id) {
      setError("Create your profile first from the Profile page.");
      setCurrentPage(APP_PAGES.PROFILE);
      return;
    }
    const result = await runAction(() => createIncome({ ...incomeData, userId: user.id }), "Income saved successfully.");
    if (result) await refreshFinancialData(user.id);
  };

  const handleExpenseSubmit = async (expenseData) => {
    if (!user?.id) {
      setError("Create your profile first from the Profile page.");
      setCurrentPage(APP_PAGES.PROFILE);
      return;
    }
    const result = await runAction(() => createExpense({ ...expenseData, userId: user.id }), "Expense saved successfully.");
    if (result) await refreshFinancialData(user.id);
  };

  const handleCalculateTax = async (taxData) => {
    if (!user?.id) {
      setError("Create your profile first from the Profile page.");
      setCurrentPage(APP_PAGES.PROFILE);
      return;
    }
    const result = await runAction(() => calculateTax({ ...taxData, userId: user.id }), "Tax calculation completed.");
    if (result) {
      setTaxResult(result);
      setCurrentPage(APP_PAGES.RESULTS_ANALYTICS);
    }
  };

  const handleRunFraudCheck = async () => {
    if (!user?.id) {
      setError("Create your profile first from the Profile page.");
      setCurrentPage(APP_PAGES.PROFILE);
      return;
    }
    const result = await runAction(() => runFraudScan(user.id), "Transaction scan completed. Alerts are potential issues requiring review.");
    if (result) await refreshFinancialData(user.id);
  };

  const handleRetry = () => user?.id ? runAction(() => refreshFinancialData(user.id), "") : setCurrentPage(APP_PAGES.PROFILE);
  const dismissSuccess = () => setSuccessMessage("");
  const navigate = (page) => setCurrentPage(page);

  const dashboardSummary = summary ? {
    ...summary,
    totalIncome: summary.income,
    totalExpenses: summary.expenses,
    netIncome: summary.netPosition,
    tax: taxResult ? { taxableIncome: taxResult.taxableIncome, taxAmount: taxResult.totalTax } : null,
    alerts,
  } : null;

  const renderPage = () => {
    const shared = { loading, error, successMessage, onRetry: handleRetry, onDismissSuccess: dismissSuccess };
    switch (currentPage) {
      case APP_PAGES.PROFILE:
        return <Profile {...shared} user={user} onSave={handleSaveProfile} />;
      case APP_PAGES.SALARIED:
        return <Salaried {...shared} user={user} taxResult={taxResult} onIncomeSubmit={handleIncomeSubmit} onCalculateTax={handleCalculateTax} />;
      case APP_PAGES.BUSINESS:
        return <Business {...shared} user={user} taxResult={taxResult} alerts={alerts} onIncomeSubmit={handleIncomeSubmit} onExpenseSubmit={handleExpenseSubmit} onCalculateTax={handleCalculateTax} onRunFraudCheck={handleRunFraudCheck} />;
      case APP_PAGES.RESULTS_ANALYTICS:
        return user ? <ResultsAnalytics user={user} /> : <Profile {...shared} user={user} onSave={handleSaveProfile} />;
      case APP_PAGES.DASHBOARD:
      default:
        return <Dashboard {...shared} user={user} summary={dashboardSummary} onNavigate={navigate} />;
    }
  };

  return (
    <div id="taxsaint-app">
      <header id="taxsaint-header"><h1>TaxSaint</h1></header>
      <nav id="taxsaint-navigation" aria-label="Main navigation">
        <button type="button" onClick={() => navigate(APP_PAGES.DASHBOARD)}>Dashboard</button>
        <button type="button" onClick={() => navigate(APP_PAGES.PROFILE)}>Profile</button>
        <button type="button" onClick={() => navigate(APP_PAGES.SALARIED)}>Salaried</button>
        <button type="button" onClick={() => navigate(APP_PAGES.BUSINESS)}>Business</button>
        <button type="button" onClick={() => navigate(APP_PAGES.RESULTS_ANALYTICS)}>Results &amp; Analytics</button>
      </nav>
      {error && <div role="alert" id="taxsaint-global-error">{error}</div>}
      <main id="taxsaint-content">{renderPage()}</main>
    </div>
  );
}

export default App;
