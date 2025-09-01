import json
import pandas as pd
from pathlib import Path

def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    print('Start aggregating data...')
    result = (
        df.groupby(['title', 'authority'])
          .apply(lambda g: pd.Series({
              'title': g.name[0],
              'authority': g.name[1],
              'tenders': g[['date', 'url']].to_dict(orient='records')
          }))
          .reset_index(drop=True)
    )
    print('Finished aggregating data.')
    return result

def get_all_csv_files(dir: str) -> list[Path]:
    dir_path = Path(dir)
    return list(dir_path.rglob(f'*.csv'))

def load_csvs(dir: str) -> pd.DataFrame:
    df = pd.DataFrame(columns=['title', 'authority', 'date', 'url'])
    paths = get_all_csv_files(dir)
    for path in paths:
        sub_df = pd.read_csv(path)
        sub_df['title'] = sub_df['title'].astype(str)
        sub_df['authority'] = sub_df['authority'].astype(str)
        sub_df['date'] = pd.to_datetime(sub_df['date'])
        sub_df['url'] = sub_df['url'].astype(str)
        df = pd.concat([df, sub_df], axis=0, ignore_index=True)
    print(f'Loaded {len(paths)} CSV file(s).')
    return df

def save_data(df: pd.DataFrame, dir: str) -> None:
    records = df.to_dict(orient='records')

    for record in records:
        record['tenders'].sort(key=lambda t: pd.to_datetime(t['date']))
        for tender in record['tenders']:
            if isinstance(tender['date'], (pd.Timestamp,)):
                tender['date'] = tender['date'].strftime('%Y-%m-%d')

    with open(dir, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        print(f'Aggregated data was saved to {dir}.')

if __name__ == '__main__':
    p = load_csvs('./data')
    f = filter_data(p)
    save_data(f, './data/agg.json')