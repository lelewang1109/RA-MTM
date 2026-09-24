"""Portable entry point for the RA-MTM public-data experiments."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=['ring', 'era5', 'both'])
    parser.add_argument('--verify', action='store_true', help='Verify published hashes without raw data or rerunning')
    parser.add_argument('--audit', action='store_true', help='Audit numerical outputs; requires regenerated/local map arrays')
    args = parser.parse_args()
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'src') + os.pathsep + str(ROOT)

    def run(*command):
        subprocess.run([sys.executable, *command], cwd=ROOT, env=env, check=True)

    if args.verify or not (args.dataset or args.audit):
        run('scripts/verify_results.py', '--verify')
        return
    dataset = args.dataset or 'both'
    if not args.audit:
        if dataset in ('era5', 'both'):
            source = ROOT / 'data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114.nc'
            if not source.is_file():
                parser.error('ERA5 input missing: ' + str(source) + '; see data/README.md, or use --dataset ring')
        run('-m', 'unittest', 'discover', '-s', 'tests', '-v')
        run('experiments/run.py', '--dataset', dataset)
    run('scripts/verify_results.py', '--dataset', dataset)


if __name__ == '__main__':
    main()
