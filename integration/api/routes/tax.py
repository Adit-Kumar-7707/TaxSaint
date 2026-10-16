"""Tax calculation endpoint that calls the existing C++ tax engine."""
from __future__ import annotations
import json
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database_manager.connection import get_db
from database_manager.models import TaxResult, TaxSettings, TaxSlab, User
from integration.api.schemas.requests import TaxCalculateRequest

router = APIRouter(prefix="/api/tax", tags=["tax"])
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENGINE_SOURCE = PROJECT_ROOT / "tax_calculation" / "tax_engine" / "calculatetax.cpp"

@lru_cache(maxsize=1)
def _compiled_engine(source_mtime: float) -> str:
    """Compile the C++ engine once per source version into a temporary binary."""
    compiler = shutil.which("g++") or shutil.which("c++")
    if not compiler:
        raise RuntimeError("A C++ compiler (g++) is required to run the tax engine.")
    binary = Path(tempfile.gettempdir()) / "taxsaint_calculatetax"
    result = subprocess.run([compiler, "-std=c++17", str(ENGINE_SOURCE), "-o", str(binary)],
                            capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Could not compile tax engine: {result.stderr[-1500:]}")
    return str(binary)

def _run_engine(user_id: int, worker_type: str, income: float, expenses: float, settings: TaxSettings, slabs: list[TaxSlab]) -> dict:
    if not slabs:
        raise HTTPException(status_code=503, detail="No tax slabs are configured in the database.")
    try:
        binary = _compiled_engine(ENGINE_SOURCE.stat().st_mtime)
        lines = [
            f"RULE|standard_deduction|{float(settings.standard_deduction)}",
            f"RULE|rebate_limit|{float(settings.rebate_limit)}",
            f"RULE|cess_rate|{float(settings.cess_rate)}",
        ]
        for slab in sorted(slabs, key=lambda row: float(row.lower_limit)):
            upper = "" if slab.upper_limit is None else str(float(slab.upper_limit))
            lines.append(f"SLAB|{float(slab.lower_limit)}|{upper}|{float(slab.rate)}")
        lines.append(f"USER|{user_id}|{worker_type}|{income}|{expenses}")
        proc = subprocess.run([binary], input="\n".join(lines) + "\n", capture_output=True,
                              text=True, timeout=10)
        if proc.returncode not in (0, 2):
            raise RuntimeError(proc.stderr or f"Tax engine exited with code {proc.returncode}.")
        output = json.loads(proc.stdout)
        if not output.get("results"):
            message = "; ".join(item.get("message", str(item)) for item in output.get("errors", []))
            raise HTTPException(status_code=422, detail=message or "Tax calculation could not be completed.")
        return output["results"][0]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Tax engine error: {exc}") from exc

@router.post("/calculate")
def calculate_tax(payload: TaxCalculateRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found. Create the user before calculating tax.")
    worker_type = (payload.user_type or user.worker_type).upper()
    if worker_type not in {"SALARIED", "BUSINESS"}:
        raise HTTPException(status_code=422, detail="userType must be salaried or business.")
    if worker_type != user.worker_type:
        raise HTTPException(status_code=422, detail="userType does not match the saved user profile.")

    if worker_type == "SALARIED":
        income = float(payload.income if payload.income is not None else ((payload.salary or 0) + (payload.other_income or 0)))
        # The C++ engine applies the salaried standard deduction. Other deductions
        # are not separately modeled by this engine and are therefore not silently applied.
        expenses = float(payload.expenses or 0)
    else:
        income = float(payload.income if payload.income is not None else (payload.business_income or 0))
        expenses = float(payload.expenses if payload.expenses is not None else (payload.business_expenses or 0))

    settings = db.query(TaxSettings).order_by(TaxSettings.id).first()
    slabs = db.query(TaxSlab).order_by(TaxSlab.lower_limit).all()
    if settings is None:
        raise HTTPException(status_code=503, detail="Tax settings are missing. Initialize the database first.")
    result = _run_engine(user.user_id, worker_type, income, expenses, settings, slabs)
    saved = TaxResult(user_id=user.user_id, gross_income=result["gross_income"], expenses=result["expenses"],
                      taxable_income=result["taxable_income"], tax_before_cess=result["tax_before_cess"],
                      cess=result["cess"], total_tax=result["total_tax"])
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return _serialize_tax_result(saved)

def _serialize_tax_result(row: TaxResult) -> dict:
    return {
        "id": row.result_id, "result_id": row.result_id, "user_id": row.user_id,
        "income": float(row.gross_income), "gross_income": float(row.gross_income),
        "expenses": float(row.expenses), "taxableIncome": float(row.taxable_income),
        "taxable_income": float(row.taxable_income), "tax": float(row.tax_before_cess),
        "tax_before_cess": float(row.tax_before_cess), "cess": float(row.cess),
        "totalTax": float(row.total_tax), "total_tax": float(row.total_tax),
        "calculated_at": row.calculated_at.isoformat() if row.calculated_at else None,
    }

@router.get("/result/{user_id}")
def get_tax_result(user_id: int, db: Session = Depends(get_db)):
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found.")
    row = db.query(TaxResult).filter(TaxResult.user_id == user_id).order_by(TaxResult.calculated_at.desc(), TaxResult.result_id.desc()).first()
    if row is None:
        return None
    return _serialize_tax_result(row)
