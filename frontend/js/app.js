// TAXSAINT FRONTEND APPLICATION

// 1. LOAD SAVED DATA
let incomes = JSON.parse(localStorage.getItem("taxsaint_incomes") || "[]");
let expenses = JSON.parse(localStorage.getItem("taxsaint_expenses") || "[]");
let bankTransactions = [];

// LOAD INCOME FROM DATABASE
async function loadIncomeFromBackend() {
    try {
        const result = await apiRequest(`/income?user_id=${USER_ID}`);

        incomes = result.income.map(item => ({
            income_id: item.income_id,
            source: item.source,
            party_name: item.party_name,
            amount: Number(item.amount),
            date: item.income_date
        }));

        updateApplication();

    } catch (error) {
        console.error("Unable to load income:", error);
        alert("Could not load income from database: " + error.message);
    }
}

// LOAD EXPENSES FROM DATABASE
async function loadExpensesFromBackend() {
    try {
        const result = await apiRequest(`/expenses?user_id=${USER_ID}`);

        expenses = result.expenses.map(item => ({
            expense_id: item.expense_id,
            category: item.category,
            party_name: item.party_name,
            amount: Number(item.amount),
            date: item.expense_date
        }));

        updateApplication();

    } catch (error) {
        console.error("Unable to load expenses:", error);
        alert("Could not load expenses: " + error.message);
    }
}

// LOAD BANK TRANSACTIONS FROM DATABASE
async function loadBankTransactionsFromBackend() {
    try {
        const data = await apiRequest(
            `/bank-transactions?user_id=${USER_ID}`
        );

        bankTransactions = data.bank_transactions || [];
        renderBankTransactions();

    } catch (error) {
        console.error("Error loading bank transactions:", error);
    }
}

// DISPLAY BANK TRANSACTIONS
function renderBankTransactions() {
    const bankList = document.getElementById("bank-list");
    const bankEmpty = document.getElementById("bank-empty");

    if (!bankList || !bankEmpty) return;

    bankList.innerHTML = "";

    if (bankTransactions.length === 0) {
        bankEmpty.style.display = "block";
        return;
    }

    bankEmpty.style.display = "none";

    bankTransactions.forEach(transaction => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${transaction.party_name}</td>
            <td>${transaction.transaction_type}</td>
            <td>₹${transaction.amount}</td>
            <td>${transaction.transaction_date}</td>
        `;

        bankList.appendChild(row);
    });
}

// ADD BANK TRANSACTION TO DATABASE
const bankForm = document.getElementById("bank-transaction-form");

if (bankForm) {
    bankForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const transaction = {
            user_id: USER_ID,
            party_name: document.getElementById("bank-party").value,
            transaction_type: document.getElementById("bank-type").value,
            amount: parseFloat(document.getElementById("bank-amount").value),
            transaction_date: document.getElementById("bank-date").value
        };

        try {
            await apiRequest("/bank-transactions", {
                method: "POST",
                body: JSON.stringify(transaction)
            });

            await loadBankTransactionsFromBackend();

            bankForm.reset();
            alert("Bank transaction added successfully!");

        } catch (error) {
            alert("Error: " + error.message);
        }
    });
}

// BACKEND API CONFIGURATION
const API_URL = "http://127.0.0.1:8000";
const USER_ID = 1;

// SEND REQUEST TO BACKEND
async function apiRequest(endpoint, options = {}) {
    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "API request failed");
    }

    return data;
}

// 2. SAVE DATA
function saveData() {
    localStorage.setItem("taxsaint_incomes", JSON.stringify(incomes));
    localStorage.setItem("taxsaint_expenses", JSON.stringify(expenses));
}

// 3. CURRENCY FORMAT
function formatMoney(amount) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2
    }).format(Number(amount) || 0);
}

// 4. NAVIGATION
const navLinks = document.querySelectorAll("#navigation a");
const pages = document.querySelectorAll(".page");

const pageTitles = {
    overview: "Good to see you.",
    income: "Your Income.",
    expenses: "Your Expenses.",
    tax: "Tax Planner.",
    shield: "SaintShield.",
    reports: "Your Reports."
};

function showPage(pageName) {
    pages.forEach(page => {
        page.hidden = page.id !== `page-${pageName}`;
    });

    navLinks.forEach(link => {
        link.classList.toggle("active", link.dataset.page === pageName);
    });

    const title = document.querySelector("#page-title");

    if (title) {
        title.textContent = pageTitles[pageName] || "TaxSaint";
    }
}

navLinks.forEach(link => {
    link.addEventListener("click", function(event) {
        event.preventDefault();
        showPage(this.dataset.page);
    });
});

// 5. TOTAL CALCULATION
function getTotal(items) {
    return items.reduce((total, item) => {
        return total + Number(item.amount || 0);
    }, 0);
}

// 6. UPDATE DASHBOARD
function updateDashboard() {
    const totalIncome = getTotal(incomes);
    const totalExpenses = getTotal(expenses);
    const balance = totalIncome - totalExpenses;

    const elements = {
        "total-income": totalIncome,
        "total-expenses": totalExpenses,
        "net-balance": balance,
        "cash-in": totalIncome,
        "cash-out": totalExpenses,
        "cash-balance": balance
    };

    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);

        if (element) {
            element.textContent = formatMoney(value);
        }
    });
}

// 7. DISPLAY INCOME
function renderIncome() {
    const list = document.getElementById("income-list");
    const empty = document.getElementById("income-empty");

    if (!list) return;

    list.innerHTML = "";

    if (empty) {
        empty.hidden = incomes.length !== 0;
    }

    incomes.forEach((item, index) => {
        const row = document.createElement("tr");

        const sourceCell = document.createElement("td");
        sourceCell.textContent = item.source;

        const amountCell = document.createElement("td");
        amountCell.textContent = formatMoney(item.amount);

        const dateCell = document.createElement("td");
        dateCell.textContent = item.date;

        const actionCell = document.createElement("td");
        const deleteButton = document.createElement("button");

        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-btn";

        deleteButton.addEventListener("click", function() {
            deleteIncome(index);
        });

        actionCell.appendChild(deleteButton);

        row.append(sourceCell, amountCell, dateCell, actionCell);
        list.appendChild(row);
    });
}

// 8. ADD INCOME - BACKEND INTEGRATION
const incomeForm = document.getElementById("income-form");

if (incomeForm) {
    incomeForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const source = document.getElementById("income-source").value.trim();
        const partyName = document.getElementById("income-party").value.trim();
        const amount = Number(document.getElementById("income-amount").value);
        const date = document.getElementById("income-date").value;

        if (!source || !partyName || amount <= 0 || !date) {
            alert("Please enter valid income details.");
            return;
        }

        try {
            const result = await apiRequest("/income", {
                method: "POST",
                body: JSON.stringify({
                    user_id: USER_ID,
                    source: source,
                    party_name: partyName,
                    amount: amount,
                    income_date: date
                })
            });

            incomes.push({
                income_id: result.income_id,
                source: source,
                party_name: partyName,
                amount: amount,
                date: date
            });

            saveData();
            updateApplication();
            incomeForm.reset();

            alert("Income saved successfully in database!");

        } catch (error) {
            console.error("Income save error:", error);
            alert("Unable to save income: " + error.message);
        }
    });
}

async function deleteIncome(index) {
    const item = incomes[index];

    if (!item || !item.income_id) {
        alert("Income ID not found. Please reload the records.");
        return;
    }

    if (!confirm("Are you sure you want to delete this income?")) {
        return;
    }

    try {
        await apiRequest(
            `/income/${item.income_id}?user_id=${USER_ID}`,
            { method: "DELETE" }
        );

        incomes.splice(index, 1);
        saveData();
        updateApplication();

        alert("Income deleted successfully!");

    } catch (error) {
        console.error("Delete income error:", error);
        alert("Unable to delete income: " + error.message);
    }
}

// 10. DISPLAY EXPENSES
function renderExpenses() {
    const list = document.getElementById("expense-list");
    const empty = document.getElementById("expense-empty");

    if (!list) return;

    list.innerHTML = "";

    if (empty) {
        empty.hidden = expenses.length !== 0;
    }

    expenses.forEach((item, index) => {
        const row = document.createElement("tr");

        const categoryCell = document.createElement("td");
        categoryCell.textContent = item.category;

        const amountCell = document.createElement("td");
        amountCell.textContent = formatMoney(item.amount);

        const dateCell = document.createElement("td");
        dateCell.textContent = item.date;

        const actionCell = document.createElement("td");
        const deleteButton = document.createElement("button");

        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-btn";

        deleteButton.addEventListener("click", function() {
            deleteExpense(index);
        });

        actionCell.appendChild(deleteButton);

        row.append(categoryCell, amountCell, dateCell, actionCell);
        list.appendChild(row);
    });
}

// 11. ADD EXPENSE - BACKEND INTEGRATION
const expenseForm = document.getElementById("expense-form");

if (expenseForm) {
    expenseForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const category = document.getElementById("expense-category").value.trim();
        const partyName = document.getElementById("expense-party").value.trim();
        const amount = Number(document.getElementById("expense-amount").value);
        const date = document.getElementById("expense-date").value;

        if (!category || !partyName || amount <= 0 || !date) {
            alert("Please enter valid expense details.");
            return;
        }

        try {
            const result = await apiRequest("/expenses", {
                method: "POST",
                body: JSON.stringify({
                    user_id: USER_ID,
                    category: category,
                    party_name: partyName,
                    amount: amount,
                    expense_date: date
                })
            });

            expenses.push({
                expense_id: result.expense_id,
                category: category,
                party_name: partyName,
                amount: amount,
                date: date
            });

            saveData();
            updateApplication();
            expenseForm.reset();

            alert("Expense saved successfully in database!");

        } catch (error) {
            console.error("Expense save error:", error);
            alert("Unable to save expense: " + error.message);
        }
    });
}

// DELETE EXPENSE - BACKEND INTEGRATION

async function deleteExpense(index) {
    const item = expenses[index];

    if (!item || !item.expense_id) {
        alert("Expense ID not found. Please reload the records.");
        return;
    }

    if (!confirm("Are you sure you want to delete this expense?")) {
        return;
    }

    try {
        await apiRequest(
            `/expenses/${item.expense_id}?user_id=${USER_ID}`,
            { method: "DELETE" }
        );

        expenses.splice(index, 1);
        saveData();
        updateApplication();

        alert("Expense deleted successfully!");

    } catch (error) {
        console.error("Delete expense error:", error);
        alert("Unable to delete expense: " + error.message);
    }
}

// 13. SAINTSHIELD - BASIC DUPLICATE CHECK
function renderFraudAlerts() {
    const container = document.getElementById("fraud-alerts");

    if (!container) return;

    container.innerHTML = "";

    const allEntries = [
        ...incomes.map(item => ({
            ...item,
            type: "Income",
            category: item.source
        })),
        ...expenses.map(item => ({
            ...item,
            type: "Expense"
        }))
    ];

    const seen = new Set();
    const duplicates = [];

    allEntries.forEach(item => {
        const key = `${item.type}-${item.amount}-${item.date}-${item.category}`;

        if (seen.has(key)) {
            duplicates.push(item);
        } else {
            seen.add(key);
        }
    });

    if (duplicates.length === 0) {
        const message = document.createElement("p");
        message.textContent = "No duplicate entries detected.";
        container.appendChild(message);
        return;
    }

    duplicates.forEach(item => {
        const alertBox = document.createElement("div");

        alertBox.className = "fraud-alert";
        alertBox.textContent =
            `Possible duplicate ${item.type}: ${item.category}, ${formatMoney(item.amount)}, ${item.date}`;

        container.appendChild(alertBox);
    });
}

// 14. TAX PLANNER - BACKEND INTEGRATION

const taxButton = document.getElementById("tax-calculate");

if (taxButton) {
    taxButton.addEventListener("click", async function () {

        const message = document.getElementById("tax-message");
        const year = document.getElementById("tax-year").value;

        taxButton.disabled = true;
        taxButton.textContent = "Calculating...";

        message.textContent = "Calculating tax using saved records...";

        try {
            const result = await apiRequest(
                `/tax/calculate?user_id=${USER_ID}&financial_year=${encodeURIComponent(year)}`,
                { method: "POST" }
            );

            const tax = result.tax;

            message.textContent =
                `Gross Income: ${formatMoney(tax.gross_income)} | ` +
                `Expenses: ${formatMoney(tax.expenses)} | ` +
                `Taxable Income: ${formatMoney(tax.taxable_income)} | ` +
                `Total Tax: ${formatMoney(tax.total_tax)}. ` +
                (result.notice || "");

        } catch (error) {
            console.error("Tax calculation error:", error);
            message.textContent = "Tax calculation failed: " + error.message;

        } finally {
            taxButton.disabled = false;
            taxButton.textContent = "Calculate Tax";
        }
    });
}
// 15. REPORTS
function updateReports() {
    const totalIncome = getTotal(incomes);
    const totalExpenses = getTotal(expenses);
    const balance = totalIncome - totalExpenses;

    const reportElements = {
        "report-income": formatMoney(totalIncome),
        "report-expenses": formatMoney(totalExpenses),
        "report-balance": formatMoney(balance),
        "report-income-count": incomes.length,
        "report-expense-count": expenses.length
    };

    Object.entries(reportElements).forEach(([id, value]) => {
        const element = document.getElementById(id);

        if (element) {
            element.textContent = value;
        }
    });
}

// 16. EXPORT REPORT AS CSV
const exportButton = document.getElementById("export-report");

if (exportButton) {
    exportButton.addEventListener("click", function() {
        const rows = [
            ["Type", "Category/Source", "Amount", "Date"]
        ];

        incomes.forEach(item => {
            rows.push(["Income", item.source, item.amount, item.date]);
        });

        expenses.forEach(item => {
            rows.push(["Expense", item.category, item.amount, item.date]);
        });

        const csv = rows.map(row => {
            return row.map(value => {
                return `"${String(value).replace(/"/g, '""')}"`;
            }).join(",");
        }).join("\n");

        const blob = new Blob([csv], {
            type: "text/csv;charset=utf-8;"
        });

        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = url;
        link.download = "TaxSaint_Report.csv";

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(url);
    });
}

// 17. UPDATE COMPLETE APPLICATION
function updateApplication() {
    updateDashboard();
    renderIncome();
    renderExpenses();
    renderFraudAlerts();
    updateReports();
}

// 18. INITIALIZE APPLICATION
showPage("overview");

async function initializeApplication() {
    await Promise.all([
        loadIncomeFromBackend(),
        loadExpensesFromBackend(),
        loadBankTransactionsFromBackend()
    ]);
}

initializeApplication();

console.log("TaxSaint frontend loaded successfully!");
// SAINTSHIELD - DUPLICATE EXPENSE SCAN

const scanButton = document.getElementById("scan-duplicates");

if (scanButton) {
    scanButton.addEventListener("click", async function () {

        const alertBox = document.getElementById("fraud-alerts");

        scanButton.disabled = true;
        scanButton.textContent = "Scanning...";
        alertBox.textContent = "Checking expenses for duplicates...";

        try {
            // Run duplicate expense scan
            await apiRequest(
                `/fraud/duplicate-expenses/scan?user_id=${USER_ID}`,
                { method: "POST" }
            );
            // Run income mismatch scan
await apiRequest(
    `/fraud/income-mismatches/scan?user_id=${USER_ID}`,
    { method: "POST" }
);

// Run expense mismatch scan
await apiRequest(
    `/fraud/expense-mismatches/scan?user_id=${USER_ID}`,
    { method: "POST" }
);
   



            // Fetch detected alerts
            const result = await apiRequest(
                `/fraud/alerts?user_id=${USER_ID}`
            );

            const alerts = Array.isArray(result)
                ? result
                : (result.alerts || []);

            if (alerts.length === 0) {
                alertBox.innerHTML = "<p>No fraud alerts found.</p>";
                return;
            }

   alertBox.innerHTML = alerts.map(alert => `
    <div class="alert-item">
        <h4>${alert.fraud_type || "Financial Alert"}</h4>

        <p>${alert.reason || "Please review this entry."}</p>

        <p>Transaction ID: ${alert.transaction_id ?? "N/A"}</p>

        <p>Status: ${alert.status || "PENDING"}</p>

        <button class="verify-alert" data-id="${alert.alert_id}">
            Verify
        </button>

        <button class="dismiss-alert" data-id="${alert.alert_id}">
            Dismiss
        </button>
    </div>
`).join("");
// Update fraud alert status

document.querySelectorAll(".verify-alert, .dismiss-alert")
    .forEach(button => {

        button.addEventListener("click", async function () {

            const alertId = this.dataset.id;

            const status = this.classList.contains("verify-alert")
                ? "VERIFIED"
                : "DISMISSED";

            try {
                await apiRequest(
                    `/fraud/alerts/${alertId}?user_id=${USER_ID}`,
                    {
                        method: "PATCH",
                        body: JSON.stringify({ status: status })
                    }
                );

                alert("Alert status updated successfully!");

                // Refresh alerts
                const result = await apiRequest(
                    `/fraud/alerts?user_id=${USER_ID}`
                );

                const updatedAlerts = result.alerts || [];

                // Refresh display
                alertBox.innerHTML = updatedAlerts.map(alert => `
                    <div class="alert-item">
                        <h4>${alert.fraud_type || "Financial Alert"}</h4>
                        <p>${alert.reason || "Please review this entry."}</p>
                        <p>Transaction ID: ${alert.transaction_id ?? "N/A"}</p>
                        <p>Status: ${alert.status || "PENDING"}</p>
                        <button class="verify-alert" data-id="${alert.alert_id}">Verify</button>
                        <button class="dismiss-alert" data-id="${alert.alert_id}">Dismiss</button>
                    </div>
                `).join("");

            } catch (error) {
                alert("Unable to update alert: " + error.message);
            }
        });
    });

        } catch (error) {
            console.error("Duplicate scan error:", error);
            alertBox.textContent = "Scan failed: " + error.message;

        } finally {
            scanButton.disabled = false;
            scanButton.textContent = "Scan Duplicate Expenses";
        }
    });
}