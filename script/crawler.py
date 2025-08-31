import argparse
from datetime import datetime
from pathlib import Path
from tender import get_records_as_dataframe # See `tender.py` for crawler details
from time import sleep

# Constants
SPACING = 1.5

def query_tenders(q: str, time_range: tuple[int, int] | None = None, verbose: bool = False, dir: str = '../data') -> None:
    current = datetime.now().year - 1911
    log_level = 'verbose' if verbose else 'none'
    outdir = Path(dir)
    outdir.mkdir(parents=True, exist_ok=True)
    t = (88, current)
    if (time_range is None):
        pass
    elif (not isinstance(time_range, tuple)):
        pass
    elif (not len(time_range) == 2):
        pass
    else:
        t = time_range

    for year in range(t[0], t[1] + 1):
        df = get_records_as_dataframe(q, level=log_level, minguo=True, range=(year, year), spacing=SPACING)
        outfile = outdir / f'{q}_{year:03d}.csv'
        df.to_csv(outfile, index=False)
        print(f'{len(df)} record(s) found in {year + 1911}.')
        sleep(SPACING)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Query tenders and save results as CSV.')
    parser.add_argument('query', type=str, help='The query string.')
    parser.add_argument(
        '--time-range', '-t',
        nargs=2,
        type=int,
        metavar=('START', 'END'),
        help='Time range in Minguo (ROC) years. (e.g. -t 88 114)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging.'
    )
    parser.add_argument(
        '--outdir', '-o',
        type=str,
        default='./data',
        help='Output directory for CSV files. (default: ./data)'
    )
    args = parser.parse_args()
    time_range = tuple(args.time_range) if args.time_range else None
    query_tenders(args.query, time_range, args.verbose, args.outdir)