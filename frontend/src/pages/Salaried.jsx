// TaxSaint salaried employee page

import React, { useState } from "react";

import PageContainer from "../components/PageContainer.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import SuccessMessage from "../components/SuccessMessage.jsx";

import IncomeForm from "../components/forms/IncomeForm.jsx";


// salaried employee page component
function Salaried({
  user = null,
  taxResult = null,
  loading = false,
  error = null,
  successMessage = "",
  onIncomeSubmit,
  onCalculateTax,
  onRetry,
  onDismissSuccess
}) {

  // salaried financial data
  const [financialData, setFinancialData] = useState({
    salary: "",
    deductions: "",
    otherIncome: ""
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


  // handle tax calculation
  const handleTaxCalculation = (event) => {
    // prevent browser page reload
    event.preventDefault();

    // prepare tax calculation data
    const taxData = {
      userId: user?.id || null,
      userType: "salaried",
      salary: Number(financialData.salary) || 0,
      deductions: Number(financialData.deductions) || 0,
      otherIncome: Number(financialData.otherIncome) || 0
    };

    // send tax data to parent
    if (typeof onCalculateTax === "function") {
      onCalculateTax(taxData);
    }
  };


  // salaried employee page layout
  return (
    <PageContainer
      title="Salaried Employee"
      subtitle="Manage your salary, deductions and tax calculation."
    >

      {/* loading state */}
      {loading && (
        <Loading message="Processing financial information..." />
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


      {/* salary information */}
      <section id="salaried-financial-information">

        <h2>Financial Information</h2>

        {/* salary */}
        <div className="form-field">
          <label htmlFor="salaried-salary">
            Annual Salary
          </label>

          <input
            id="salaried-salary"
            name="salary"
            type="number"
            value={financialData.salary}
            onChange={handleChange}
            placeholder="Enter annual salary"
            min="0"
            step="0.01"
          />
        </div>


        {/* deductions */}
        <div className="form-field">
          <label htmlFor="salaried-deductions">
            Deductions
          </label>

          <input
            id="salaried-deductions"
            name="deductions"
            type="number"
            value={financialData.deductions}
            onChange={handleChange}
            placeholder="Enter eligible deductions"
            min="0"
            step="0.01"
          />
        </div>


        {/* other income */}
        <div className="form-field">
          <label htmlFor="salaried-other-income">
            Other Income
          </label>

          <input
            id="salaried-other-income"
            name="otherIncome"
            type="number"
            value={financialData.otherIncome}
            onChange={handleChange}
            placeholder="Enter other income"
            min="0"
            step="0.01"
          />
        </div>

      </section>


      {/* income entry */}
      <section id="salaried-income-entry">

        <IncomeForm
          onSubmit={handleIncomeSubmit}
          loading={loading}
        />

      </section>


      {/* tax calculation */}
      <section id="salaried-tax-calculation">

        <h2>Tax Calculation</h2>

        <form onSubmit={handleTaxCalculation}>

          <button
            type="submit"
            id="salaried-calculate-tax"
            disabled={loading}
          >
            Calculate Tax
          </button>

        </form>

      </section>


      {/* tax result */}
      <section id="salaried-tax-result">

        <h2>Tax Result</h2>

        {taxResult ? (
          <div id="salaried-tax-result-content">

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
            Enter your financial information and calculate your tax.
          </p>
        )}

      </section>

    </PageContainer>
  );
}


// export salaried page
export default Salaried;