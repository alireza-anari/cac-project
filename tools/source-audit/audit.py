"""Read-only bounded provenance inventory; does not extract or execute archive code."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ap = argparse.ArgumentParser()
ap.add_argument('--workspace', type=Path, required=True)
ap.add_argument('--refs', type=Path, required=True, help='Frozen branch-name to commit map')
ap.add_argument('--output', type=Path, required=True)
a = ap.parse_args()
sha = lambda b: hashlib.sha256(b).hexdigest()
def git(*args):
    return subprocess.check_output(['git', *args])
refs = json.loads(a.refs.read_text())
commits = sorted(set(git('rev-list', *refs.values()).decode().splitlines()))
paths = {}
blobs = {}
for commit in commits:
    for entry in git('ls-tree', '-rz', commit).split(b'\0'):
        if not entry:
            continue
        meta, name = entry.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        name = name.decode()
        paths.setdefault(name, set()).add(oid)
        if kind == 'blob':
            blobs.setdefault(oid, {'paths': set(), 'commit_example': commit})['paths'].add(name)
pattern = re.compile(rb'v?3[._-]?3[789]|APR-036|SOURCE-001', re.I)
hits = []
for oid, info in blobs.items():
    data = git('cat-file', 'blob', oid)
    matches = [i for i, line in enumerate(data.splitlines(), 1) if pattern.search(line)]
    if matches:
        hits.append({'blob': oid, 'sha256': sha(data), 'paths': sorted(info['paths']),
                     'commit_example': info['commit_example'], 'matching_lines': matches})
archives = {}
def inspect_zip(data, location, depth=0):
    digest = sha(data)
    if digest in archives:
        archives[digest]['locations'].append(location)
        return
    if depth > 6 or len(data) > 64 * 1024 * 1024:
        raise ValueError('Archive safety limit exceeded')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members = z.infolist()
        if sum(m.file_size for m in members) > 128 * 1024 * 1024:
            raise ValueError('Uncompressed safety limit exceeded')
        names = [m.filename for m in members if not m.is_dir()]
        if len(set(names)) != len(names):
            raise ValueError('Duplicate archive member')
        if any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts for n in names):
            raise ValueError('Unsafe archive member path')
        assert z.testzip() is None, 'CRC failure'
        record = {'sha256': digest, 'size': len(data), 'locations': [location], 'crc': 'PASS',
                  'members': names, 'manifests': [], 'validation_reports': []}
        archives[digest] = record
        for name in names:
            b = z.read(name)
            if name.lower().endswith('.sha256'):
                entries = []
                for line in b.decode().splitlines():
                    if not line.strip():
                        continue
                    expected, relative = line.split(None, 1)
                    target = str(PurePosixPath(name).parent / relative.lstrip('* '))
                    actual = sha(z.read(target)) if target in names else None
                    entries.append({'path': target, 'expected': expected, 'actual': actual, 'match': actual == expected})
                record['manifests'].append({'path': name, 'sha256': sha(b), 'checked_entries': len(entries), 'failures': [e for e in entries if not e['match']],
                                            'pass': all(e['match'] for e in entries)})
            if name.endswith(('VALIDATION_REPORT.json', 'VALIDATION_AND_SOURCE_STATUS.json')):
                record['validation_reports'].append({'path': name, 'sha256': sha(b), 'content': json.loads(b)})
            if name.lower().endswith('.zip'):
                inspect_zip(b, location + '!' + name, depth + 1)
exclude = {'.git', 'node_modules', '.venv', 'venv', 's0-05-venv', 'clean-venv', '__pycache__'}
workspace_files = []
for directory, dirs, files in os.walk(a.workspace):
    dirs[:] = sorted(d for d in dirs if d not in exclude)
    for name in sorted(files):
        p = Path(directory) / name
        relative = p.relative_to(a.workspace).as_posix()
        if p.is_symlink():
            continue
        if name.lower().endswith('.zip'):
            data = p.read_bytes()
            workspace_files.append({'path': relative, 'size': len(data), 'sha256': sha(data)})
            inspect_zip(data, relative)
        elif re.search(r'v?3[._-]?3[789]|000[12]_.*\.py|AGENTS\.md', name, re.I):
            workspace_files.append({'path': relative, 'size': p.stat().st_size,
                                    'sha256': sha(p.read_bytes()), 'type': 'filename-lead'})
log = git('log', '--format=%H%x09%aI%x09%an%x09%s', *refs.values()).decode().splitlines()
result = {'refs': refs, 'git_shallow': git('rev-parse','--is-shallow-repository').decode().strip(),
          'reachable_commit_count': len(commits), 'commits': log, 'unique_blob_count': len(blobs),
          'history_paths': {p: sorted(v) for p,v in sorted(paths.items())}, 'text_hits': hits,
          'workspace_exclusions': sorted(exclude), 'workspace_files': workspace_files,
          'archives_by_sha256': archives,
          'scope': 'Current accessible refs and workspace only; hashes do not authenticate APR-036.'}
a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
failures = sum(not m['pass'] for r in archives.values() for m in r['manifests'])
print(json.dumps({'commits':len(commits),'blobs':len(blobs),'paths':len(paths),'text_hit_blobs':len(hits),
                  'workspace_archives':sum(p['path'].endswith('.zip') for p in workspace_files),
                  'unique_archives':len(archives),'manifest_failures':failures}))
raise SystemExit(bool(failures))
