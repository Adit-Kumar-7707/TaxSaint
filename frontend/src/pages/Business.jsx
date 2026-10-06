// TaxSaint business owner page

import React, { useState } from "react";

import PageContainer from "../components/PageContainer.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import SuccessMessage from "../components/SuccessMessage.jsx";

import IncomeForm from "../components/forms/IncomeForm.jsx";
import ExpenseForm from "../components/forms/ExpenseForm.jsx";


// business owner page component
function Business({
  user = null,
  taxResult = null,
  alerts = [],
  loading = false,
  error = null,
  successMessage = "",
  onIncomeSubmit,
  onExpenseSubmit,
  onCalculateTax,
  onRunFraudCheck,
  onRetry,
  onDismissSuccess
}) {

  // business financial data
  const [financialData, setFinancialData] = useState({
    businessIncome: "",
    businessExpenses: "",
    deductions: ""
  });


  // handle financial data changes
  const handleChange = (event) => {
    // get changed field
    const { name, value } = event.target;

    // update financial data
    setFinancialData((previousData) => ({
      ...previousData,
      [name]: value
    }));
  };


  // handle income submission
  const handleIncomeSubmit = (incomeData) => {
    // submit income data to parent
    if (typeof onIncomeSubmit === "function") {
      onIncomeSubmit(incomeData);
    }
  };


  // handle expense submission
  const handleExpenseSubmit = (expenseData) => {
    // submit expense data to parent
    if (typeof onExpenseSubmit === "function") {
      onExpenseSubmit(expenseData);
    }
  };


  // handle tax calculation
  const handleTaxCalculation = (event) => {
    // prevent browser page reload
    event.preventDefault();

    // prepare tax calculation data
    const taxData = {
      userId: user?.id || null,
      userType: "business",
      businessIncome: Number(financialData.businessIncome) || 0,
      businessExpenses: Number(financialData.businessExpenses) || 0,
      deductions: Number(financialData.deductions) || 0
    };

    // send tax data to parent
    if (typeof onCalculateTax === "function") {
      onCalculateTax(taxData);
    }
  };


  // handle fraud check
  const handleFraudCheck = () => {
    // run fraud detection through parent
    if (typeof onRunFraudCheck === "function") {
      onRunFraudCheck({
        userId: user?.id || null
      });
    }
  };


  // business owner page layout
  return (
    <PageContainer
      title="Business Owner"
      subtitle="Manage business finances, tax and financial alerts."
    >

      {/* loading state */}
      {loading && (
        <Loading message="Processing business information..." />
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


      {/* business financial information */}
      <section id="business-financial-information">

        <h2>Business Financial Information</h2>

        {/* business income */}
        <div className="form-field">
          <label htmlFor="business-income">
            Business Income
          </label>

          <input
            id="business-income"
            name="businessIncome"
            type="number"
            value={financialData.businessIncome}
            onChange={handleChange}
            placeholder="Enter business income"
            min="0"
            step="0.01"
          />
        </div>


        {/* business expenses */}
        <div className="form-field">
          <label htmlFor="business-expenses">
            Business Expenses
          </label>

          <input
            id="business-expenses"
            name="businessExpenses"
            type="number"
            value={financialData.businessExpenses}
            onChange={handleChange}
            placeholder="Enter business expenses"
            min="0"
            step="0.01"
          />
        </div>


        {/* deductions */}
        <div className="form-field">
          <label htmlFor="business-deductions">
            Deductions
          </label>

          <input
            id="business-deductions"
            name="deductions"
            type="number"
            value={financialData.deductions}
            onChange={handleChange}
            placeholder="Enter eligible deductions"
            min="0"
            step="0.01"
          />
        </div>

      </section>


      {/* income entry */}
      <section id="business-income-entry">

        <IncomeForm
          onSubmit={handleIncomeSubmit}
          loading={loading}
        />

      </section>


      {/* expense entry */}
      <section id="business-expense-entry">

        <ExpenseForm
          onSubmit={handleExpenseSubmit}
          loading={loading}
        />

      </section>


      {/* tax calculation */}
      <section id="business-tax-calculation">

        <h2>Tax Calculation</h2>

        <form onSubmit={handleTaxCalculation}>

          <button
            type="submit"
            id="business-calculate-tax"
            disabled={loading}
          >
            Calculate Tax
          </button>

        </form>

      </section>


      {/* fraud detection */}
      <section id="business-fraud-detection">

        <h2>Financial Verification</h2>

        <p>
          Check business transactions for potential financial
          irregularities.
        </p>

        <button
          type="button"
          id="business-fraud-check"
          onClick={handleFraudCheck}
          disabled={loading}
        >
          Check Transactions
        </button>

      </section>


      {/* tax result */}
      <section id="business-tax-result">

        <h2>Tax Result</h2>

        {taxResult ? (
          <div id="business-tax-result-content">

            <p>
              Taxable Income: ₹
              {Number(
                taxResult.taxableIncome || 0
              ).toLocaleString("en-IN")}
            </p>

            <p>
              Estimated Tax: ₹
              {Number(
                taxResult.taxAmount || 0
              ).toLocaleString("en-IN")}
            </p>

          </div>
        ) : (
          <p>
            Enter your business financial information and
            calculate your tax.
          </p>
        )}

      </section>


      {/* fraud alerts */}
      <section id="business-fraud-alerts">

        <h2>Financial Alerts</h2>

        {alerts.length > 0 ? (
          <ul>
            {alerts.map((alert, index) => (
              <li key={alert.id || index}>
                <strong>
                  {alert.alertType || "Financial Alert"}:
                </strong>{" "}
                {alert.message ||
                  "Potential financial irregularity requires verification."}
              </li>
            ))}
          </ul>
        ) : (
          <p>
            No financial alerts at the moment.
          </p>
        )}

      </section>

    </PageContainer>
  );
}


// export business page
export default Business;