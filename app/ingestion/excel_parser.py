"""Flexible Excel parsing pipeline powered by Claude.

Steps:
  1. Identify the correct maintenance-log sheet (if >1 sheet exists)
  2. Map arbitrary column headers to standard field names
  3. Normalise the full dataframe using that mapping
  4. Analyse maintenance patterns and return structured JSON
"""

import json
import math
from io import BytesIO
from typing import Any

import pandas as pd
from openai import AsyncOpenAI

from app.config import settings


def _extract_json(text: str) -> Any:
    """Strip markdown fences and parse JSON."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)


def _safe_value(v: Any) -> Any:
    """Convert pandas / numpy non-serialisable types to plain Python types."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):  # numpy scalar
        return v.item()
    if hasattr(v, "isoformat"):  # datetime / Timestamp
        return v.isoformat()
    return v


class ExcelParser:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.API_KEY, base_url=settings.API_BASE_URL)

    # ── Step 1: Identify the right sheet ──────────────────────────────────────

    async def _identify_sheet(self, xl: pd.ExcelFile) -> str:
        if len(xl.sheet_names) == 1:
            return xl.sheet_names[0]

        previews: list[str] = []
        for name in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=name, header=None, nrows=4)
            df = df.ffill(axis=1).ffill(axis=0)
            previews.append(f"Sheet: '{name}'\nPreview:\n{df.to_string(index=False)}")

        prompt = (
            "You are an aviation data analyst. I have an Excel file with the following sheets. "
            "Identify which sheet contains the aircraft maintenance log.\n\n"
            + "\n\n".join(previews)
            + "\n\nReturn ONLY the exact sheet name with no extra text."
        )

        resp = await self._client.chat.completions.create(
            model=settings.MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip().strip("'\"")

    # ── Step 2: Map columns ───────────────────────────────────────────────────

    async def _map_columns(self, headers: list[str], sample_rows: list[dict]) -> dict[str, str | None]:
        sample_text = "\n".join(str(r) for r in sample_rows)
        prompt = (
            'You are an aviation data analyst. Map these Excel columns to these standard fields: '
            'fault_date, ata_chapter, fault_code, fault_description, action_taken, part_number, '
            'flight_hours, status. '
            '\n\nHeaders: ' + str(headers) +
            '\nSample rows:\n' + sample_text +
            '\n\nReturn only a JSON object where keys are standard field names and values are '
            'the matching column name from the file. If a field has no match, set its value to null.'
            '\nExample: {"fault_date": "Date of Fault", "ata_chapter": "ATA", "fault_code": null}'
        )

        resp = await self._client.chat.completions.create(
            model=settings.MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_json(resp.choices[0].message.content)

    # ── Step 3: Pattern analysis ──────────────────────────────────────────────

    async def _analyze_patterns(self, records: list[dict]) -> dict:
        # Cap at 50 records and strip to key fields to keep prompt small
        key_fields = ["fault_description", "component", "date", "action_taken", "status"]
        trimmed = [
            {k: r.get(k) for k in key_fields if r.get(k) is not None}
            for r in records[:50]
        ]
        data_text = json.dumps(trimmed, default=str)

        prompt = (
            "Analyze this aircraft maintenance history. "
            "Return ONLY a compact JSON object with these fields — keep all string values short:\n"
            '{"top_faults":["<5 most frequent faults>"],'
            '"recurring_components":["<components appearing 2+ times>"],'
            '"unresolved_patterns":["<faults that recurred after fix>"],'
            '"time_between_recurrences":<avg days as number or null>,'
            '"risk_summary":"<1 sentence max>"}\n\n'
            "Data:\n" + data_text
        )

        resp = await self._client.chat.completions.create(
            model=settings.MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            return _extract_json(resp.choices[0].message.content)
        except (json.JSONDecodeError, Exception):
            return {
                "top_faults": [],
                "recurring_components": [],
                "unresolved_patterns": [],
                "time_between_recurrences": None,
                "risk_summary": "Pattern analysis unavailable.",
            }

    # ── Public entry point ────────────────────────────────────────────────────

    async def parse(
        self, file_content: bytes, filename: str
    ) -> tuple[list[dict], dict]:
        """Return (normalised_records, pattern_analysis)."""
        xl = pd.ExcelFile(BytesIO(file_content))

        # 1. Sheet identification
        sheet_name = await self._identify_sheet(xl)

        # 2. Load sheet
        df = pd.read_excel(xl, sheet_name=sheet_name)
        df = df.ffill()                  # fill merged cells
        df = df.dropna(how="all")        # remove blank rows

        # 3. Column mapping
        headers = list(df.columns.astype(str))
        sample = df.head(10).to_dict("records")
        mapping = await self._map_columns(headers, sample)

        # 4. Normalise
        records: list[dict] = []
        for _, row in df.iterrows():
            record: dict[str, Any] = {}
            for std_field, excel_col in mapping.items():
                if excel_col and excel_col in df.columns:
                    record[std_field] = _safe_value(row.get(excel_col))
                else:
                    record[std_field] = None
            records.append(record)

        # 5. Pattern analysis
        pattern_analysis = await self._analyze_patterns(records)

        return records, pattern_analysis
