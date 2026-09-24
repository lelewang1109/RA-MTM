"""Run RA-MTM dual-axis experiments and reference-point ablations."""
from pathlib import Path
import sys,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from experiments.public import main,ep
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dataset',choices=['ring','era5','both'],default='both')
    args=ap.parse_args()
    for dataset in ['ring','era5'] if args.dataset=='both' else [args.dataset]:
        try:
            main(dataset,reference_kind='extremum',output_root=ROOT/'results')
        except Exception as error:
            ep.save(ROOT/'results'/dataset/'status.json',dict(status='failed',error=str(error)))
            raise
