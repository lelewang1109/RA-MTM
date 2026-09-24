"""Single current entry point; updates only the chosen evidence package."""
from pathlib import Path
import argparse,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def run(*args):subprocess.run([sys.executable,*args],cwd=ROOT,check=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dataset',choices=['ring','era5','both'],default='both')
    ap.add_argument('--suite',choices=['public','mechanisms'],default='public')
    args=ap.parse_args()
    run('-m','unittest','discover','-s','tests','-v')
    if args.suite=='public':
        run('experiments/xy/run.py','--dataset',args.dataset)
        run('experiments/xy/verify.py','--dataset',args.dataset)
    else:
        for step in ['run_experiment','exact_mechanisms','verify','figures','finalize','manifest']:
            run('experiments/dual_reference/'+step+'.py')
