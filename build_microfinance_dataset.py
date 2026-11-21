"""MFIN Micrometer Annexure 5 (state-level) PDFs -> one Power BI-ready table.

Beyond extracting the numbers, it does only the usual prep before loading into Power BI:
  - real report date + full state name + region (so maps / slicers / sorting work)
  - current-year and prior-year values side by side in ONE row (suffix _PY = prior year,
    taken from the same report), so Power BI needs no current-vs-prior filtering

Growth %, ratios and rankings are left to Power BI measures, because they must be
recalculated from sums when the user filters (never averaged row-level percentages).

Run:  python build_dataset_lean.py      (needs: pymupdf pandas openpyxl)
Folder: raw_reports/*.pdf  ->  processed/state_data.csv, processed/state_data.xlsx
"""
import re
from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd

RAW, OUT = Path("raw_reports"), Path("processed")

# Issue -> (data as-on date, disbursement basis). Year-end issues (53, 57) report
# FULL-YEAR disbursement in the state table; the others report one quarter.
REPORTS = {53: ("2025-03-31", "Annual"),    54: ("2025-06-30", "Quarterly"),
           55: ("2025-09-30", "Quarterly"), 56: ("2025-12-31", "Quarterly"),
           57: ("2026-03-31", "Annual"),    58: ("2026-06-30", "Quarterly")}

# State code as printed in the report -> (name, region). Regions follow the report's grouping;
# checked by reproducing its Dec-25 regional AUM shares (East&NE 33%, South 28%, North/West 15%, Central 9%).
E_NE, N, S, W, C = "East & North East", "North", "South", "West", "Central"
STATES = {
    "AN": ("Andaman and Nicobar Islands", S), "AP": ("Andhra Pradesh", S), "AR": ("Arunachal Pradesh", E_NE),
    "AS": ("Assam", E_NE), "BH": ("Bihar", E_NE), "CG": ("Chhattisgarh", C), "CH": ("Chandigarh", N),
    "DL": ("Delhi", N), "DN": ("Dadra and Nagar Haveli and Daman and Diu", W), "GJ": ("Gujarat", W),
    "GO": ("Goa", W), "HP": ("Himachal Pradesh", N), "HR": ("Haryana", N), "JH": ("Jharkhand", E_NE),
    "JK": ("Jammu and Kashmir", N), "KA": ("Karnataka", S), "KL": ("Kerala", S), "MH": ("Maharashtra", W),
    "ML": ("Meghalaya", E_NE), "MN": ("Manipur", E_NE), "MP": ("Madhya Pradesh", C), "MZ": ("Mizoram", E_NE),
    "NL": ("Nagaland", E_NE), "OR": ("Odisha", E_NE), "PB": ("Punjab", N), "PY": ("Puducherry", S),
    "RJ": ("Rajasthan", W), "SK": ("Sikkim", E_NE), "TL": ("Telangana", S), "TN": ("Tamil Nadu", S),
    "TR": ("Tripura", E_NE), "UK": ("Uttarakhand", N), "UP": ("Uttar Pradesh", N), "WB": ("West Bengal", E_NE),
}

NUM = r"-?\d[\d,]*(?:\.\d+)?"                      # handles Indian grouping, e.g. 8,27,919
ROW = re.compile(rf"((?:Q[1-4] )?FY \d\d-\d\d)((?: {NUM}){{8}})")
STATE_RE = re.compile(rf"\b({'|'.join(STATES)})\b(?= (?:Q[1-4] )?FY)")
COLS = ["MFI_Count", "AUM_Cr", "Clients_Lakh", "Branches", "Employees",
        "Disbursed_Cr", "Loans_Disbursed_Lakh", "Avg_Loan_Rs"]
# Numbers that get a prior-year twin. MFI_Count (overlaps between states) and Avg_Loan_Rs (an average)
# can't be summed in Power BI, so they are dropped / kept current-only; compute averages as measures.
WITH_PY = ["AUM_Cr", "Clients_Lakh", "Branches", "Employees", "Disbursed_Cr", "Loans_Disbursed_Lakh"]


def parse_page(text: str, issue: int) -> list[dict]:
    text = re.sub(r"\s+", " ", text)               # ignore how the PDF breaks lines
    hits = [(m.start(), "state", m.group()) for m in STATE_RE.finditer(text)]
    hits += [(m.start(), "row", m) for m in ROW.finditer(text)]
    rows, state = [], None
    for _, kind, obj in sorted(hits, key=lambda h: h[0]):
        if kind == "state":
            state = obj
        elif state:
            vals = [float(v.replace(",", "")) for v in obj.group(2).split()]
            rows.append({"Issue": issue, "State_Code": state, "Period": obj.group(1), **dict(zip(COLS, vals))})
    return rows


def main():
    rows = []
    for pdf in sorted(RAW.glob("*.pdf")):
        issue = int(re.match(r"(\d+)", pdf.name).group(1))
        if issue not in REPORTS:
            continue
        with fitz.open(pdf) as doc:
            for page in doc:
                t = page.get_text()
                if "Aggregated state level data" in t and "Branches" in t:
                    rows += parse_page(t, issue)
    df = pd.DataFrame(rows)
    assert not df.duplicated(["Issue", "State_Code", "Period"]).any(), "duplicate rows"
    assert (df.groupby(["Issue", "State_Code"]).size() == 2).all(), "each state needs a current and a prior-year row"

    # Current vs prior-year row: the later fiscal year in the period label ("25-26" > "24-25") is current
    fy = df.Period.str[-5:]
    is_cur = fy == fy.groupby(df.Issue).transform("max")
    cur = df[is_cur]
    prev = df[~is_cur][["Issue", "State_Code", *WITH_PY]]
    out = cur.merge(prev, on=["Issue", "State_Code"], suffixes=("", "_PY"))

    out["Report_Date"] = pd.to_datetime(out.Issue.map(lambda i: REPORTS[i][0]))
    out["Disbursement_Basis"] = out.Issue.map(lambda i: REPORTS[i][1])
    out["State"] = out.State_Code.map(lambda c: STATES[c][0])
    out["Region"] = out.State_Code.map(lambda c: STATES[c][1])

    cols = ["Issue", "Report_Date", "State", "Region", "Disbursement_Basis", "MFI_Count",
            *[c for w in WITH_PY for c in (w, w + "_PY")]]
    out = out[cols].sort_values(["Issue", "State"]).reset_index(drop=True)

    OUT.mkdir(exist_ok=True)
    out.to_csv(OUT / "state_data.csv", index=False)
    out.to_excel(OUT / "state_data.xlsx", index=False)
    print(len(df), "raw rows ->", len(out), "state-report rows,", out.State.nunique(), "states")


if __name__ == "__main__":
    main()