"""Canonical public-data XY workflow. Historical centroid runs are untouched."""
from pathlib import Path
import sys,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from experiments.dual_reference.public_data import main,ep
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dataset',choices=['ring','era5','both'],default='both')
    args=ap.parse_args()
    for dataset in ['ring','era5'] if args.dataset=='both' else [args.dataset]:
        try:
            main(dataset,reference_kind='extremum',output_root=ROOT/'results/xy')
        except Exception as error:
            ep.save(ROOT/'results/xy'/dataset/'status.json',dict(status='failed',error=str(error)))
            raise
