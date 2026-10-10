# data_input — CSV/Excel Transaction Import (Deliverable 2)

> **Status:** Skeleton only (Step 1). Functions are not implemented yet.

## Purpose

Imports income, expense, and bank transaction records from CSV and Excel
files, validates them, and sends valid records to the TaxSaint FastAPI backend.

## Pipeline

```
CSV / Excel
    ↓
Pandas Importer
    ↓
Column Validation
    ↓
Row Validation
    ↓
Convert to TaxSaint Internal Format
    ↓
Send through FastAPI
    ↓
Supabase PostgreSQL
    ↓
Fraud Engine / Dashboard
```

## Structure

```
data_input/
├── README.md
└── importers/
    ├── csv_importer.py     # CSV reading + shared import pipeline
    └── excel_importer.py   # Excel reading; reuses the shared pipeline
```

## Supported record types

| Type             | Expected columns                             |
|------------------|----------------------------------------------|
| Income           | `source`, `amount`, `date`                   |
| Expense          | `category`, `party_name`, `amount`, `date`   |
| Bank transaction | `party_name`, `transaction_type` (`INCOME`/`EXPENSE`), `amount`, `date` |

Bank transaction columns follow `database_manager/schema/data.sql`. Every
imported record also needs a `user_id`, which is passed to the importer
(it is not a CSV column). Column names will be re-checked against the FastAPI
request schema once the backend owner provides it.

## Scope

This module is responsible for **data import only**. It does not perform tax
calculation, fraud detection, or dashboard logic, and it never connects to
Supabase directly. Valid records are sent through the FastAPI backend.

## Usage

TODO: Add command-line and programmatic usage examples after Step 2.

## Open items

- Final FastAPI request schema (owned by the backend team member)
- How `user_id` reaches the API (parameter vs. authenticated session)
- Final bank transaction field names
- Accepted date formats
- Duplicate-import strategy
