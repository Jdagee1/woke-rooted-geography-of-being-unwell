PRAGMA foreign_keys = ON;
DROP VIEW IF EXISTS county_metrics;
DROP TABLE IF EXISTS observations;
DROP TABLE IF EXISTS counties;
CREATE TABLE counties (
    county_fips TEXT PRIMARY KEY,
    state_abbr TEXT NOT NULL,
    state_name TEXT,
    county_name TEXT NOT NULL
);
CREATE TABLE observations (
    county_fips TEXT NOT NULL,
    measure_id TEXT NOT NULL CHECK(measure_id IN ('MHLTH','ISOLATION','EMOTIONSPT')),
    prevalence_pct REAL NOT NULL CHECK(prevalence_pct BETWEEN 0 AND 100),
    PRIMARY KEY (county_fips, measure_id),
    FOREIGN KEY (county_fips) REFERENCES counties(county_fips)
);
CREATE VIEW county_metrics AS
SELECT c.county_fips,c.state_abbr,c.state_name,c.county_name,
       MAX(CASE WHEN o.measure_id='MHLTH' THEN o.prevalence_pct END) AS mental_distress_pct,
       MAX(CASE WHEN o.measure_id='ISOLATION' THEN o.prevalence_pct END) AS isolation_pct,
       MAX(CASE WHEN o.measure_id='EMOTIONSPT' THEN o.prevalence_pct END) AS lack_support_pct,
       COUNT(o.measure_id) AS available_metrics
FROM counties c LEFT JOIN observations o ON o.county_fips=c.county_fips
GROUP BY c.county_fips,c.state_abbr,c.state_name,c.county_name;
