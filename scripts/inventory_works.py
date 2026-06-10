'''
Created on Tue Jun  9 2026

inventory raw boundary pages before feature engineering

examples:
python scripts/inventory_works.py
python scripts/inventory_works.py --start-year 1933 --end-year 2025

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from tqdm import tqdm

from kairos.data.config import (
    BOUNDARY_LAYERS,
    END_YEAR,
    MODEL_START_YEAR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    START_YEAR,
    BoundaryLayer,
)


#%% settings
DEFAULT_OUTPUT = PROCESSED_DATA_DIR / 'inventory_works.csv'
PAGE_SIZE = 100  # same page size used by fetch_boundary.py

FIELDNAMES = (
    'layer',
    'fetch_mode',
    'year',
    'in_model_window',
    'work_pages',
    'work_records',
    'work_exhausted',
    'abstract_pages',
    'abstract_records',
    'abstracts_seen',
    'abstract_pull_complete',
    'count_saved',
    'count_works',
)


#%% command line
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start-year', type=int, default=START_YEAR)
    parser.add_argument('--end-year', type=int, default=END_YEAR)
    parser.add_argument('--layer', action='append')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def selected_layers(layer_keys: list[str] | None) -> list[BoundaryLayer]:
    if not layer_keys:
        return list(BOUNDARY_LAYERS)

    layers = {layer.key: layer for layer in BOUNDARY_LAYERS}
    missing = [
        layer_key for layer_key in layer_keys
        if layer_key not in layers
    ]
    if missing:
        known_layers = ', '.join(layers)
        raise SystemExit(f'unknown layer(s) {missing}; choose from: {known_layers}')
    return [layers[layer_key] for layer_key in layer_keys]


#%% paths
def work_dir(layer: BoundaryLayer, year: int) -> Path:
    return RAW_DATA_DIR / 'works' / layer.key / str(year)


def abstract_dir(layer: BoundaryLayer, year: int) -> Path:
    return RAW_DATA_DIR / 'abstracts' / layer.key / str(year)


def count_path(layer: BoundaryLayer, year: int) -> Path:
    return RAW_DATA_DIR / 'counts' / layer.key / f'{year}.json'


def json_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob('*.json'))


#%% JSON summaries
def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except:
        return None


def saved_record_count(page_count: int, last_page_count: int) -> int:
    if page_count == 0:
        return 0

    # full OA pages should have PAGE_SIZE records, so only the tail needs reading
    return ((page_count - 1) * PAGE_SIZE) + last_page_count


def abstract_count(payload: dict[str, Any] | None) -> int:
    if payload is None:
        return 0

    metadata_count = payload.get('metadata', {}).get('abstracts_seen')
    if isinstance(metadata_count, int):
        return metadata_count

    return sum(
        bool(work.get('abstract_inverted_index'))
        for work in payload.get('results') or []
    )


#%% inventory rows
def work_page_summary(layer: BoundaryLayer, year: int) -> dict[str, Any]:
    pages = json_files(work_dir(layer, year))
    last_page = pages[-1] if pages else None
    last_payload = None
    last_page_count = 0
    if last_page is not None:
        last_payload = read_json(last_page)
        last_page_count = len((last_payload or {}).get('results') or [])

    exhausted = ''
    if pages and last_payload is not None:
        # when there is no next page OA would return None
        exhausted = last_payload.get('metadata', {}).get('next_cursor') is None

    return {
        'work_pages': len(pages),
        'work_records': saved_record_count(len(pages), last_page_count),
        'work_exhausted': exhausted,
    }


def abstract_page_summary(layer: BoundaryLayer, year: int) -> dict[str, Any]:
    pages = json_files(abstract_dir(layer, year))
    abstract_records = 0
    abstracts_seen = 0

    for page in pages:
        payload = read_json(page)
        abstract_records += len((payload or {}).get('results') or [])
        abstracts_seen += abstract_count(payload)

    return {
        'abstract_pages': len(pages),
        'abstract_records': abstract_records,
        'abstracts_seen': abstracts_seen,
    }


def count_summary(layer: BoundaryLayer, year: int) -> dict[str, Any]:
    path = count_path(layer, year)
    if not path.exists():
        return {
            'count_saved': False,
            'count_works': '',
        }

    payload = read_json(path)
    if payload is None:
        return {
            'count_saved': True,
            'count_works': '',
        }

    return {
        'count_saved': True,
        'count_works': payload.get('works_count', ''),
    }


def inventory_row(layer: BoundaryLayer, year: int) -> dict[str, Any]:
    work = work_page_summary(layer, year)
    abstract = abstract_page_summary(layer, year)
    count = count_summary(layer, year)
    fetch_mode = 'works' if layer.fetch_works else 'counts'

    # the counts should line up with the boundary fetch
    if layer.fetch_works and work['work_pages']:
        abstract_pull_complete = abstract['abstract_pages'] == work['work_pages']
    else:
        abstract_pull_complete = ''

    return {
        'layer': layer.key,
        'fetch_mode': fetch_mode,
        'year': year,
        'in_model_window': year >= MODEL_START_YEAR,
        **work,
        **abstract,
        'abstract_pull_complete': abstract_pull_complete,
        **count,
    }


def inventory_rows(
        layers: list[BoundaryLayer],
        start_year: int,
        end_year: int,
        ) -> list[dict[str, Any]]:
    rows = []
    for layer in layers:
        years = range(start_year, end_year + 1)
        for year in tqdm(years, desc=layer.key, unit='year'):
            rows.append(inventory_row(layer, year))

    return rows


def write_inventory(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


#%% main
def main() -> None:
    args = parse_args()
    layers = selected_layers(args.layer)
    rows = inventory_rows(layers, args.start_year, args.end_year)
    write_inventory(rows, args.output)
    print(f'wrote {args.output} ({len(rows)} rows)')


if __name__ == '__main__':
    main()
