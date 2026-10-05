-- TaxSaint : database schema (New Tax Regime)

CREATE DATABASE IF NOT EXISTS taxsaint;

USE taxsaint;


-- 1. Users
CREATE TABLE users (
    user_id      INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    email        VARCHAR(100) UNIQUE NOT NULL,
    password     VARCHAR(255) NOT NULL,
    worker_type  ENUM('SALARIED', 'BUSINESS') NOT NULL
);


-- 2. Income records
CREATE TABLE income (
    income_id    INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    source       VARCHAR(50) NOT NULL,
    amount       DECIMAL(12,2) NOT NULL,
    income_date  DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
); -- income for tax


-- 3. Expense records
CREATE TABLE expenses (
    expense_id    INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    category      VARCHAR(50) NOT NULL,
    party_name    VARCHAR(100) NOT NULL,
    amount        DECIMAL(12,2) NOT NULL,
    expense_date  DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
); -- expense for fraud


-- 4. Bank transactions
CREATE TABLE bank_transactions (
    transaction_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    party_name      VARCHAR(100),
    transaction_type ENUM('INCOME', 'EXPENSE') NOT NULL,
    amount          DECIMAL(12,2) NOT NULL,
    transaction_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
); -- bank data source


-- 5. Tax slabs
CREATE TABLE tax_slabs (
    slab_id       INT AUTO_INCREMENT PRIMARY KEY,
    lower_limit   DECIMAL(12,2) NOT NULL,
    upper_limit   DECIMAL(12,2),
    rate          DECIMAL(5,2) NOT NULL
); -- tax rule storage


-- 6. Tax calculation results
CREATE TABLE tax_results (
    result_id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL,
    gross_income     DECIMAL(12,2) NOT NULL,
    expenses         DECIMAL(12,2) NOT NULL,
    taxable_income   DECIMAL(12,2) NOT NULL,
    tax_before_cess  DECIMAL(12,2) NOT NULL,
    cess              DECIMAL(12,2) NOT NULL,
    total_tax         DECIMAL(12,2) NOT NULL,
    calculated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
); -- calculator output


-- 7. Fraud alerts
CREATE TABLE fraud_alerts (
    alert_id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id               INT NOT NULL,
    fraud_type             ENUM(
        'DUPLICATE_EXPENSE',
        'INCOME_MISMATCH'
    ) NOT NULL,
    transaction_id         INT,
    matched_transaction_id INT,
    difference_amount      DECIMAL(12,2),
    reason                 VARCHAR(255) NOT NULL,
    status                 ENUM(
        'NEEDS_VERIFICATION',
        'VERIFIED',
        'DISMISSED'
    ) DEFAULT 'NEEDS_VERIFICATION',
    detected_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (transaction_id)
        REFERENCES bank_transactions(transaction_id),
    FOREIGN KEY (matched_transaction_id)
        REFERENCES bank_transactions(transaction_id)
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