# Tax Engine

C++ engine (namespace `tax_engine`) that calculates income tax under the **new tax regime** for `SALARIED` and `BUSINESS` users. It has no database code and no hardcoded tax values: every rule comes from the backend.

## Functions (`calculatetax.h`)

| Function | Purpose |
|---|---|
| `validate_rules(rules)` | Checks the rules sent by the backend. An empty list means they are valid. |
| `validate_input(income, expenses, workerType)` | Checks one user's input. |
| `calculate_tax(taxable_income, rules)` | Applies the slabs and the 87A rebate, then returns the tax before cess. |
| `calculate_tax_result(income, expenses, workerType, rules)` | Runs the full calculation and returns a `TaxResult`. |

`TaxResult` contains `grossIncome`, `expenses`, `taxableIncome`, `taxBeforeCess`, `cess` and `totalTax`.

## Calculation

1. `taxable = income − expenses`
2. For SALARIED users, subtract `standard_deduction`. Taxable income never goes below 0.
3. Apply the slabs progressively. If `taxable ≤ rebate_limit`, the tax becomes 0. This gives `taxBeforeCess`.
4. `cess = taxBeforeCess × cess_rate / 100`, then `totalTax = taxBeforeCess + cess`.

## Build and run

```bash
g++ -std=c++17 calculatetax.cpp -o calculatetax
./calculatetax < input.txt
```

## Input (stdin)

Write one record per line, with fields separated by `|`. Blank lines and lines starting with `#` are ignored.

```
RULE|standard_deduction|75000
RULE|rebate_limit|1200000
RULE|cess_rate|4
SLAB|0|400000|0
SLAB|400000|800000|5
SLAB|800000|1200000|10
SLAB|1200000|1600000|15
SLAB|1600000|2000000|20
SLAB|2000000|2400000|25
SLAB|2400000||30
USER|u1|SALARIED|1800000|0
USER|u2|BUSINESS|3000000|1000000
```

| Record | Fields | Notes |
|---|---|---|
| `RULE` | `key`, `value` | All 3 rules are **required**. |
| `SLAB` | `lower`, `upper`, `rate` | Send in ascending order and start at 0, with no gaps. Leave `upper` empty on the last slab (DB `NULL`). The rate is a percent. |
| `USER` | `user_id`, `worker_type`, `income`, `expenses` | `worker_type` is `SALARIED` or `BUSINESS`. Amounts must be ≥ 0, with no commas. Text must not contain `\|`. |

## Output (stdout)

```json
{
  "ok": true,
  "results": [
    {"user_id": "u1", "worker_type": "SALARIED", "gross_income": 1800000.00, "expenses": 0.00,
     "taxable_income": 1725000.00, "tax_before_cess": 145000.00, "cess": 5800.00, "total_tax": 150800.00}
  ],
  "errors": []
}
```

## Exit codes

| Code | Meaning | What the backend should do |
|---|---|---|
| `0` | All OK | Use `results`. |
| `2` | Some input was invalid | Return `errors` as HTTP 422. Valid users are still in `results`. If the rules are invalid, `results` is empty. |
| other | Crash | HTTP 500 |

## Backend example

```python
import json, subprocess

def run_tax_engine(users, rules, slabs):
    lines = [f"RULE|standard_deduction|{rules['standard_deduction']}",
             f"RULE|rebate_limit|{rules['rebate_limit']}",
             f"RULE|cess_rate|{rules['cess_rate']}"]
    for s in sorted(slabs, key=lambda s: s.lower_limit):
        upper = "" if s.upper_limit is None else s.upper_limit
        lines.append(f"SLAB|{s.lower_limit}|{upper}|{s.rate}")
    for u in users:
        lines.append(f"USER|{u['user_id']}|{u['worker_type']}|{u['income']}|{u['expenses']}")

    proc = subprocess.run(["./tax_engine/calculatetax"], input="\n".join(lines),
                          capture_output=True, text=True, timeout=10)
    if proc.returncode not in (0, 2):
        raise RuntimeError(proc.stderr)
    return json.loads(proc.stdout)
```

## Known limitations

- **No marginal relief just above the rebate limit.** ₹12,00,010 of taxable income pays ₹62,401.56.
- **No surcharge** for incomes above ₹50L.
- **New regime only.**

## Tests

```bash
cd tax_calculation
pytest tests/test_tax.py -v
```
