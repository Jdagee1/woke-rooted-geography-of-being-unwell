"""CDC PLACES 2024 -> validated SQLite model -> reproducible county report.

No third-party dependencies. Python 3.10+.
"""
import argparse
import csv
import hashlib
import io
import re
import sqlite3
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
SOURCE_URL = 'https://data.cdc.gov/api/v3/views/fu4u-a9bh/export.csv?accessType=DOWNLOAD'
MEASURES = ('MHLTH', 'ISOLATION', 'EMOTIONSPT')


def clean_header(name):
    return re.sub(r'[^a-z0-9]', '', (name or '').lower())


def get(row, key, default=''):
    return row.get(clean_header(key), default)


def download(destination=DATA / 'places_county_2024.csv'):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix('.download')
    try:
        with urllib.request.urlopen(urllib.request.Request(SOURCE_URL, headers={'User-Agent':'WokeRootedPortfolio/1.0'}), timeout=90) as response, temp.open('wb') as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
        if temp.stat().st_size < 1000:
            raise ValueError('CDC download is unexpectedly small')
        temp.replace(destination)
    finally:
        temp.unlink(missing_ok=True)
    print(f'Downloaded official CDC file: {destination} ({destination.stat().st_size:,} bytes)')


def parse_rows(path, minimum_counties=100):
    counties = {}
    observations = {}
    with Path(path).open('r', encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        headings = {clean_header(h) for h in (reader.fieldnames or [])}
        required = {'locationid','stateabbr','locationname','measureid','datavalue'}
        if not required <= headings:
            raise ValueError('Missing CDC CSV fields: ' + ', '.join(sorted(required - headings)))
        type_available = 'datavaluetype' in headings
        matching = 0
        for idx, original in enumerate(reader, 2):
            row = {clean_header(k): (v or '').strip() for k,v in original.items() if k}
            measure = get(row,'MeasureId').upper()
            if measure not in MEASURES:
                continue
            if type_available:
                t = get(row, 'Data_Value_Type').lower()
                # Keep crude estimates only; avoid double-counting age-adjusted rows.
                if t and ('crude' not in t or 'age-adjusted' in t or 'age adjusted' in t):
                    continue
            # Exclude US national summary records
            if get(row,'StateAbbr').upper() == 'US':
                continue
            county_id = get(row,'LocationID').zfill(5)
            state = get(row,'StateAbbr').upper()
            name = get(row,'LocationName')
            state_name = get(row,'StateDesc')
            if not (re.fullmatch(r'\d{5}',county_id) and re.fullmatch(r'[A-Z]{2}',state) and name):
                raise ValueError(f'Invalid county ID/state/name at CSV row {idx}')
            descriptor=(county_id,state,state_name,name)
            if county_id in counties:
                old = counties[county_id]
                if old[1] != state or old[3] != name:
                    raise ValueError(f'Contradictory county descriptor at CSV row {idx}')
            else:
                counties[county_id]=descriptor
            raw=get(row,'Data_Value')
            if raw in ('','NA','N/A','null','NULL'):
                continue  # Explicit missingness is preserved in county_metrics view.
            try:
                pct=float(raw)
            except ValueError:
                raise ValueError(f'Non-numeric prevalence at CSV row {idx}: {raw}') from None
            if not 0 <= pct <= 100:
                raise ValueError(f'Out-of-range prevalence at CSV row {idx}: {pct}')
            key=(county_id,measure)
            if key in observations:
                raise ValueError(f'Duplicate county/measure observation at CSV row {idx}: {key}')
            observations[key]=(county_id,measure,pct)
            matching+=1
    if len(counties)<minimum_counties:
        raise ValueError(f'Too few counties ({len(counties)}), expected at least {minimum_counties}')
    if set(m for _,m in observations)!=set(MEASURES):
        raise ValueError('One or more required CDC mental/social measures are missing')
    return list(counties.values()),list(observations.values())


def build(source=DATA/'places_county_2024.csv', db=DATA/'woke_rooted.sqlite', minimum_counties=100):
    counties, observations = parse_rows(source,minimum_counties)
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as conn:
        conn.executescript((ROOT/'sql/01_schema.sql').read_text())
        conn.executemany('INSERT INTO counties VALUES (?,?,?,?)',counties)
        conn.executemany('INSERT INTO observations VALUES (?,?,?)',observations)
        failures=conn.execute('SELECT COUNT(*) FROM observations WHERE prevalence_pct NOT BETWEEN 0 AND 100').fetchone()[0]
        if failures:
            raise AssertionError('Out-of-range prevalence observations detected')
        n=conn.execute('SELECT COUNT(*) FROM county_metrics').fetchone()[0]
        if n!=len(counties):
            raise AssertionError('Loss of counties during pivot')
    sha=hashlib.sha256(Path(source).read_bytes()).hexdigest()
    print(f'Built SQLite: {len(counties):,} counties; {len(observations):,} observed measures')
    print(f'Source SHA-256: {sha}')
    return len(counties),len(observations)


def report(db=DATA/'woke_rooted.sqlite', output=DATA/'report.csv'):
    output.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(db) as conn:
        conn.row_factory=sqlite3.Row
        query='''WITH complete AS (
            SELECT * FROM county_metrics WHERE available_metrics=3
        ), ranked AS (
            SELECT *, DENSE_RANK() OVER (ORDER BY mental_distress_pct DESC) AS mental_rank
            FROM complete
        )
        SELECT county_fips,state_abbr,county_name,mental_distress_pct,isolation_pct,
               lack_support_pct,mental_rank FROM ranked
        ORDER BY mental_rank,county_fips'''
        rows=conn.execute(query).fetchall()
        if not rows:
            raise ValueError('No counties with complete three-measure observations')
        with output.open('w',newline='',encoding='utf-8') as fh:
            writer=csv.writer(fh)
            writer.writerow(rows[0].keys())
            writer.writerows([tuple(row) for row in rows])
        counts=conn.execute('''SELECT COUNT(*) total, SUM(available_metrics=3) complete,
                SUM(mental_distress_pct IS NULL) missing_mental,
                SUM(isolation_pct IS NULL) missing_isolation,
                SUM(lack_support_pct IS NULL) missing_support
                FROM county_metrics''').fetchone()
        print('COUNTY DATA COVERAGE:',dict(counts))
        print(f'Wrote {len(rows):,} complete county observations to {output}')
        print('Run sql/02_analysis.sql with sqlite3 / DB Browser for the full SQL portfolio.')
    return len(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download',action='store_true')
    parser.add_argument('--build',action='store_true')
    parser.add_argument('--report',action='store_true')
    parser.add_argument('--csv',type=Path,default=DATA/'places_county_2024.csv')
    parser.add_argument('--db',type=Path,default=DATA/'woke_rooted.sqlite')
    args=parser.parse_args()
    if not (args.download or args.build or args.report):
        parser.print_help(); return
    if args.download: download(args.csv)
    if args.build: build(args.csv,args.db)
    if args.report: report(args.db)

if __name__=='__main__': main()
