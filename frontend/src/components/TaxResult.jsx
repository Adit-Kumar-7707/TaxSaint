// TaxSaint tax result component

import React from "react";


// tax result component
function TaxResult({
  result = null,
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
      id="tax-result-loading"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <p>Loading tax results...</p>
    </div>
  );
};
// render error state
const renderError = () => {
  // determine readable error message
  const errorMessage =
    error instanceof Error
      ? error.message
      : String(error || "Unable to load tax results.");

  // return error state
  return (
    <div
      id="tax-result-error"
      role="alert"
      aria-live="assertive"
    >
      <h3>Unable to load tax results</h3>

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
      id="tax-result-empty"
      role="status"
      aria-live="polite"
    >
      <h3>No Tax Result Available</h3>

      <p>
        Calculate your tax to view the income, taxable income,
        tax, cess and total tax.
      </p>
    </div>
  );
};


// render tax result
const renderResult = () => {
  // return tax result cards
  return (
    <div id="tax-result-grid">

      {/* total income */}
      <article className="tax-result-card">
        <span className="tax-result-label">
          Total Income
        </span>

        <strong className="tax-result-value">
          {formatCurrency(result.income)}
        </strong>
      </article>


      {/* total expenses */}
      <article className="tax-result-card">
        <span className="tax-result-label">
          Total Expenses
        </span>

        <strong className="tax-result-value">
          {formatCurrency(result.expenses)}
        </strong>
      </article>


      {/* taxable income */}
      <article className="tax-result-card">
        <span className="tax-result-label">
          Taxable Income
        </span>

        <strong className="tax-result-value">
          {formatCurrency(result.taxableIncome)}
        </strong>
      </article>


      {/* tax */}
      <article className="tax-result-card">
        <span className="tax-result-label">
          Tax
        </span>

        <strong className="tax-result-value">
          {formatCurrency(result.tax)}
        </strong>
      </article>


      {/* cess */}
      <article className="tax-result-card">
        <span className="tax-result-label">
          Cess
        </span>

        <strong className="tax-result-value">
          {formatCurrency(result.cess)}
        </strong>
      </article>


      {/* total tax */}
      <article
        className="tax-result-card tax-result-total"
      >
        <span className="tax-result-label">
          Total Tax
        </span>

        <strong className="tax-result-value">
          {formatCurrency(result.totalTax)}
        </strong>
      </article>

    </div>
  );
};


  // tax result component layout
  return (
    <section id="taxsaint-tax-result">

      {/* component heading */}
      <header id="tax-result-header">
        <h2>Tax Result</h2>

        <p>
          Summary of your calculated tax.
        </p>
      </header>


{/* component content */}
<div id="tax-result-content">

  {loading
    ? renderLoading()
    : error
      ? renderError()
      : !result
        ? renderEmpty()
        : renderResult()
  }

</div>

    </section>
  );
}


// export tax result component
export default TaxResult;