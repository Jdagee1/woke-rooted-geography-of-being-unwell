"""Fictional fixture tests. These numbers are never reported as CDC findings."""
import csv
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pipeline

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.csv=self.root/'fictional_fixture.csv'
        self.db=self.root/'fixture.sqlite'
        with self.csv.open('w',newline='') as fh:
            w=csv.writer(fh)
            w.writerow(['LocationID','StateAbbr','StateDesc','LocationName','MeasureId','Data_Value','Data_Value_Type'])
            for i in range(5):
                for m,j in [('MHLTH',0),('ISOLATION',1),('EMOTIONSPT',2)]:
                    w.writerow([f'0100{i}','AL','Alabama',f'Fictional County {i}',m,10+i+j,'Crude prevalence'])

    def test_valid_build_and_report(self):
        n,obs=pipeline.build(self.csv,self.db,minimum_counties=5)
        self.assertEqual((n,obs),(5,15))
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM county_metrics WHERE available_metrics=3').fetchone()[0],5)
            self.assertEqual(conn.execute('SELECT mental_distress_pct FROM county_metrics WHERE county_fips=?',('01000',)).fetchone()[0],10.0)
        self.assertEqual(pipeline.report(self.db,self.root/'report.csv'),5)

    def test_national_summary_excluded_without_dropping_counties(self):
        # CDC exports may contain nationwide records with StateAbbr=US.
        with self.csv.open('a') as fh:
            fh.write('59,US,United States,,ISOLATION,32.0,Crude prevalence\n')
        counties, observations = pipeline.parse_rows(self.csv, minimum_counties=5)
        self.assertEqual(len(counties), 5)
        self.assertEqual(len(observations), 15)

    def test_duplicate_rejected(self):
        with self.csv.open('a') as fh:
            fh.write('01000,AL,Alabama,Fictional County 0,MHLTH,99,Crude prevalence\n')
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            pipeline.parse_rows(self.csv,minimum_counties=5)

    def test_out_of_range_rejected(self):
        content=self.csv.read_text().replace('MHLTH,10,Crude','MHLTH,110,Crude')
        self.csv.write_text(content)
        with self.assertRaisesRegex(ValueError,'Out-of-range'):
            pipeline.parse_rows(self.csv,minimum_counties=5)

    def test_counties_preserve_leading_zero(self):
        counties,_=pipeline.parse_rows(self.csv,minimum_counties=5)
        self.assertEqual(counties[0][0],'01000')

if __name__=='__main__': unittest.main()
