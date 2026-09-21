"""Hash the completed source/data/output dependency closure; verify on demand."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'results/manifest.json'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dependency_files():
    files=[]
    for folder in ['src/ramtm','experiments','scripts','data/generated','results','docs','figures_theory']:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=path and p.name!='.DS_Store')
    files.extend(ROOT/n for n in ['pyproject.toml','README.md','references/provenance.json'])
    return sorted(set(files))
if '--verify' in sys.argv:
    m=json.loads(path.read_text())
    wrong=[k for k,v in m['sha256'].items() if not (ROOT/k).is_file() or digest(ROOT/k)!=v]
    actual={str(p.relative_to(ROOT)) for p in dependency_files()}
    extra=actual-set(m['sha256'])
    if wrong or extra:raise SystemExit(f'Manifest mismatch: {wrong}; unlisted dependencies: {sorted(extra)}')
    if json.loads((ROOT/'results/run_status.json').read_text())['status']!='complete':
        raise SystemExit('Run is not complete')
    print('PASS manifest:',len(m['sha256']),'files')
else:
    files=dependency_files()
    path.write_text(json.dumps({'schema':2,'sha256':{str(p.relative_to(ROOT)):digest(p) for p in files}},indent=2))
    print('WROTE manifest:',len(files),'files')
