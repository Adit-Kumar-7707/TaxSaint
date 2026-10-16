// TaxSaint profile page
import React, { useState, useEffect } from "react";
import PageContainer from "../components/PageContainer.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import SuccessMessage from "../components/SuccessMessage.jsx";

function Profile({
  user = null,
  loading = false,
  error = null,
  successMessage = "",
  onSave,
  onRetry,
  onDismissSuccess
}) {
  const [formData, setFormData] = useState({
    name: user?.name || "",
    email: user?.email || "",
    phone: user?.phone || "",
    userType: user?.worker_type?.toLowerCase() || user?.userType || "salaried"
  });

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || "",
        email: user.email || "",
        phone: user.phone || "",
        userType: user.worker_type?.toLowerCase() || user.userType || "salaried"
      });
    }
  }, [user]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((previous) => ({
      ...previous,
      [name]: value
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (typeof onSave === "function") {
      onSave(formData);
    }
  };

  return (
    <PageContainer
      title="User Profile & Regime Settings"
      subtitle="Configure your tax profile, contact information, and filing classification."
    >
      {loading && <Loading message="Saving profile to database..." />}
      {error && <ErrorMessage message={error} onRetry={onRetry} />}
      {successMessage && <SuccessMessage message={successMessage} onDismiss={onDismissSuccess} />}

      <div className="content-card" style={{ maxWidth: "650px" }}>
        <h3>Account & Taxpayer Details</h3>
        <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", marginBottom: "1.5rem" }}>
          Profile data links all financial entries, tax calculations, and fraud scans.
        </p>

        <form id="taxsaint-profile-form" onSubmit={handleSubmit}>
          <div className="form-field" style={{ marginBottom: "1.25rem" }}>
            <label htmlFor="profile-name">Full Name</label>
            <input
              id="profile-name"
              name="name"
              type="text"
              value={formData.name}
              onChange={handleChange}
              placeholder="e.g. Rahul Sharma"
              required
            />
          </div>

          <div className="form-field" style={{ marginBottom: "1.25rem" }}>
            <label htmlFor="profile-email">Email Address</label>
            <input
              id="profile-email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="e.g. rahul.sharma@example.com"
              required
            />
          </div>

          <div className="form-field" style={{ marginBottom: "1.25rem" }}>
            <label htmlFor="profile-phone">Phone Number</label>
            <input
              id="profile-phone"
              name="phone"
              type="tel"
              value={formData.phone}
              onChange={handleChange}
              placeholder="e.g. 9876543210"
            />
          </div>

          <div className="form-field" style={{ marginBottom: "1.75rem" }}>
            <label htmlFor="profile-user-type">Worker / Filing Classification</label>
            <select
              id="profile-user-type"
              name="userType"
              value={formData.userType}
              onChange={handleChange}
              required
            >
              <option value="salaried">Salaried Employee (Standard ₹75k Deduction)</option>
              <option value="business">Business Owner (Deductible Operating Expenses)</option>
            </select>
          </div>

          <button
            type="submit"
            id="profile-save-button"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? "Saving Profile..." : "Save Profile & Sync Database"}
          </button>
        </form>
      </div>
    </PageContainer>
  );
}

export default Profile;