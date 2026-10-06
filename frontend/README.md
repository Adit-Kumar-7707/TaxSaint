# TaxSaint Frontend

## Overview

The TaxSaint frontend is the React-based user interface for the TaxSaint financial assistance platform.

It provides separate workflows for:

- Salaried employees
- Business owners

The frontend collects financial information, displays tax results, displays financial alerts, and communicates with the FastAPI backend through REST APIs.

The frontend does not connect directly to the Supabase database.

---

## Technology Stack

- React 19
- Vite
- JavaScript
- REST API
- FastAPI backend
- Supabase PostgreSQL through the backend

---

## Project Structure

```text
TaxSaint/
├── .gitignore
├── README.md
├── requirements.txt
│
├── data_input/
│   ├── README.md
│   ├── forms/
│   │   ├── ExpenseForm.jsx
│   │   ├── IncomeForm.jsx
│   │   └── UserForm.jsx
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
│   │       └── index-CS-zHLpy.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/
│       │   ├── ErrorMessage.jsx
│       │   ├── Loading.jsx
│       │   ├── Navbar.jsx
│       │   ├── PageContainer.jsx
│       │   ├── Sidebar.jsx
│       │   └── SuccessMessage.jsx
│       ├── hooks/
│       │   └── useApi.js
│       ├── pages/
│       │   ├── Business.jsx
│       │   ├── Dashboard.jsx
│       │   ├── Profile.jsx
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