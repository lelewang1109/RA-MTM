"""Independent dual package source/output closure; never re-certify historical runs."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/dual_reference';TARGET=OUT/'manifest.json'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():
 paths=[]
 for folder in ['src/ramtm','tests','experiments/dual_reference','experiments/gaussian_2d','experiments/synthetic_1d']:
  paths.extend(p for p in (ROOT/folder).rglob('*') if p.suffix in ('.py','.json','.md') and '__pycache__' not in p.parts)
 paths.extend(ROOT/p for p in ['README.md','docs/EXPERIMENT_REPORT.md','docs/DUAL_REFERENCE_REPORT.md','scripts/run_all.py','pyproject.toml'])
 return paths
def outputs():return [p for p in OUT.rglob('*') if p.is_file() and p!=TARGET and p.name!='.DS_Store' and p.suffix!='.npz']
if '--verify' in sys.argv:
 m=json.loads(TARGET.read_text());wrong=[k for k,v in m['sha256'].items() if not (ROOT/k).is_file() or digest(ROOT/k)!=v]
 actual={str(p.relative_to(ROOT)) for p in sources()+outputs()}
 if wrong or actual!=set(m['sha256']):raise SystemExit('Dual manifest mismatch: '+str(wrong))
 if json.loads((OUT/'records/validation.json').read_text())['status']!='complete':raise SystemExit('Dual run incomplete')
 print('PASS dual manifest',len(actual),'files')
else:
 fs=sorted(set(sources()+outputs()))
 TARGET.write_text(json.dumps(dict(schema=1,scope='Dual-reference package only; historical results retain their original provenance',
  local_arrays='Reproducible .npz arrays excluded from portable closure',sha256={str(p.relative_to(ROOT)):digest(p) for p in fs}),indent=2))
 print('Wrote dual manifest',len(fs),'files')
