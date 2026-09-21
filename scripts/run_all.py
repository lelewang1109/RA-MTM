"""Clean, fail-fast production run; no old artifacts survive in results/."""
from pathlib import Path
from datetime import datetime,timezone
import os,sys,subprocess,shutil,json
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
backup=ROOT/'archive'/('before_run_'+stamp)
if (ROOT/'results').exists():
    backup.mkdir(parents=True)
    shutil.move(str(ROOT/'results'),str(backup/'results'))
if (ROOT/'data/generated').exists():
    backup.mkdir(parents=True,exist_ok=True)
    shutil.move(str(ROOT/'data/generated'),str(backup/'generated'))
(ROOT/'results').mkdir()
status=ROOT/'results/run_status.json'
status.write_text(json.dumps({'status':'running','started_utc':stamp},indent=2))
commands=['experiments/synthetic_1d/run_experiments.py','experiments/synthetic_1d/verify.py',
          'experiments/synthetic_1d/sensitivity.py','experiments/synthetic_1d/ablation.py',
          'experiments/synthetic_1d/finalize.py','experiments/gaussian_2d/run_experiment.py',
          'experiments/gaussian_2d/validation_study.py','experiments/publication.py']
try:
    for path in commands:
        print('RUN',path,flush=True)
        subprocess.run([sys.executable,path],check=True)
    status.write_text(json.dumps({'status':'complete','started_utc':stamp,'commands':commands},indent=2))
    path='scripts/manifest.py'
    subprocess.run([sys.executable,path],check=True)
except BaseException as error:
    status.write_text(json.dumps({'status':'failed','started_utc':stamp,'stage':path,'error':str(error)},indent=2))
    raise
