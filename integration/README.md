# Integration API

The integration layer connects the TaxSaint frontend with the tax calculation,
fraud detection, and database modules.

## Structure

```text
integration/
├── api/
│   ├── main.py
│   ├── routes/
│   │   ├── financial.py
│   │   ├── fraud.py
│   │   ├── tax.py
│   │   └── users.py
│   └── schemas/
│       └── requests.py
└── README.md
```

## Modules

- `api/main.py`: API application entry point.
- `api/routes/users.py`: User-related routes.
- `api/routes/tax.py`: Tax calculation routes.
- `api/routes/financial.py`: Income and expense routes.
- `api/routes/fraud.py`: Fraud detection and alert routes.
- `api/schemas/requests.py`: Shared request schemas.

The API modules are currently scaffolded and ready for route and schema
implementations.

## Run the API

From the repository root, install the dependencies from `requirements.txt` and run:

```bash
uvicorn integration.api.main:app --reload
```

The default development database is SQLite. Set `DATABASE_URL` to a Supabase PostgreSQL connection string for PostgreSQL, and apply `database_manager/schema/migration_backend.sql` if the original tables already exist. The API docs are available at `/docs`.

The route modules now provide user/profile operations, income/expense/bank transaction entry, financial summaries, tax calculations through the C++ engine, and potential anomaly-alert review. Alerts are not confirmed findings of fraud.
