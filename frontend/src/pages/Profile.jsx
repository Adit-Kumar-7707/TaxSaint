// TaxSaint profile page

import React, { useState } from "react";

import PageContainer from "../components/PageContainer.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import SuccessMessage from "../components/SuccessMessage.jsx";


// profile page component
function Profile({
  user = null,
  loading = false,
  error = null,
  successMessage = "",
  onSave,
  onRetry,
  onDismissSuccess
}) {

  // profile form data
  const [formData, setFormData] = useState({
    name: user?.name || "",
    email: user?.email || "",
    phone: user?.phone || "",
    userType: user?.userType || ""
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


  // handle profile submission
  const handleSubmit = (event) => {
    // prevent browser page reload
    event.preventDefault();

    // send updated profile data to parent
    if (typeof onSave === "function") {
      onSave(formData);
    }
  };


  // profile page layout
  return (
    <PageContainer
      title="Profile"
      subtitle="Manage your TaxSaint account information."
    >

      {/* loading state */}
      {loading && (
        <Loading message="Loading profile..." />
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


      {/* profile form */}
      <form
        id="taxsaint-profile-form"
        onSubmit={handleSubmit}
      >

        {/* name field */}
        <div className="form-field">
          <label htmlFor="profile-name">
            Full Name
          </label>

          <input
            id="profile-name"
            name="name"
            type="text"
            value={formData.name}
            onChange={handleChange}
          />
        </div>


        {/* email field */}
        <div className="form-field">
          <label htmlFor="profile-email">
            Email
          </label>

          <input
            id="profile-email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
          />
        </div>


        {/* phone field */}
        <div className="form-field">
          <label htmlFor="profile-phone">
            Phone Number
          </label>

          <input
            id="profile-phone"
            name="phone"
            type="tel"
            value={formData.phone}
            onChange={handleChange}
          />
        </div>


        {/* user type */}
        <div className="form-field">
          <label htmlFor="profile-user-type">
            User Type
          </label>

          <select
            id="profile-user-type"
            name="userType"
            value={formData.userType}
            onChange={handleChange}
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


        {/* save button */}
        <button
          type="submit"
          id="profile-save-button"
          disabled={loading}
        >
          {loading ? "Saving..." : "Save Changes"}
        </button>

      </form>

    </PageContainer>
  );
}


// export profile page
export default Profile;