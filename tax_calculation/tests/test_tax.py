"""Tests for the C++ tax engine (tax_engine/calculatetax.cpp).

The engine is compiled once and run through subprocess,
the same way the FastAPI backend will call it.
Run: pytest tests/test_tax.py -v
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ENGINE_SOURCE = Path(__file__).resolve().parent.parent / "tax_engine" / "calculatetax.cpp"

# FY 2026-27 rules, sent the same way the backend sends them from the database
RULES = [
    "RULE|standard_deduction|75000",
    "RULE|rebate_limit|1200000",
    "RULE|cess_rate|4",
    "SLAB|0|400000|0",
    "SLAB|400000|800000|5",
    "SLAB|800000|1200000|10",
    "SLAB|1200000|1600000|15",
    "SLAB|1600000|2000000|20",
    "SLAB|2000000|2400000|25",
    "SLAB|2400000||30",
]


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    """Compile calculatetax.cpp once for all tests."""
    if shutil.which("g++") is None:
        pytest.skip("g++ is not installed")
    binary = tmp_path_factory.mktemp("build") / "calculatetax"
    subprocess.run(["g++", "-std=c++17", str(ENGINE_SOURCE), "-o", str(binary)], check=True)
    return binary


def run_engine(engine, lines):
    """Send lines to the engine, return (exit_code, parsed_json)."""
    proc = subprocess.run([str(engine)], input="\n".join(lines) + "\n",
                          capture_output=True, text=True, timeout=10)
    return proc.returncode, json.loads(proc.stdout)


def tax_for(engine, worker_type, income, expenses=0):
    code, out = run_engine(engine, RULES + [f"USER|u1|{worker_type}|{income}|{expenses}"])
    assert code == 0, out
    return out["results"][0]


# ---------------- Salaried ----------------

def test_salaried_12_75_lakh_pays_zero(engine):
    r = tax_for(engine, "SALARIED", 1275000)
    assert r["taxable_income"] == 1200000
    assert r["total_tax"] == 0


def test_salaried_18_lakh(engine):
    r = tax_for(engine, "SALARIED", 1800000)
    assert r["taxable_income"] == 1725000
    assert r["tax_before_cess"] == 145000
    assert r["cess"] == 5800
    assert r["total_tax"] == 150800


def test_salaried_30_lakh_reaches_30_percent_slab(engine):
    assert tax_for(engine, "SALARIED", 3000000)["total_tax"] == 475800


def test_salaried_low_income_never_negative(engine):
    r = tax_for(engine, "SALARIED", 50000)
    assert r["taxable_income"] == 0
    assert r["total_tax"] == 0


# ---------------- Business ----------------

def test_business_no_standard_deduction(engine):
    r = tax_for(engine, "BUSINESS", 3000000, 1000000)
    assert r["taxable_income"] == 2000000
    assert r["total_tax"] == 208000


def test_business_exactly_12_lakh_gets_rebate(engine):
    assert tax_for(engine, "BUSINESS", 1200000)["total_tax"] == 0


def test_business_loss_gives_zero_tax(engine):
    r = tax_for(engine, "BUSINESS", 500000, 800000)
    assert r["taxable_income"] == 0
    assert r["total_tax"] == 0


# ---------------- Result format ----------------

def test_result_has_all_fields(engine):
    r = tax_for(engine, "SALARIED", 1800000)
    for key in ("gross_income", "expenses", "taxable_income",
                "tax_before_cess", "cess", "total_tax"):
        assert key in r


# ---------------- Rules from backend ----------------

def test_rules_come_from_input(engine):
    rules = [line if line != "RULE|cess_rate|4" else "RULE|cess_rate|0" for line in RULES]
    code, out = run_engine(engine, rules + ["USER|u1|SALARIED|1800000|0"])
    assert out["results"][0]["total_tax"] == 145000


def test_missing_rules_refuse_to_calculate(engine):
    code, out = run_engine(engine, ["USER|u1|SALARIED|1800000|0"])
    assert code == 2
    assert out["ok"] is False
    assert out["results"] == []


def test_slab_gap_rejected(engine):
    rules = [line for line in RULES if line != "SLAB|800000|1200000|10"]
    code, out = run_engine(engine, rules + ["USER|u1|SALARIED|1800000|0"])
    assert code == 2
    assert out["results"] == []


# ---------------- Validation ----------------

def test_bad_users_reported_good_users_calculated(engine):
    code, out = run_engine(engine, RULES + [
        "USER|ok|SALARIED|1800000|0",
        "USER|b1|STUDENT|500000|0",
        "USER|b2|SALARIED|-100|0",
        "USER|b3|BUSINESS|abc|0",
        "USER|b4|BUSINESS|100000",
    ])
    assert code == 2
    assert [r["user_id"] for r in out["results"]] == ["ok"]
    assert len(out["errors"]) == 4
