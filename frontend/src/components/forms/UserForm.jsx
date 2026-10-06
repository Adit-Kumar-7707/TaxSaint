// TaxSaint user information form

import React, { useState } from "react";


// user form component
function UserForm({
  initialData = {},
  onSubmit,
  loading = false
}) {

  // user form data
  const [formData, setFormData] = useState({
    name: initialData.name || "",
    email: initialData.email || "",
    phone: initialData.phone || "",
    userType: initialData.userType || ""
  });


  // handle input changes
  const handleChange = (event) => {

    const {
      name,
      value
    } = event.target;

    setFormData((currentData) => ({
      ...currentData,
      [name]: value
    }));
  };


  // handle form submission
  const handleSubmit = (event) => {

    event.preventDefault();

    if (typeof onSubmit !== "function") {
      return;
    }

    onSubmit(formData);
  };


  // user form layout
  return (
    <form
      id="taxsaint-user-form"
      onSubmit={handleSubmit}
    >

      {/* form heading */}
      <div id="user-form-header">
        <h2>User Information</h2>

        <p>
          Enter your basic information to continue.
        </p>
      </div>


      {/* name field */}
      <div className="form-field">

        <label htmlFor="user-name">
          Full Name
        </label>

        <input
          id="user-name"
          name="name"
          type="text"
          value={formData.name}
          onChange={handleChange}
          placeholder="Enter your full name"
          required
        />

      </div>


      {/* email field */}
      <div className="form-field">

        <label htmlFor="user-email">
          Email
        </label>

        <input
          id="user-email"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="Enter your email"
          required
        />

      </div>


      {/* phone field */}
      <div className="form-field">

        <label htmlFor="user-phone">
          Phone Number
        </label>

        <input
          id="user-phone"
          name="phone"
          type="tel"
          value={formData.phone}
          onChange={handleChange}
          placeholder="Enter your phone number"
          required
        />

      </div>


      {/* user type field */}
      <div className="form-field">

        <label htmlFor="user-type">
          User Type
        </label>

        <select
          id="user-type"
          name="userType"
          value={formData.userType}
          onChange={handleChange}
          required
        >

          <option value="">
            Select user type
          </option>

          <option value="salaried">
            Salaried Employee
          </option>

          <option value="business">
            Business Owner
          </option>

        </select>

      </div>


      {/* submit button */}
      <button
        type="submit"
        id="user-form-submit"
        disabled={loading}
      >
        {loading ? "Saving..." : "Continue"}
      </button>

    </form>
  );
}


// export user form
export default UserForm;