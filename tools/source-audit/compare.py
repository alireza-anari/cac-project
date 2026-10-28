"""Reproduce the known v3.40 source/API diff; never infer missing baseline code."""
import argparse
import difflib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

p = argparse.ArgumentParser()
p.add_argument('--project-zip', type=Path, required=True)
p.add_argument('--refs', type=Path, required=True)
p.add_argument('--output-dir', type=Path, required=True)
a = p.parse_args()
refs = json.loads(a.refs.read_text())
sha = lambda b: hashlib.sha256(b).hexdigest()
rows, patch = [], []
with zipfile.ZipFile(a.project_zip) as outer:
    data = outer.read('CAC-Project-Sources-v3.42/references/CAC-v3.40-standalone-onboarding.zip')
assert sha(data) == 'e685e8872e953aff66daeeb6c551332f0dc6a178269f4041382c2f84c8e1118e'
with zipfile.ZipFile(io.BytesIO(data)) as z:
    for name in z.namelist():
        rel = name.removeprefix('cac-v3.40-onboarding-module/')
        if not (rel.endswith('.py') or rel == 'integration/openapi-onboarding-addendum.yaml'):
            continue
        old = z.read(name)
        archived = subprocess.check_output(['git', 'show', refs['archive/v3.40-unpatched-reference'] + ':reference/v3.40-unpatched/' + rel])
        current = subprocess.check_output(['git', 'show', refs['main'] + ':standalone/onboarding/' + rel])
        rows.append({'path': rel, 'original_sha256': sha(old), 'historical_sha256': sha(archived),
                     'historical_exact': old == archived, 'current_sha256': sha(current), 'current_exact': old == current})
        patch.extend(difflib.unified_diff(old.decode().splitlines(True), current.decode().splitlines(True),
                                         fromfile='v3.40/' + rel, tofile='main-standalone/' + rel))
rel = 'tests/test_revocation.py'
current = subprocess.check_output(['git', 'show', refs['main'] + ':standalone/onboarding/' + rel])
patch.extend(difflib.unified_diff([], current.decode().splitlines(True), fromfile='/dev/null', tofile='main-standalone/' + rel))
rows.append({'path': rel, 'status': 'added after v3.40', 'current_sha256': sha(current)})
(a.output_dir / 'existing-source-comparison.json').write_text(json.dumps(rows, indent=2) + '\n')
(a.output_dir / 'v340-to-current-standalone.patch').write_text(''.join(patch))
assert len(rows) == 8 and all(r['historical_exact'] for r in rows[:-1])
print('Seven historical files byte-identical; existing standalone source/API/test diff written. No missing-version comparison claimed.')
