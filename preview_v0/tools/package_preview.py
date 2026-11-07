"""Build a deterministic SOURCE-only ZIP. Run after evidence is finalized."""
import hashlib
from pathlib import Path
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
excluded = {'.local_state', '.venv', '__pycache__', '.git', 'dist'}
allowed = {'.py', '.html', '.css', '.js', '.md', '.txt', '.json'}
output = Path(sys.argv[1]).resolve()
entries = {}
for path in sorted(root.rglob('*')):
    relative = path.relative_to(root)
    if not path.is_file() or path.is_symlink() or any(p in excluded for p in relative.parts):
        continue
    if path.name.startswith('.env') or (path.suffix not in allowed and path.name != '.gitignore'):
        continue
    if path.resolve() == output:
        continue
    entries['preview_v0/'+relative.as_posix()] = path.read_bytes()
manifest = '\n'.join(hashlib.sha256(data).hexdigest()+'  '+name for name, data in entries.items())+'\n'
entries['preview_v0/MANIFEST.sha256'] = manifest.encode()
output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for name, data in entries.items():
        info = zipfile.ZipInfo(name, (2026, 11, 7, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, data)
print(output)
print('SHA-256:', hashlib.sha256(output.read_bytes()).hexdigest())
print('Source entries:', len(entries))
