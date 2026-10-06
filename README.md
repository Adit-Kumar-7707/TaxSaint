# TaxSaint

TaxSaint is organized into tax calculation, data input, database management, frontend, and integration layers.


https://github.com/Adit-Kumar-7707/TaxSaint.git

File Structure
```text
TaxSaint/
├── .gitignore
├── README.md
├── requirements.txt
│
├── data_input/
│   ├── README.md
│   └── importers/
│       ├── csv_importer.py
│       └── excel_importer.py
│
├── database_manager/
│   ├── README.md
│   ├── connection.py
│   ├── models/
│   │   ├── bank_transaction.py
│   │   ├── expense.py
│   │   ├── fraud_alert.py
│   │   ├── income.py
│   │   └── user.py
│   ├── repositories/
│   │   ├── financial_repository.py
│   │   ├── fraud_repository.py
│   │   └── user_repository.py
│   └── schema/
│       └── data.sql
│
├── frontend/
│   ├── README.md
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── dist/
│   │   ├── index.html
│   │   └── assets/
│   │       └── index-OsF9brEX.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/
│       │   ├── AnalyticsChart.jsx
│       │   ├── ErrorMessage.jsx
│       │   ├── FinancialSummary.jsx
│       │   ├── FraudAlerts.jsx
│       │   ├── Loading.jsx
│       │   ├── Navbar.jsx
│       │   ├── PageContainer.jsx
│       │   ├── Sidebar.jsx
│       │   ├── SuccessMessage.jsx
│       │   ├── TaxResult.jsx
│       │   └── forms/
│       │       ├── ExpenseForm.jsx
│       │       ├── IncomeForm.jsx
│       │       └── UserForm.jsx
│       ├── hooks/
│       │   └── useApi.js
│       ├── pages/
│       │   ├── Business.jsx
│       │   ├── Dashboard.jsx
│       │   ├── Profile.jsx
│       │   ├── ResultsAnalytics.jsx
│       │   └── Salaried.jsx
│       └── services/
│           └── api.js
│
├── integration/
│   ├── README.md
│   └── api/
│       ├── main.py
│       ├── routes/
│       │   ├── financial.py
│       │   ├── fraud.py
│       │   ├── tax.py
│       │   └── users.py
│       └── schemas/
│           └── requests.py
│
├── tax_calculation/
│   ├── fraud_engine/
│   │   ├── README.md
│   │   ├── fraud_detector.py
│   │   └── rules.py
│   ├── tax_engine/
│   │   ├── README.md
│   │   ├── calculatetax.cpp
│   │   └── calculatetax.h
│   └── tests/
│       ├── test_fraud.py
│       └── test_tax.py
│
└── tests/
    └── integration/
        └── .gitkeep
