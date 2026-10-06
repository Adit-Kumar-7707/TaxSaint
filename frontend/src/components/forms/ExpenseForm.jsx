// TaxSaint expense information form

import React, { useState } from "react";


// expense form component
function ExpenseForm({
  initialData = {},
  onSubmit,
  loading = false
}) {

  // expense form data
  const [formData, setFormData] = useState({
    partyName: initialData.partyName || "",
    category: initialData.category || "",
    amount: initialData.amount || "",
    expenseDate: initialData.expenseDate || "",
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


  // expense form layout
  return (
    <form
      id="taxsaint-expense-form"
      onSubmit={handleSubmit}
    >

      {/* form heading */}
      <div id="expense-form-header">
        <h2>Expense Information</h2>
        <p>
          Enter your expense details.
        </p>
      </div>


      {/* party name */}
      <div className="form-field">
        <label htmlFor="expense-party-name">
          Party Name
        </label>

        <input
          id="expense-party-name"
          name="partyName"
          type="text"
          value={formData.partyName}
          onChange={handleChange}
          placeholder="Enter party or vendor name"
        />
      </div>


      {/* expense category */}
      <div className="form-field">
        <label htmlFor="expense-category">
          Category
        </label>

        <input
          id="expense-category"
          name="category"
          type="text"
          value={formData.category}
          onChange={handleChange}
          placeholder="Rent, supplies, travel, etc."
        />
      </div>


      {/* expense amount */}
      <div className="form-field">
        <label htmlFor="expense-amount">
          Amount
        </label>

        <input
          id="expense-amount"
          name="amount"
          type="number"
          value={formData.amount}
          onChange={handleChange}
          placeholder="Enter expense amount"
          min="0"
          step="0.01"
        />
      </div>


      {/* expense date */}
      <div className="form-field">
        <label htmlFor="expense-date">
          Expense Date
        </label>

        <input
          id="expense-date"
          name="expenseDate"
          type="date"
          value={formData.expenseDate}
          onChange={handleChange}
        />
      </div>


      {/* expense description */}
      <div className="form-field">
        <label htmlFor="expense-description">
          Description
        </label>

        <textarea
          id="expense-description"
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
        id="expense-form-submit"
        disabled={loading}
      >
        {loading ? "Saving..." : "Add Expense"}
      </button>

    </form>
  );
}


// export expense form
export default ExpenseForm;