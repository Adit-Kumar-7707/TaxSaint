// TAXSAINT FRONTEND APPLICATION

// 1. LOAD SAVED DATA
let incomes = JSON.parse(localStorage.getItem("taxsaint_incomes") || "[]");
let expenses = JSON.parse(localStorage.getItem("taxsaint_expenses") || "[]");

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

// 8. ADD INCOME
const incomeForm = document.getElementById("income-form");

if (incomeForm) {
    incomeForm.addEventListener("submit", function(event) {
        event.preventDefault();

        const source = document.getElementById("income-source").value.trim();
        const amount = Number(document.getElementById("income-amount").value);
        const date = document.getElementById("income-date").value;

        if (!source || amount <= 0 || !date) {
            alert("Please enter valid income details.");
            return;
        }

        incomes.push({
            source: source,
            amount: amount,
            date: date
        });

        saveData();
        updateApplication();
        incomeForm.reset();

        alert("Income added successfully!");
    });
}

// 9. DELETE INCOME
function deleteIncome(index) {
    if (confirm("Are you sure you want to delete this income?")) {
        incomes.splice(index, 1);
        saveData();
        updateApplication();
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

// 11. ADD EXPENSE
const expenseForm = document.getElementById("expense-form");

if (expenseForm) {
    expenseForm.addEventListener("submit", function(event) {
        event.preventDefault();

        const category = document.getElementById("expense-category").value.trim();
        const amount = Number(document.getElementById("expense-amount").value);
        const date = document.getElementById("expense-date").value;

        if (!category || amount <= 0 || !date) {
            alert("Please enter valid expense details.");
            return;
        }

        expenses.push({
            category: category,
            amount: amount,
            date: date
        });

        saveData();
        updateApplication();
        expenseForm.reset();

        alert("Expense added successfully!");
    });
}

// 12. DELETE EXPENSE
function deleteExpense(index) {
    if (confirm("Are you sure you want to delete this expense?")) {
        expenses.splice(index, 1);
        saveData();
        updateApplication();
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

// 14. TAX PLANNER
const taxButton = document.getElementById("tax-calculate");

if (taxButton) {
    taxButton.addEventListener("click", function() {
        const incomeInput = document.getElementById("tax-income");
        const expenseInput = document.getElementById("tax-expenses");
        const message = document.getElementById("tax-message");

        if (!incomeInput || !expenseInput || !message) return;

        const income = Number(incomeInput.value);
        const expenseAmount = Number(expenseInput.value);

        if (
            incomeInput.value === "" ||
            expenseInput.value === "" ||
            income < 0 ||
            expenseAmount < 0
        ) {
            message.textContent = "Please enter valid amounts.";
            return;
        }

        const taxableIncome = Math.max(0, income - expenseAmount);

        message.textContent =
            `Estimated taxable income: ${formatMoney(taxableIncome)}. Connect the tax calculation engine for an actual tax estimate.`;
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
updateApplication();
showPage("overview");

console.log("TaxSaint frontend loaded successfully!");