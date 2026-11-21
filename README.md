# India Microfinance Dashboard (MFIN Micrometer, Issues 53-58)
 
A Python script and a Power BI report built from the state-level tables in six issues of the MFIN Micrometer.
 
## Files
 
| File | What it is |
|---|---|
| `build_dataset_lean.py` | Python script that reads the state-level table from the Micrometer PDFs and writes a data table |
| `microfinance_recovery.pbix` | Power BI report (the data is stored inside the file) |
| `dashboard.pdf` | PDF export of the Power BI report |
 
The Micrometer PDFs are not included. They are published by MFIN (www.mfinindia.org).
 
## Data source
 
MFIN (Microfinance Industry Network), *Micrometer*, issues 53 to 58 (data as on 31 Mar 2025, 30 Jun 2025, 30 Sep 2025, 31 Dec 2025, 31 Mar 2026 and 30 Jun 2026). The script uses Annexure 5, "Aggregated state level data", which covers member NBFC-MFIs.
 
Each report lists every state twice: the current period and the same period a year earlier.
 
## Python script
 
`build_dataset_lean.py` does the following:
 
- Finds the Annexure 5 pages in each PDF.
- Extracts each state's row (8 numbers: MFI count, AUM, clients, branches, employees, amount disbursed, loans disbursed, average loan).
- Converts numbers in Indian format (for example `8,27,919`) into numeric values.
- Puts each state's current-period and prior-year (`_PY`) values on one row.
- Adds the report date, full state name and region, and a label for annual or quarterly disbursement.
- Checks for duplicate rows and confirms every state has both a current and a prior-year row.
- Saves `processed/state_data.csv` and `processed/state_data.xlsx`.
Output: 304 rows extracted from the PDFs, reduced to 152 rows (one per state per report) across 27 states, with 18 columns.
 
## Columns in the data table
 
| Column | Meaning |
|---|---|
| `Issue`, `Report_Date` | Micrometer issue number and the date its data is as on |
| `State`, `Region` | State name and region (regions follow the grouping in the report) |
| `Disbursement_Basis` | `Annual` or `Quarterly` |
| `MFI_Count` | Number of member NBFC-MFIs in the state (current period) |
| `AUM_Cr`, `AUM_Cr_PY` | Loans outstanding, Rs crore |
| `Clients_Lakh`, `Clients_Lakh_PY` | Clients, in lakh |
| `Branches`, `Branches_PY` | Branches |
| `Employees`, `Employees_PY` | Employees |
| `Disbursed_Cr`, `Disbursed_Cr_PY` | Loan amount disbursed, Rs crore |
| `Loans_Disbursed_Lakh`, `Loans_Disbursed_Lakh_PY` | Number of loans disbursed, in lakh |
 
`_PY` means prior year (the same period a year earlier, taken from the same report).
 
## Power BI report
 
The CSV is loaded into Power BI as a table named `state_data`.
 
**DAX measures**
 
| Measure | Definition |
|---|---|
| Total AUM / Total AUM PY | Sum of `AUM_Cr` / `AUM_Cr_PY` |
| AUM YoY % | `DIVIDE([Total AUM], [Total AUM PY]) - 1` |
| Total Clients / Total Clients PY | Sum of `Clients_Lakh` / `Clients_Lakh_PY` |
| Clients YoY % | `DIVIDE([Total Clients], [Total Clients PY]) - 1` |
| AUM per Client (Rs) / AUM per Client PY (Rs) | `DIVIDE(AUM, Clients) * 100` for the current and prior year |
| AUM per Client YoY % | `DIVIDE([AUM per Client (Rs)], [AUM per Client PY (Rs)]) - 1` |
 
Growth rates are calculated from summed values, not by averaging state percentages.
 
**Pages**
 
- **Overview:** KPI cards, a line chart of AUM growth and client growth by report, and a column chart of AUM per client.
- **State view:** report-date and region slicers, a bar chart of AUM growth by state, and a scatter chart of client growth against AUM-per-client growth.


## Data notes
 
- In issues 53 and 57 (year-end), the disbursement columns are full-year totals. In the other issues they are single-quarter totals. `Disbursement_Basis` marks which.
- The state table only lists states where 5 or more MFIN member NBFC-MFIs operate, so totals are not national totals.
- The same date can differ slightly between issues, so each report is compared only with its own prior-year row.
## Source
 
MFIN, *Micrometer* (Microfinance Industry Network). All source data belongs to MFIN. This is an independent project for learning purposes and is not affiliated with MFIN.
 

 
