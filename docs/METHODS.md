# Methods and data dictionary

## Unit of analysis
A county-equivalent FIPS identifier (`LocationID`), treated as five-character text, preserving leading zeroes. Source long-format observations are filtered to three `MeasureId` values, then pivoted to one county row with three measures.

## Source fields used
| Raw field (normalized for case/spacing) | Meaning |
|---|---|
| `LocationID` | County-equivalent five-digit FIPS text |
| `StateAbbr` | Two-letter state abbreviation |
| `StateDesc` | State name, when provided |
| `LocationName` | County name |
| `MeasureId` | `MHLTH`, `ISOLATION`, or `EMOTIONSPT` |
| `Data_Value` | Modeled prevalence estimate, percent |
| `Data_Value_Type` | If present, filter to crude prevalence |

Some CDC releases change field capitalization and use spaces/underscores. The loader normalizes headers. If source schema changes materially, the pipeline fails instead of silently misinterpreting data.

## Quality gates
- Reject missing identifiers, duplicate county+measure rows, contradictory county descriptors, nonnumeric or out-of-range prevalence, and missing requisite headers.
- Only target measures are loaded. Missing prevalence values are recorded as missing, **not** converted to zero.
- Reject an empty extract, missing required measures, and implausibly small input (fewer than 100 counties) when processing real CDC data.
- Tests use a clearly fictional five-row CSV and do **not** assert population findings.

## Distinctions worth explaining in interviews
- `COUNT(*)` counts records, not respondents, and cannot recover a population estimate from a prevalence rate.
- `GROUP BY` groups rows before aggregation.
- `JOIN` links measures to county descriptors by stable FIPS; the pivot is conditional aggregation.
- `WHERE` excludes missing values from comparisons; disclosure of missingness is mandatory.
- Window functions rank and calculate medians without collapsing all observations.
- Three co-occurring above-median measures are a descriptive flag, not a risk diagnosis.

## Limitations and ethics
CDC PLACES 2024 release largely draws on 2022 BRFSS estimates and ACS/census information. The modeled county estimates carry uncertainty and may not track the same individual people. Correlation between prevalence estimates cannot establish whether isolation causes distress or vice versa. This design neither estimates the effects of churches/nonprofits nor represents any faith community, marital status, or identity group directly. Do not infer individual characteristics or stigmatize places. County medians and averages are unweighted across counties; do not label as national adult prevalence. Respect the CDC warning that PLACES estimates should not be used to evaluate local interventions.

## Actual production ingestion fix and geographic coverage (Nov 2026)

The official CSV also contains national summary rows (`StateAbbr='US'`) that are not county-level observations and have no valid county name/FIPS at this grain. A **targeted filter before county ID validation** excludes only those national rows; all other county validations remain in force. The original CSV is never edited. Regression coverage is included in `tests/test_pipeline.py`.

The CDC reports that in its **2024 release**, new health-related social needs estimates were modeled for **39 states and Washington, D.C.** As a result, missing isolation and support values cannot be assumed missing at random and may reflect known geographic availability restrictions. Query `sql/04_findings.sql` (section 06) before concluding anything about representativeness.

The main analysis uses `WHERE mental_distress_pct IS NOT NULL AND isolation_pct IS NOT NULL AND lack_support_pct IS NOT NULL` (2,417 cases reported from VM). The mean-categorization threshold is **32.88%**, rounded to two decimals, as documented in the November 7 local analysis. Correlations are unweighted Pearson r across these same cases.

Validation of county uniqueness uses **five-digit FIPS text** rather than county names; counties with the same name in different states are distinct. The absence of duplicate FIPS values in the counties dimension doesn't imply county-level measurement precision or causal identifiability.

The chart included in this repository uses the 3 correlations returned from the user's real-data VM analysis; the included SVG generator recalculates correlations from the local database when run. The repository intentionally excludes the CDC raw source file and generated database, allowing explicit provenance checks and reproducibility.
