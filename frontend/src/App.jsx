// TaxSaint main application

import React, { useState } from "react";

import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";
import Salaried from "./pages/Salaried";
import Business from "./pages/Business";

// results and analytics page
import ResultsAnalytics from "./pages/ResultsAnalytics";

// available application pages
const APP_PAGES = {
  DASHBOARD: "dashboard",
  PROFILE: "profile",
  SALARIED: "salaried",
  BUSINESS: "business",
  RESULTS_ANALYTICS: "results-analytics"
};


// main application component
function App() {

  // current active page
  const [currentPage, setCurrentPage] = useState(APP_PAGES.DASHBOARD);

  // current logged-in user
const [user, setUser] = useState(null);

  // change active page
  const handlePageChange = (page) => {
    setCurrentPage(page);
  };


  // render current page
  const renderPage = () => {

    switch (currentPage) {

      case APP_PAGES.PROFILE:
        return <div>Profile Page</div>;

      case APP_PAGES.SALARIED:
        return <div>Salaried Employee Page</div>;

      case APP_PAGES.BUSINESS:
        return <div>Business Owner Page</div>;

      case APP_PAGES.RESULTS_ANALYTICS:
         return <ResultsAnalytics user={user} />;
      case APP_PAGES.DASHBOARD:
      default:
        return <div>TaxSaint Dashboard</div>;
    }
  };


  // application layout
  return (
    <div id="taxsaint-app">

      {/* application header */}
      <header id="taxsaint-header">
        <h1>TaxSaint</h1>
      </header>


      {/* application navigation */}
      <nav id="taxsaint-navigation">

  <button
    type="button"
    onClick={() => handlePageChange(APP_PAGES.DASHBOARD)}
  >
    Dashboard
  </button>

  <button
    type="button"
    onClick={() => handlePageChange(APP_PAGES.PROFILE)}
  >
    Profile
  </button>

  <button
    type="button"
    onClick={() => handlePageChange(APP_PAGES.SALARIED)}
  >
    Salaried
  </button>

  <button
    type="button"
    onClick={() => handlePageChange(APP_PAGES.BUSINESS)}
  >
    Business
  </button>

  <button
    type="button"
    onClick={() =>
      handlePageChange(APP_PAGES.RESULTS_ANALYTICS)
    }
  >
    Results & Analytics
  </button>

</nav>


      {/* current application page */}
      <main id="taxsaint-content">
        {renderPage()}
      </main>

    </div>
  );
}


// export application
export default App;