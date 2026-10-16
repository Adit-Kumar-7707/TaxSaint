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

## Run the project locally

### 1. Backend API

Python 3.10+ and a C++ compiler (`g++`) are required. The tax engine is compiled by the API when the first tax calculation is requested.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn integration.api.main:app --reload
```

The API runs at `http://localhost:8000`; interactive API documentation is at `http://localhost:8000/docs`. If `DATABASE_URL` is not set, development uses a local SQLite database (`taxsaint.db`).

### 2. Supabase PostgreSQL

1. Copy `.env.example` to `.env` and set `DATABASE_URL` to your Supabase PostgreSQL connection string. Do not commit `.env` or share its credentials.
2. If the Supabase tables already exist, run `database_manager/schema/migration_backend.sql` in the Supabase SQL Editor. If setting up a new database from scratch, run `database_manager/schema/data.sql` instead.
3. Start the API with `uvicorn integration.api.main:app --reload --env-file .env`.

The backend is the only layer that connects to the database. The React frontend must call the API and must not contain database credentials.

### 3. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local` with:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

Then run:

```bash
npm run dev
```

### 4. Tests

From the project root:

```bash
python -m compileall -q database_manager integration tax_calculation data_input
pytest -q
```

The API integration test uses an isolated temporary SQLite database. Tax calculations use the existing C++ engine; financial anomaly alerts are potential issues that must be reviewed, not automatic findings of fraud.

## Current prototype boundaries

- The API supports user profile CRUD, income/expense/bank transaction entry, financial summaries, persisted tax results, and potential anomaly alerts.
- The tax engine uses the tax settings and slabs stored in the database. The current engine applies the salaried standard deduction and configured rebate/cess; the separate `deductions` UI field is not yet applied as a tax deduction.
- Authentication and authorization are not implemented. Do not deploy this prototype with real personal or financial data until access controls and production security have been added.
