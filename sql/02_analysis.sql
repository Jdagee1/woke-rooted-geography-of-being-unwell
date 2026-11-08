-- Woke & Rooted × F+M Labs: real CDC PLACES 2024 release, county grain.
-- All values are prevalence percentages (modeled); these are NOT diagnosed counts.

-- Q1: Highest estimated frequent mental distress counties (a descriptive rank)
SELECT state_abbr, county_name, county_fips, mental_distress_pct,
       DENSE_RANK() OVER (ORDER BY mental_distress_pct DESC) AS national_rank
FROM county_metrics
WHERE mental_distress_pct IS NOT NULL
ORDER BY mental_distress_pct DESC, county_fips
LIMIT 20;

-- Q2: County-level national medians using ROW_NUMBER + COUNT (works in SQLite).
-- A median county rate is not a population-weighted national rate.
WITH ranked AS (
  SELECT mental_distress_pct AS value,
         ROW_NUMBER() OVER (ORDER BY mental_distress_pct) AS rn,
         COUNT(*) OVER () AS n
  FROM county_metrics WHERE mental_distress_pct IS NOT NULL
)
SELECT ROUND(AVG(value),2) AS median_county_mental_distress_pct
FROM ranked WHERE rn IN ((n+1)/2, (n+2)/2);

-- Q3: Three-metric concurrence above each metric's own national county median.
-- 'Above median' is an exploratory descriptive rule, not a clinical threshold.
WITH metrics AS (
  SELECT county_fips, state_abbr, county_name, mental_distress_pct, isolation_pct, lack_support_pct
  FROM county_metrics WHERE available_metrics=3
), unpivot AS (
  SELECT 'mental' AS metric, mental_distress_pct AS val FROM metrics
  UNION ALL SELECT 'isolation', isolation_pct FROM metrics
  UNION ALL SELECT 'support', lack_support_pct FROM metrics
), ordered AS (
  SELECT metric,val,ROW_NUMBER() OVER (PARTITION BY metric ORDER BY val) AS rn,
         COUNT(*) OVER (PARTITION BY metric) AS n
  FROM unpivot
), medians AS (
  SELECT metric,AVG(val) AS median_val FROM ordered
  WHERE rn IN ((n+1)/2,(n+2)/2) GROUP BY metric
)
SELECT m.state_abbr,m.county_name,m.county_fips,
       m.mental_distress_pct,m.isolation_pct,m.lack_support_pct
FROM metrics m
CROSS JOIN (SELECT median_val v FROM medians WHERE metric='mental') t1
CROSS JOIN (SELECT median_val v FROM medians WHERE metric='isolation') t2
CROSS JOIN (SELECT median_val v FROM medians WHERE metric='support') t3
WHERE m.mental_distress_pct>t1.v AND m.isolation_pct>t2.v AND m.lack_support_pct>t3.v
ORDER BY m.mental_distress_pct DESC,m.county_fips
LIMIT 30;

-- Q4: Alabama overview (county-rate averages; unweighted across counties)
SELECT state_abbr, COUNT(*) AS counties_with_all_metrics,
       ROUND(AVG(mental_distress_pct),2) AS avg_county_mental_distress_pct,
       ROUND(AVG(isolation_pct),2) AS avg_county_isolation_pct,
       ROUND(AVG(lack_support_pct),2) AS avg_county_lack_support_pct
FROM county_metrics WHERE state_abbr='AL' AND available_metrics=3
GROUP BY state_abbr;

-- Q5: Number of fully observed counties by state (completeness, not rates)
SELECT state_abbr, COUNT(*) AS counties,
       SUM(CASE WHEN available_metrics=3 THEN 1 ELSE 0 END) AS complete_counties
FROM county_metrics GROUP BY state_abbr ORDER BY state_abbr;
