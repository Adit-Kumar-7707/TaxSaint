// TaxSaint API service
// Connects React UI components to the FastAPI backend.

// Backend base URL
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const AUTH_TOKEN_KEY = "taxsaint_auth_token";

// --- Token Management Helpers ---

function getStoredToken() {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  } catch {
    return null;
  }
}

function setStoredToken(token) {
  try {
    if (token) {
      localStorage.setItem(AUTH_TOKEN_KEY, token);
    } else {
      localStorage.removeItem(AUTH_TOKEN_KEY);
    }
  } catch {
    // LocalStorage might be disabled in privacy modes
  }
}

function clearStoredToken() {
  try {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  } catch {
    // ignore
  }
}

// Build standard request headers with optional Bearer token
function getAuthHeaders(additionalHeaders = {}) {
  const headers = {
    Accept: "application/json",
    ...additionalHeaders,
  };
  const token = getStoredToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// Build API endpoint URL
function buildUrl(endpoint) {
  const baseUrl = API_BASE_URL.replace(/\/$/, "");
  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${baseUrl}${path}`;
}

// Handle API response
async function handleResponse(response) {
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredToken();
    }
    const message =
      data?.detail ||
      data?.message ||
      `Request failed with status ${response.status}.`;
    throw new Error(message);
  }

  return data;
}

// --- Base HTTP Methods ---

async function getRequest(endpoint) {
  const response = await fetch(buildUrl(endpoint), {
    method: "GET",
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}

async function postRequest(endpoint, data) {
  const response = await fetch(buildUrl(endpoint), {
    method: "POST",
    headers: getAuthHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify(data),
  });
  return handleResponse(response);
}

async function putRequest(endpoint, data) {
  const response = await fetch(buildUrl(endpoint), {
    method: "PUT",
    headers: getAuthHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify(data),
  });
  return handleResponse(response);
}

async function deleteRequest(endpoint) {
  const response = await fetch(buildUrl(endpoint), {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}

// --- Authentication & User Endpoints ---

async function loginUser(credentials) {
  const data = await postRequest("/api/users/login", credentials);
  if (data?.access_token) {
    setStoredToken(data.access_token);
  }
  return data;
}

async function getCurrentUser() {
  return getRequest("/api/users/me");
}

function logoutUser() {
  clearStoredToken();
}

async function getUser(userId) {
  return getRequest(`/api/users/${userId}`);
}

async function createUser(userData) {
  const data = await postRequest("/api/users", userData);
  if (data?.access_token) {
    setStoredToken(data.access_token);
  }
  return data;
}

async function updateUser(userId, userData) {
  return putRequest(`/api/users/${userId}`, userData);
}

// --- Financial Endpoints ---

async function createIncome(incomeData) {
  return postRequest("/api/financial/income", incomeData);
}

async function createExpense(expenseData) {
  return postRequest("/api/financial/expenses", expenseData);
}

async function getFinancialSummary(userId) {
  return getRequest(`/api/financial/summary/${userId}`);
}

async function getIncomeList(userId) {
  return getRequest(`/api/financial/income/${userId}`);
}

async function getExpenseList(userId) {
  return getRequest(`/api/financial/expenses/${userId}`);
}

// Upload CSV, Excel or PDF statement file
async function uploadStatement(userId, file) {
  const formData = new FormData();
  formData.append("user_id", userId);
  formData.append("file", file);

  const response = await fetch(buildUrl("/api/financial/upload"), {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });

  return handleResponse(response);
}

// --- Tax Endpoints ---

async function calculateTax(taxData) {
  return postRequest("/api/tax/calculate", taxData);
}

async function getTaxResult(userId) {
  return getRequest(`/api/tax/result/${userId}`);
}

// --- Fraud & Anomaly Endpoints ---

async function getFraudAlerts(userId) {
  return getRequest(`/api/fraud/alerts/${userId}`);
}

async function updateFraudAlertStatus(alertId, status) {
  return putRequest(`/api/fraud/alerts/${alertId}/status`, { status });
}

async function runFraudScan(userId) {
  return postRequest(`/api/fraud/scan/${userId}`, {});
}

export {
  getStoredToken,
  setStoredToken,
  clearStoredToken,
  loginUser,
  getCurrentUser,
  logoutUser,
  getUser,
  createUser,
  updateUser,
  createIncome,
  createExpense,
  getFinancialSummary,
  getIncomeList,
  getExpenseList,
  uploadStatement,
  calculateTax,
  getTaxResult,
  getFraudAlerts,
  updateFraudAlertStatus,
  runFraudScan,
};
