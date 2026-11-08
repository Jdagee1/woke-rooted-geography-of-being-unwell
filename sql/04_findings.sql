-- WOKE & ROOTED | PORTFOLIO PROJECT 001
-- Findings SQL, to run on CDC PLACES 2024 data loaded into county_metrics.
-- From project root: sqlite3 -header -column data/woke_rooted.sqlite < sql/04_findings.sql
-- County values = modeled crude prevalence percentages; not diagnoses or population counts.

-- 01: Coverage and complete-case sample (expected from Nov 7 VM: 3144 / 2417)
SELECT COUNT(*) AS county_rows,
       SUM(mental_distress_pct IS NULL) AS missing_distress,
       SUM(isolation_pct IS NULL) AS missing_isolation,
       SUM(lack_support_pct IS NULL) AS missing_support,
       SUM(isolation_pct IS NULL AND lack_support_pct IS NULL) AS missing_both_social,
       SUM(mental_distress_pct IS NOT NULL
           AND isolation_pct IS NOT NULL
           AND lack_support_pct IS NOT NULL) AS complete_cases
FROM county_metrics;

-- 02: Highest mental distress among complete-case counties (tie order by FIPS)
SELECT state_name, county_name, county_fips,
       ROUND(mental_distress_pct,2) AS mental_distress_pct,
       ROUND(isolation_pct,2) AS isolation_pct,
       ROUND(lack_support_pct,2) AS lack_support_pct
FROM county_metrics
WHERE mental_distress_pct IS NOT NULL
  AND isolation_pct IS NOT NULL
  AND lack_support_pct IS NOT NULL
ORDER BY mental_distress_pct DESC, county_fips ASC
LIMIT 15;

-- 03: Unweighted county means; not national adult prevalence estimates
SELECT COUNT(*) AS counties_analyzed,
       ROUND(AVG(mental_distress_pct),2) AS avg_distress,
       ROUND(AVG(isolation_pct),2) AS avg_isolation,
       ROUND(AVG(lack_support_pct),2) AS avg_lack_support
FROM county_metrics
WHERE mental_distress_pct IS NOT NULL
  AND isolation_pct IS NOT NULL
  AND lack_support_pct IS NOT NULL;

-- 04: Group comparison. The threshold is the *rounded* observed mean, 32.88%.
-- A fixed, clearly stated threshold reproduces the Nov 7 analysis exactly.
SELECT CASE WHEN isolation_pct >= 32.88 THEN 'Higher isolation'
            ELSE 'Lower isolation' END AS isolation_group,
       COUNT(*) AS county_count,
       ROUND(AVG(mental_distress_pct),2) AS avg_distress,
       ROUND(AVG(isolation_pct),2) AS avg_isolation
FROM county_metrics
WHERE mental_distress_pct IS NOT NULL
  AND isolation_pct IS NOT NULL
  AND lack_support_pct IS NOT NULL
GROUP BY isolation_group
ORDER BY avg_isolation DESC;

-- 05: All 3 Pearson r coefficients using SQL alone.
-- Requires a SQLite build with SQRT() math function (common on modern Ubuntu).
-- Outputs are county-level associations and cannot demonstrate causation.
WITH moments AS (
  SELECT COUNT(*) AS n,
         SUM(mental_distress_pct) AS sm,
         SUM(isolation_pct) AS si,
         SUM(lack_support_pct) AS ss,
         SUM(mental_distress_pct * mental_distress_pct) AS sm2,
         SUM(isolation_pct * isolation_pct) AS si2,
         SUM(lack_support_pct * lack_support_pct) AS ss2,
         SUM(mental_distress_pct * isolation_pct) AS smi,
         SUM(mental_distress_pct * lack_support_pct) AS sms,
         SUM(isolation_pct * lack_support_pct) AS sis
  FROM county_metrics
  WHERE mental_distress_pct IS NOT NULL
    AND isolation_pct IS NOT NULL
    AND lack_support_pct IS NOT NULL
)
SELECT n,
  ROUND((n*smi-sm*si) / SQRT((n*sm2-sm*sm)*(n*si2-si*si)), 4)
    AS distress_isolation_r,
  ROUND((n*sms-sm*ss) / SQRT((n*sm2-sm*sm)*(n*ss2-ss*ss)), 4)
    AS distress_lack_support_r,
  ROUND((n*sis-si*ss) / SQRT((n*si2-si*si)*(n*ss2-ss*ss)), 4)
    AS isolation_lack_support_r
FROM moments;

-- 06: Where are values missing? Investigate *coverage*, not just total missingness.
SELECT state_abbr,
       COUNT(*) AS total_areas,
       SUM(isolation_pct IS NULL) AS missing_isolation,
       SUM(lack_support_pct IS NULL) AS missing_support,
       SUM(mental_distress_pct IS NOT NULL
           AND isolation_pct IS NOT NULL
           AND lack_support_pct IS NOT NULL) AS complete_areas
FROM county_metrics
GROUP BY state_abbr
ORDER BY missing_isolation DESC, state_abbr;
