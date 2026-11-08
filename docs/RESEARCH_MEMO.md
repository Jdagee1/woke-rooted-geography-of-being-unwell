# ASCEND Research & Interpretation Memo
## Evidence Gap 1: End-to-End SQL Analytics Project

**F+M Labs / ASCEND Career Development** · **Woke & Rooted**  
**Project:** The Geography of Being Unwell  
**Completed analytic run:** November 7, 2026  
**Status:** Reproducible descriptive analysis; publication preparation in progress

## Executive finding

Across 2,417 U.S. county and county-equivalent records with modeled estimates available for all three selected CDC PLACES indicators, social isolation and mental distress are moderately positively associated (**r = 0.5069**), as are lack of social and emotional support and mental distress (**r = 0.4738**). Social isolation and lack of support are more strongly associated with each other (**r = 0.7180**). These are **ecological, descriptive relationships**, not evidence of causation or relationships among individual people.

## Research question

Where do frequent mental distress, social isolation, and a lack of social/emotional support coincide geographically—and what responsible research questions does this raise for community-centered organizations?

## Methods and provenance

- **Source:** CDC PLACES, County Data 2024 release (`fu4u-a9bh`), CDC-hosted CSV.
- **Extraction:** Python `urllib` downloaded the public CSV to the Ubuntu VM.
- **Transformation:** Header normalization, crude-prevalence filtering, county identifier preservation, national-summary exclusion, missingness preservation, and three-measure pivot.
- **Storage:** SQLite `counties` and `observations` tables, with `county_metrics` analytic view.
- **Quality gates:** County FIPS uniqueness, geographic match coverage, completeness checks, duplicate observation checks and range checks.
- **Analysis:** `SELECT`, `COUNT`, `WHERE`, `AND`, `IS NULL`, `JOIN`, `AVG`, `CASE`, `GROUP BY`, CTEs and SQL-computed Pearson correlations.
- **Analytical sample:** 3,144 county areas; 2,417 complete across all three measures; 727 missing both social indicators.

## Findings to defend in an interview

| Test | Result | What can be concluded |
|---|---|---|
| County row count vs distinct FIPS | 3,144 / 3,144 | County IDs are unique in the county dimension |
| Missing county-to-metric matches | 0 | Every county has a metrics-view record |
| Missingness in distress / isolation / support | 0 / 727 / 727 | Complete-case selection excludes 727 records |
| Unweighted average distress / isolation / support | 17.31% / 32.88% / 25.01% | Descriptive county means within complete cases |
| Distress mean, higher- vs lower-isolation county group | 18.17% vs 16.47% | 1.70-point group difference |
| Correlations: distress-isolation / distress-support / isolation-support | .5069 / .4738 / .7180 | Moderate / moderate / stronger positive ecological associations |

## Discover → Reflect → Explain → Apply

### Discover

I identified a public CDC source that connects to Woke & Rooted's interest in mental health and community support. I inspected real database tables, county identifiers and model-based estimates rather than relying on invented example data.

### Reflect

The project required addressing a real ingestion failure: the source contained U.S.-level summary records, which failed county validation. Rather than suppressing all errors, I introduced a targeted filter that excludes national records while retaining validation of actual counties. Missingness was another substantive finding: the social isolation and support metrics share 727 missing county areas.

### Explain

I can distinguish row counts from distinct county identifiers, understand why county names are not unique keys, explain inner and left joins, recognize NULL versus zero, describe complete-case analysis, and calculate and interpret three pairwise Pearson correlations. I can also explain why a county-average percentage is not a national adult prevalence rate.

### Apply

I implemented the source-to-database pipeline on Ubuntu, queried and interpreted the real results, assembled reusable SQL, and prepared documented research artifacts for publication. The next application is to examine geographic missingness by state, evaluate uncertainties and build evidence-based visual storytelling rather than asserting causes.

## Decisions and caveats

1. The unit of analysis is a **county/county-equivalent**, not an individual resident.
2. The social measures from this **2024 release are geographically limited**: CDC modeled new health-related social-needs measures for 39 states and Washington, D.C. The 727 missing estimates should not be treated as random missingness.
3. Removing incomplete records gives a consistent sample for three-way comparisons, but also narrows geographic coverage.
4. Rates are modeled and historical, so geographic rankings carry uncertainty.
5. The study does not test the effects of churches, public programs, or nonprofit interventions; these may be topics for further research, not findings.
6. The heatmap is generated from the analyzed correlations and is not an independent validation of raw records.

## Evidence-gap completion criteria

- [x] Real public source and reproducible extraction process
- [x] Working database schema and county-level analytical view
- [x] County key and match checks
- [x] Missing-data profiling and sample selection
- [x] Descriptive and comparative SQL analysis
- [x] Full three-variable correlation matrix
- [x] Reusable `sql/04_findings.sql` and documented interpretation
- [ ] Rerun all saved SQL in the VM and save output/checksum
- [ ] Confirm tests on the VM and GitHub Actions after publishing
- [ ] Publish repository to GitHub and verify files online
- [ ] Investigate geographic noncoverage and uncertainty

## Interview-ready project summary

> I built a reproducible Python-and-SQL pipeline from the CDC's 2024 PLACES county release, cleaned mixed-grain geographic data, validated county identifiers and geographic joins, audited missing measurements, and computed descriptive statistics and county-level correlations. Across 2,417 complete records, I observed moderate positive associations between mental distress and two measures of social disconnection. I clearly documented limitations caused by modeled estimates, missing geography, equal county weighting and the inability to infer causality.

**Source:** https://data.cdc.gov/d/fu4u-a9bh  
**Technical methods:** [`../docs/METHODS.md`](METHODS.md)  
**SQL reproducibility:** [`../sql/04_findings.sql`](../sql/04_findings.sql)
