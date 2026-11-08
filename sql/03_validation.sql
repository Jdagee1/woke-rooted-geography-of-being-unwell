-- Each query should return zero rows, except the summary at the end.
SELECT county_fips,measure_id,COUNT(*) AS n FROM observations
GROUP BY county_fips,measure_id HAVING COUNT(*)>1;
SELECT county_fips,measure_id,prevalence_pct FROM observations
WHERE prevalence_pct<0 OR prevalence_pct>100 OR prevalence_pct IS NULL;
SELECT o.county_fips FROM observations o LEFT JOIN counties c USING(county_fips)
WHERE c.county_fips IS NULL;
-- Summary: missingness must be disclosed rather than silently ignored.
SELECT COUNT(*) AS counties, SUM(available_metrics=3) AS fully_observed_counties,
       SUM(mental_distress_pct IS NULL) AS missing_mental,
       SUM(isolation_pct IS NULL) AS missing_isolation,
       SUM(lack_support_pct IS NULL) AS missing_support
FROM county_metrics;
