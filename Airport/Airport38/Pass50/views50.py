"""Pass50: write Pass48/Look48Views.json for Check50.ps1 (PowerShell 5.1 mangles nested arrays).

Usage: python views50.py <out dir> <name,name,...|all>
Views: Pass48/AllViews51.json plus Pass50/Views50.json.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
out, names = sys.argv[1], sys.argv[2].split(',')
views = json.loads((HERE.parent / 'Pass48' / 'AllViews51.json').read_text(encoding='utf-8'))['views']
extra = HERE / 'Views50.json'
if extra.exists():
    views += json.loads(extra.read_text(encoding='utf-8'))['views']
want = views if 'all' in names else [v for v in views if v[0] in names]
missing = sorted(set(names) - {v[0] for v in views} - {'all'})
(HERE.parent / 'Pass48' / 'Look48Views.json').write_text(json.dumps(dict(outdir=out, views=want)), encoding='utf-8')
print('views %d%s' % (len(want), ('  unknown: ' + ','.join(missing)) if missing else ''))
