"""
pdf_importer.py

TaxSaint Bank Statement PDF Ingestion Engine.
Parses text and tabular statement data from PDF bank statements (SBI, HDFC, ICICI, Axis, etc.)
and normalizes records into the standard TaxSaint transaction pipeline.
"""
from __future__ import annotations

import io
import re
from datetime import datetime
from typing import BinaryIO, Union
import pandas as pd


DATE_REGEX = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}-[A-Za-z]{3}-\d{2,4})\b"
)
AMOUNT_REGEX = re.compile(r"[\d,]+\.\d{2}")


def parse_date_str(date_text: str) -> str | None:
    """Standardizes various date formats to ISO YYYY-MM-DD."""
    cleaned = date_text.strip().replace("/", "-")
    for fmt in ("%d-%m-%Y", "%d-%m-%y", "%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y"):
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def extract_raw_text(file_source: Union[bytes, BinaryIO, str]) -> str:
    """Extracts raw text strings from PDF bytes or path."""
    if isinstance(file_source, bytes):
        stream = io.BytesIO(file_source)
    elif hasattr(file_source, "read"):
        stream = file_source
    else:
        with open(file_source, "rb") as f:
            stream = io.BytesIO(f.read())

    # 1. Try PyPDF / pypdf if installed
    try:
        from pypdf import PdfReader
        reader = PdfReader(stream)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            return text
    except ImportError:
        pass

    # 2. Try pdfplumber if available
    try:
        import pdfplumber
        stream.seek(0)
        with pdfplumber.open(stream) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            if text.strip():
                return text
    except ImportError:
        pass

    # 3. Native fallback: Extract text streams directly from PDF object stream
    stream.seek(0)
    raw_bytes = stream.read()
    matches = re.findall(rb"\((.*?)\)\s*Tj", raw_bytes)
    if matches:
        return "\n".join(m.decode("latin1", errors="ignore") for m in matches)

    return raw_bytes.decode("latin1", errors="ignore")


def parse_pdf_statement(file_source: Union[bytes, BinaryIO, str]) -> pd.DataFrame:
    """
    Parses a bank statement PDF and returns a DataFrame matching TaxSaint's
    bank_transaction / income / expense schema.
    """
    raw_text = extract_raw_text(file_source)
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    records = []

    for line in lines:
        date_match = DATE_REGEX.search(line)
        if not date_match:
            continue

        raw_date = date_match.group(1)
        iso_date = parse_date_str(raw_date)
        if not iso_date:
            continue

        amounts = AMOUNT_REGEX.findall(line)
        if not amounts:
            continue

        float_amounts = []
        for a in amounts:
            try:
                float_amounts.append(float(a.replace(",", "")))
            except ValueError:
                continue

        if not float_amounts:
            continue

        narration = line
        narration = narration.replace(raw_date, "")
        for a in amounts:
            narration = narration.replace(a, "")
        narration = re.sub(r"\s+", " ", narration).strip(" -|/")
        if not narration:
            narration = "Bank Transaction"

        line_upper = line.upper()
        if "CR" in line_upper or "CREDIT" in line_upper or "DEPOSIT" in line_upper:
            tx_type = "INCOME"
            amount = float_amounts[0]
        elif "DR" in line_upper or "DEBIT" in line_upper or "WITHDRAWAL" in line_upper:
            tx_type = "EXPENSE"
            amount = float_amounts[0]
        else:
            amount = float_amounts[0]
            tx_type = "EXPENSE" if "TO " in line_upper or "PAYMENT" in line_upper else "INCOME"

        records.append({
            "date": iso_date,
            "party_name": narration[:100],
            "amount": str(amount),
            "transaction_type": tx_type,
        })

    if not records:
        return pd.DataFrame(columns=["date", "party_name", "amount", "transaction_type"])

    return pd.DataFrame(records)
