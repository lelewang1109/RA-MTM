"""Clean, fail-fast production run; no old artifacts survive in results/."""
from pathlib import Path
from datetime import datetime,timezone
import os,sys,subprocess,shutil,json
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
backup=ROOT/'archive'/('before_run_'+stamp)
# Archive only legacy-owned outputs; never move current XY or centroid evidence.
for name in ['main','auxiliary','ablation','sensitivity','validity','supplementary','manifest.json','run_status.json','synthetic_1d','gaussian_2d']:
    old=ROOT/'results'/name
    if old.exists():
        (backup/'results').mkdir(parents=True,exist_ok=True)
        shutil.move(str(old),str(backup/'results'/name))
if (ROOT/'data/generated').exists():
    backup.mkdir(parents=True,exist_ok=True)
    shutil.move(str(ROOT/'data/generated'),str(backup/'generated'))
(ROOT/'results').mkdir(exist_ok=True)
status=ROOT/'results/run_status.json'
status.write_text(json.dumps({'status':'running','started_utc':stamp},indent=2))
commands=['experiments/synthetic_1d/run_experiments.py','experiments/synthetic_1d/verify.py',
          'experiments/synthetic_1d/sensitivity.py','experiments/synthetic_1d/ablation.py',
          'experiments/synthetic_1d/finalize.py','experiments/gaussian_2d/run_experiment.py',
          'experiments/gaussian_2d/validation_study.py','experiments/focused_study.py','experiments/publication.py']
real_source=ROOT/'data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114.nc'
if real_source.exists():
    commands+=['experiments/real_era5/verify.py','experiments/real_era5/run_experiment.py','experiments/real_era5/finalize.py','experiments/real_era5/paper_figure.py']
commands+=['experiments/ring/run_experiment.py','experiments/ring/verify.py',
    'tests/test_dual_reference.py','experiments/dual_reference/run_experiment.py',
    'experiments/dual_reference/exact_mechanisms.py','experiments/dual_reference/verify.py','experiments/dual_reference/figures.py',
    'experiments/dual_reference/finalize.py','experiments/dual_reference/manifest.py']
try:
    for path in commands:
        print('RUN',path,flush=True)
        subprocess.run([sys.executable,path],check=True)
    status.write_text(json.dumps({'status':'complete','started_utc':stamp,'commands':commands,
        'era5':'included' if real_source.exists() else 'not run: external input absent'},indent=2))
    path='scripts/manifest.py'
    subprocess.run([sys.executable,path],check=True)
except BaseException as error:
    status.write_text(json.dumps({'status':'failed','started_utc':stamp,'stage':path,'error':str(error)},indent=2))
    raise
