-- TaxSaint : database schema (New Tax Regime)
-- PostgreSQL / Supabase. Run in the Supabase SQL editor.


-- 1. Users
CREATE TABLE users (
    user_id      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    email        VARCHAR(100) UNIQUE NOT NULL,
    password     VARCHAR(255) NOT NULL,
    worker_type  VARCHAR(10) NOT NULL
                 CHECK (worker_type IN ('SALARIED', 'BUSINESS'))
);


-- 2. Income records
CREATE TABLE income (
    income_id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id      INT NOT NULL REFERENCES users(user_id),
    source       VARCHAR(50) NOT NULL,
    party_name   VARCHAR(100) NOT NULL,          -- payer: employer / client
    amount       DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    income_date  DATE NOT NULL
); -- income for tax and fraud


-- 3. Expense records
CREATE TABLE expenses (
    expense_id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id       INT NOT NULL REFERENCES users(user_id),
    category      VARCHAR(50) NOT NULL,
    party_name    VARCHAR(100) NOT NULL,
    amount        DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    expense_date  DATE NOT NULL
); -- expense for fraud


-- 4. Bank transactions
CREATE TABLE bank_transactions (
    transaction_id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id           INT NOT NULL REFERENCES users(user_id),
    party_name        VARCHAR(100),
    transaction_type  VARCHAR(10) NOT NULL
                      CHECK (transaction_type IN ('INCOME', 'EXPENSE')),
    amount            DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    transaction_date  DATE NOT NULL
); -- bank data source


-- 5. Tax slabs
CREATE TABLE tax_slabs (
    slab_id       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lower_limit   DECIMAL(12,2) NOT NULL,
    upper_limit   DECIMAL(12,2),                 -- NULL = no upper limit
    rate          DECIMAL(5,2) NOT NULL
); -- tax rule storage


-- 6. Tax calculation results
CREATE TABLE tax_results (
    result_id        INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id          INT NOT NULL REFERENCES users(user_id),
    gross_income     DECIMAL(12,2) NOT NULL,
    expenses         DECIMAL(12,2) NOT NULL,
    taxable_income   DECIMAL(12,2) NOT NULL,
    tax_before_cess  DECIMAL(12,2) NOT NULL,
    cess             DECIMAL(12,2) NOT NULL,
    total_tax        DECIMAL(12,2) NOT NULL,
    calculated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); -- calculator output


-- 7. Fraud alerts
-- transaction_id / matched_transaction_id can point to expenses, income
-- or bank_transactions, so the *_source column says which table.
CREATE TABLE fraud_alerts (
    alert_id                INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id                 INT NOT NULL REFERENCES users(user_id),
    fraud_type              VARCHAR(20) NOT NULL
                            CHECK (fraud_type IN ('DUPLICATE_EXPENSE', 'INCOME_MISMATCH')),
    transaction_source      VARCHAR(10) NOT NULL
                            CHECK (transaction_source IN ('EXPENSE', 'INCOME', 'BANK')),
    transaction_id          INT NOT NULL,
    matched_source          VARCHAR(10)
                            CHECK (matched_source IN ('EXPENSE', 'INCOME', 'BANK')),
    matched_transaction_id  INT,
    difference_amount       DECIMAL(12,2),
    reason                  VARCHAR(255) NOT NULL,
    status                  VARCHAR(20) DEFAULT 'NEEDS_VERIFICATION'
                            CHECK (status IN ('NEEDS_VERIFICATION', 'VERIFIED', 'DISMISSED')),
    detected_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (fraud_type, transaction_source, transaction_id)   -- re-runs don't duplicate alerts
); -- fraud result storage


-- New regime slabs, FY 2026-27
INSERT INTO tax_slabs
(lower_limit, upper_limit, rate)
VALUES
(0,       400000,  0),
(400000,  800000,  5),
(800000,  1200000, 10),
(1200000, 1600000, 15),
(1600000, 2000000, 20),
(2000000, 2400000, 25),
(2400000, NULL,    30); -- initial tax slabs
