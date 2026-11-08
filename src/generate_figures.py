"""Generate accessible SVG charts from the *local* CDC SQLite database.

Dependencies: Python 3.10+ standard library. No network or placeholder records.
Run: python3 src/generate_figures.py
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from statistics import correlation
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'woke_rooted.sqlite'
OUT = ROOT / 'figures'


def colormap(value: float) -> str:
    # Pale warm for weaker correlations, deep teal for stronger correlations.
    s = max(0, min(1, abs(value)))
    lo = (231, 239, 239)
    hi = (12, 93, 111)
    return '#%02x%02x%02x' % tuple(round(a*(1-s)+b*s) for a,b in zip(lo,hi))


def heatmap(vals: list[list[float]], n: int) -> str:
    labels = ['Mental distress', 'Social isolation', 'Lack of support']
    pieces = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="940" height="650" viewBox="0 0 940 650" role="img" aria-label="Correlation matrix of frequent mental distress, social isolation and lack of social support, from county-level CDC PLACES estimates">',
        '<rect width="940" height="650" fill="#101a25"/>',
        '<text x="58" y="60" fill="#dfb967" font-size="18" font-family="Arial, sans-serif" letter-spacing="2">F+M LABS / WOKE &amp; ROOTED</text>',
        '<text x="58" y="107" fill="#ffffff" font-size="32" font-weight="700" font-family="Arial, sans-serif">The Geography of Being Unwell</text>',
        f'<text x="58" y="142" fill="#abc0c9" font-size="17" font-family="Arial, sans-serif">County-level Pearson correlations · n = {n:,} complete records</text>',
    ]
    x0, y0, tile, gap = 390, 188, 140, 8
    for j, label in enumerate(labels):
        pieces.append(f'<text x="{x0+j*(tile+gap)+tile/2}" y="178" font-size="13" fill="#dae9ef" text-anchor="middle" font-family="Arial, sans-serif">{escape(label)}</text>')
    for i, label in enumerate(labels):
        pieces.append(f'<text x="360" y="{y0+i*(tile+gap)+tile/2}" font-size="16" fill="#d6e4ea" text-anchor="end" dominant-baseline="middle" font-family="Arial, sans-serif">{escape(label)}</text>')
        for j in range(3):
            val=vals[i][j]
            x=x0+j*(tile+gap); y=y0+i*(tile+gap)
            pieces.append(f'<rect x="{x}" y="{y}" width="{tile}" height="{tile}" rx="10" fill="{colormap(val)}"/>')
            pieces.append(f'<text x="{x+tile/2}" y="{y+tile/2}" text-anchor="middle" dominant-baseline="middle" fill="white" font-family="Arial, sans-serif" font-weight="700" font-size="25">{val:+.4f}</text>')
    pieces.append('<text x="58" y="618" fill="#a5bdc8" font-family="Arial, sans-serif" font-size="14">Modeled county estimates · descriptive only · correlation is not causation</text></svg>')
    return '\n'.join(pieces)


def scatter(rows: list[tuple[float,float]], r: float) -> str:
    w,h=940,630
    x0,y0,x1,y1=95,140,875,520
    xs=[x for x,_ in rows]; ys=[y for _,y in rows]
    xmin,xmax=min(xs),max(xs); ymin,ymax=min(ys),max(ys)
    # Expand slightly so circles do not hit axes.
    xmin=max(0,xmin-1); xmax=min(100,xmax+1)
    ymin=max(0,ymin-1); ymax=min(100,ymax+1)
    tx=lambda x: x0+(x-xmin)/(xmax-xmin)*(x1-x0)
    ty=lambda y: y1-(y-ymin)/(ymax-ymin)*(y1-y0)
    s=['<svg xmlns="http://www.w3.org/2000/svg" width="940" height="630" viewBox="0 0 940 630" role="img" aria-label="Scatterplot of county social isolation percentage versus frequent mental distress percentage">',
       f'<rect width="{w}" height="{h}" fill="#101a25"/>',
       '<text x="58" y="53" fill="#dfb967" font-size="18" font-family="Arial, sans-serif">WOKE &amp; ROOTED · PUBLIC HEALTH ANALYTICS</text>',
       '<text x="58" y="96" fill="white" font-size="30" font-weight="700" font-family="Arial, sans-serif">Isolation and mental distress</text>',
       f'<text x="58" y="123" fill="#b6cbd5" font-size="16" font-family="Arial, sans-serif">{len(rows):,} complete county areas · Pearson r = {r:+.4f}</text>',
       f'<path d="M{x0} {y0} V{y1} H{x1}" fill="none" stroke="#8da6b4" stroke-width="2"/>']
    for i in range(6):
        frac=i/5
        xv=xmin+(xmax-xmin)*frac; yv=ymin+(ymax-ymin)*frac
        xx=tx(xv); yy=ty(yv)
        s.append(f'<line x1="{xx:.1f}" y1="{y0}" x2="{xx:.1f}" y2="{y1}" stroke="#314453" stroke-width="1"/>')
        s.append(f'<line x1="{x0}" y1="{yy:.1f}" x2="{x1}" y2="{yy:.1f}" stroke="#314453" stroke-width="1"/>')
        s.append(f'<text x="{xx:.1f}" y="{y1+26}" fill="#b6cbd5" text-anchor="middle" font-size="13" font-family="Arial, sans-serif">{xv:.0f}</text>')
        s.append(f'<text x="{x0-15}" y="{yy+5:.1f}" fill="#b6cbd5" text-anchor="end" font-size="13" font-family="Arial, sans-serif">{yv:.0f}</text>')
    for x,y in rows:
        s.append(f'<circle cx="{tx(x):.1f}" cy="{ty(y):.1f}" r="2.4" fill="#67c6d3" fill-opacity="0.32"/>')
    s += [f'<text x="{(x0+x1)/2}" y="585" fill="white" font-size="16" text-anchor="middle" font-family="Arial, sans-serif">Social isolation estimate (%)</text>',
          '<text transform="translate(30 330) rotate(-90)" fill="white" font-size="16" text-anchor="middle" font-family="Arial, sans-serif">Frequent mental distress estimate (%)</text>',
          '<text x="875" y="614" fill="#b6cbd5" font-size="12" text-anchor="end" font-family="Arial, sans-serif">CDC PLACES 2024 release · not causal</text></svg>']
    return '\n'.join(s)


def main() -> None:
    if not DB.exists():
        raise SystemExit(f'No real-data database found: {DB}\nFirst run: python3 src/pipeline.py --download && python3 src/pipeline.py --build')
    with sqlite3.connect(DB) as conn:
        rows=conn.execute('''SELECT mental_distress_pct, isolation_pct, lack_support_pct
          FROM county_metrics WHERE mental_distress_pct IS NOT NULL
          AND isolation_pct IS NOT NULL AND lack_support_pct IS NOT NULL''').fetchall()
    if len(rows)<100:
        raise SystemExit('Refusing to publish a figure from a tiny or fixture-only sample')
    m,i,s=tuple(zip(*rows))
    rmi=correlation(m,i); rms=correlation(m,s); ris=correlation(i,s)
    matrix=[[1,rmi,rms],[rmi,1,ris],[rms,ris,1]]
    OUT.mkdir(exist_ok=True)
    (OUT/'correlation_heatmap.svg').write_text(heatmap(matrix,len(rows)),encoding='utf-8')
    (OUT/'scatter_isolation_distress.svg').write_text(scatter(list(zip(i,m)),rmi),encoding='utf-8')
    print(f'Generated 2 SVG charts using {len(rows):,} rows; Pearson r: {rmi:+.4f}, {rms:+.4f}, {ris:+.4f}')

if __name__=='__main__': main()
