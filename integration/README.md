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
