// TaxSaint income information form

import React, { useState } from "react";


// income form component
function IncomeForm({
  initialData = {},
  onSubmit,
  loading = false
}) {

  // income form data
  const [formData, setFormData] = useState({
    source: initialData.source || "",
    amount: initialData.amount || "",
    incomeDate: initialData.incomeDate || "",
    description: initialData.description || ""
  });


  // handle input changes
  const handleChange = (event) => {
    // get changed field
    const { name, value } = event.target;

    // update form data
    setFormData((previousData) => ({
      ...previousData,
      [name]: value
    }));
  };


  // handle form submission
  const handleSubmit = (event) => {
    // prevent browser page reload
    event.preventDefault();

    // submit form data to parent
    if (typeof onSubmit === "function") {
      onSubmit(formData);
    }
  };


  // income form layout
  return (
    <form
      id="taxsaint-income-form"
      onSubmit={handleSubmit}
    >

      {/* form heading */}
      <div id="income-form-header">
        <h2>Income Information</h2>
        <p>
          Enter your income details.
        </p>
      </div>


      {/* income source */}
      <div className="form-field">
        <label htmlFor="income-source">
          Income Source
        </label>

        <input
          id="income-source"
          name="source"
          type="text"
          value={formData.source}
          onChange={handleChange}
          placeholder="Salary, business, freelance, etc."
        />
      </div>


      {/* income amount */}
      <div className="form-field">
        <label htmlFor="income-amount">
          Amount
        </label>

        <input
          id="income-amount"
          name="amount"
          type="number"
          value={formData.amount}
          onChange={handleChange}
          placeholder="Enter income amount"
          min="0"
          step="0.01"
        />
      </div>


      {/* income date */}
      <div className="form-field">
        <label htmlFor="income-date">
          Income Date
        </label>

        <input
          id="income-date"
          name="incomeDate"
          type="date"
          value={formData.incomeDate}
          onChange={handleChange}
        />
      </div>


      {/* income description */}
      <div className="form-field">
        <label htmlFor="income-description">
          Description
        </label>

        <textarea
          id="income-description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          placeholder="Optional description"
          rows="4"
        />
      </div>


      {/* submit button */}
      <button
        type="submit"
        id="income-form-submit"
        disabled={loading}
      >
        {loading ? "Saving..." : "Add Income"}
      </button>

    </form>
  );
}


// export income form
export default IncomeForm;