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
    provenance=ROOT/'results/supplementary/era5/source.json'
    if provenance.exists():files.append(ROOT/json.loads(provenance.read_text())['path'])
    return sorted(set(files))
if '--verify' in sys.argv:
    m=json.loads(path.read_text())
    wrong=[k for k,v in m['sha256'].items() if not (ROOT/k).is_file() or digest(ROOT/k)!=v]
    actual={str(p.relative_to(ROOT)) for p in dependency_files()}
    extra=actual-set(m['sha256'])
    if wrong or extra:raise SystemExit(f'Manifest mismatch: {wrong}; unlisted dependencies: {sorted(extra)}')
    if json.loads((ROOT/'results/run_status.json').read_text())['status']!='complete':
        raise SystemExit('Run is not complete')
    real=ROOT/'results/supplementary/era5'
    if real.exists():
        provenance=json.loads((real/'source.json').read_text())
        if digest(ROOT/provenance['path'])!=provenance['sha256']:
            raise SystemExit('ERA5 input differs from the executed source audit')
        if not provenance.get('code_sha256') or any(digest(ROOT/k)!=v for k,v in provenance['code_sha256'].items()):
            raise SystemExit('ERA5 executed code differs from current implementation')
        for stage in ['main','sensitivity']:
            if not (real/('status_'+stage+'.json')).exists() or json.loads((real/('status_'+stage+'.json')).read_text())['status']!='complete':
                raise SystemExit('ERA5 stage not complete: '+stage)
    print('PASS manifest:',len(m['sha256']),'files')
else:
    files=dependency_files()
    path.write_text(json.dumps({'schema':2,'sha256':{str(p.relative_to(ROOT)):digest(p) for p in files}},indent=2))
    print('WROTE manifest:',len(files),'files')
