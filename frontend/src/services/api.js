// TaxSaint API service


// backend base URL
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";


// build API endpoint
function buildUrl(endpoint) {

  // remove duplicate slashes
  const baseUrl = API_BASE_URL.replace(/\/$/, "");
  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;

  return `${baseUrl}${path}`;
}


// handle API response
async function handleResponse(response) {

  // read response body
  const data = await response.json().catch(() => null);


  // handle failed response
  if (!response.ok) {

    const message =
      data?.detail ||
      data?.message ||
      `Request failed with status ${response.status}.`;

    throw new Error(message);
  }


  // return successful response
  return data;
}


// perform GET request
async function getRequest(endpoint) {

  // send GET request
  const response = await fetch(buildUrl(endpoint), {
    method: "GET",
    headers: {
      Accept: "application/json"
    }
  });


  // process response
  return handleResponse(response);
}


// perform POST request
async function postRequest(endpoint, data) {

  // send POST request
  const response = await fetch(buildUrl(endpoint), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json"
    },
    body: JSON.stringify(data)
  });


  // process response
  return handleResponse(response);
}


// perform PUT request
async function putRequest(endpoint, data) {

  // send PUT request
  const response = await fetch(buildUrl(endpoint), {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json"
    },
    body: JSON.stringify(data)
  });


  // process response
  return handleResponse(response);
}


// perform DELETE request
async function deleteRequest(endpoint) {

  // send DELETE request
  const response = await fetch(buildUrl(endpoint), {
    method: "DELETE",
    headers: {
      Accept: "application/json"
    }
  });


  // process response
  return handleResponse(response);
}


// user API
async function getUser(userId) {
  // endpoint implementation comes later
  return getRequest(`/api/users/${userId}`);
}


async function createUser(userData) {
  // endpoint implementation comes later
  return postRequest("/api/users", userData);
}


// income API
async function createIncome(incomeData) {
  // endpoint implementation comes later
  return postRequest("/api/financial/income", incomeData);
}


// expense API
async function createExpense(expenseData) {
  // endpoint implementation comes later
  return postRequest("/api/financial/expenses", expenseData);
}


// tax API
async function calculateTax(taxData) {
  // endpoint implementation comes later
  return postRequest("/api/tax/calculate", taxData);
}

// financial summary API
async function getFinancialSummary(userId) {
  // request financial summary
  return getRequest(`/api/financial/summary/${userId}`);
}

// tax result API
async function getTaxResult(userId) {
  // request latest tax result
  return getRequest(`/api/tax/result/${userId}`);
}

// fraud alerts API
async function getFraudAlerts(userId) {
  // request fraud alerts
  return getRequest(`/api/fraud/alerts/${userId}`);
}

// update fraud alert status API
async function updateFraudAlertStatus(alertId, status) {
  // update fraud alert status
  return putRequest(`/api/fraud/alerts/${alertId}/status`, {
    status
  });
}

// export API service
export {
  getUser,
  createUser,
  createIncome,
  createExpense,
  calculateTax,
  getFinancialSummary,
  getTaxResult,
  getFraudAlerts,
  updateFraudAlertStatus
};