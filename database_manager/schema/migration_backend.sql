-- Apply this migration in Supabase SQL Editor if the original TaxSaint tables
-- already exist. It adds fields/tables required by the implemented API.
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE users ALTER COLUMN password DROP NOT NULL;

CREATE TABLE IF NOT EXISTS tax_settings (
    id INT PRIMARY KEY,
    financial_year VARCHAR(10) NOT NULL,
    standard_deduction DECIMAL(12,2) NOT NULL,
    rebate_limit DECIMAL(12,2) NOT NULL,
    cess_rate DECIMAL(5,2) NOT NULL
);
INSERT INTO tax_settings (id, financial_year, standard_deduction, rebate_limit, cess_rate)
VALUES (1, '2026-27', 75000, 1200000, 4)
ON CONFLICT (id) DO NOTHING;

-- If tax_slabs is empty, seed the FY 2026-27 rules used by this prototype.
INSERT INTO tax_slabs (lower_limit, upper_limit, rate)
SELECT seed.lower_limit, seed.upper_limit, seed.rate
FROM (VALUES
    (0::numeric, 400000::numeric, 0::numeric),
    (400000::numeric, 800000::numeric, 5::numeric),
    (800000::numeric, 1200000::numeric, 10::numeric),
    (1200000::numeric, 1600000::numeric, 15::numeric),
    (1600000::numeric, 2000000::numeric, 20::numeric),
    (2000000::numeric, 2400000::numeric, 25::numeric),
    (2400000::numeric, NULL::numeric, 30::numeric)
) AS seed(lower_limit, upper_limit, rate)
WHERE NOT EXISTS (SELECT 1 FROM tax_slabs);
