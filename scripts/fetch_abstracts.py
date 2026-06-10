'''
Created on Tue Jun  9 2026

fetch abstract indexes for already-pulled work pages

some notes on the OA abstract data structure...
OA stores abstracts as `abstract_inverted_index`, not as plain text, so 
here we only fetch those abstract indexes, and writes matching pages under 
`data/raw/abstracts`; the abstract can be reconstructed from the inverted 
indices

examples:
python scripts/fetch_abstracts.py --layer core_nn --year 2012 --max-pages 5
python scripts/fetch_abstracts.py --layer adjacent_ml --all-years --start-year 2024 --end-year 2025 --verbose

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tqdm import tqdm

from kairos.data.api import OpenAlexClient, OpenAlexPage
from kairos.data.config import BOUNDARY_LAYERS, BoundaryLayer, END_YEAR, MODEL_START_YEAR, RAW_DATA_DIR
from kairos.data.work import short_work_id


#%% settings
DEFAULT_LAYER = 'core_nn'
DEFAULT_MAX_PAGES = 1  # so that we don't accidentally burn through usage
DEFAULT_MIN_REMAINING = 20
ABSTRACT_SELECT_FIELDS = 'id, abstract_inverted_index'
ID_CHUNK_SIZE = 100  # OA work-ID filters are still page-sized requests


#%% command line
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--layer', default=DEFAULT_LAYER)
    parser.add_argument('--year', type=int)
    parser.add_argument('--start-year', type=int, default=MODEL_START_YEAR)
    parser.add_argument('--end-year', type=int, default=END_YEAR)
    parser.add_argument('--all-years', action='store_true')
    parser.add_argument('--max-pages', type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument('--min-remaining', type=int, default=DEFAULT_MIN_REMAINING)
    parser.add_argument('--verbose', action='store_true')
    return parser.parse_args()


def selected_years(
        year: int | None,
        all_years: bool,
        start_year: int,
        end_year: int,
        ) -> list[int]:
    if year is None:
        if all_years:
            return list(range(start_year, end_year + 1))
        raise SystemExit('choose either --year or --all-years')
    return [year]  # if we just run with a specific year


def boundary_layer(layer_key: str) -> BoundaryLayer:
    layers = {layer.key: layer for layer in BOUNDARY_LAYERS}
    if layer_key not in layers:  # if layer is not in the predefined list
        known_layers = ', '.join(layers)
        raise SystemExit(f'unknown layer {layer_key}; choose one of: {known_layers}')
    return layers[layer_key]


#%% paths
def works_dir(layer: BoundaryLayer, year: int) -> Path:
    return RAW_DATA_DIR / 'works' / layer.key / str(year)


def abstracts_dir(layer: BoundaryLayer, year: int) -> Path:
    return RAW_DATA_DIR / 'abstracts' / layer.key / str(year)


def json_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob('*.json'))


def abstract_page_path(layer: BoundaryLayer, year: int, page_number: int) -> Path:
    return abstracts_dir(layer, year) / f'page_{page_number:03}.json'


#%% payloads
def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )


def work_ids_from_page(path: Path) -> list[str]:
    payload = read_json(path)
    return [
        work_id for work_id in (
            work.get('id')
            for work in payload.get('results', [])
        )
        if work_id
    ]


def rate_limit_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if 'rate' in key.lower() or 'cost' in key.lower()
    }


def remaining_request_count(headers: dict[str, str]) -> int | None:
    for key, value in headers.items():
        normalised_key = key.lower().replace('-', '_')
        if normalised_key.endswith('ratelimit_remaining'):
            try:
                return int(value)
            except ValueError:
                return None
    return None


def abstract_payload(
        pages: list[OpenAlexPage],
        layer: BoundaryLayer,
        year: int,
        source_page: Path,
        work_ids: list[str],
        ) -> dict[str, Any]:
    '''store one abstract page with its source-page metadata'''
    results = [
        work
        for page in pages
        for work in page.results
    ]
    return {
        'metadata': {
            'fetched_at_utc': datetime.now(timezone.utc).isoformat(),
            'boundary_layer': asdict(layer),
            'publication_year': year,
            'source_page': source_page.name,
            'source_work_count': len(work_ids),
            'requests': [
                {
                    'endpoint': page.endpoint,
                    'params': page.params,
                    'result_count': len(page.results),
                    'rate_limit': rate_limit_headers(page.response_headers),
                }
                for page in pages
            ],
            'result_count': len(results),
            'abstracts_seen': sum(
                bool(work.get('abstract_inverted_index'))
                for work in results
            ),
        },
        'results': results,
    }


#%% fetching
def fetch_abstract_pages(
        client: OpenAlexClient,
        work_ids: list[str],
        ) -> list[OpenAlexPage]:
    '''
    fetch abstract indexes for one saved work-page ID list
    '''
    pages = []
    for start in range(0, len(work_ids), ID_CHUNK_SIZE):
        work_id_chunk = work_ids[start:start + ID_CHUNK_SIZE]
        short_ids = [short_work_id(work_id) for work_id in work_id_chunk]
        id_filter = '|'.join(short_ids)
        pages.append(
            client.get(
                'works',
                {
                    'filter': f'ids.openalex:{id_filter}',
                    'per-page': len(short_ids),
                    'select': ABSTRACT_SELECT_FIELDS,
                },
            )
        )
    return pages


def fetch_year_abstracts(
        client: OpenAlexClient,
        layer: BoundaryLayer,
        year: int,
        max_pages: int,
        min_remaining: int,
        verbose: bool,
        ) -> None:
    '''
    fetch abstract pages for one already-pulled layer-year

    inputs:
        client: OA client with the local API key already loaded
        layer: boundary layer, e.g. core_nn or adjacent_ml
        year: publication year whose saved work pages should be scanned
        max_pages: source-page cap for this run; 0 = all saved work pages
        min_remaining: stop when OA says this many requests remain
        verbose: print every written page instead of just showing tqdm

    directly writes page_XXX.json files under data/raw/abstracts/<layer>/<year>
    '''
    # abstracts are a second pass over work pages we already decided to keep
    work_pages = json_files(works_dir(layer, year))
    if not work_pages:
        if verbose:
            print(f'skipping {layer.key} {year}; no work pages found')
        return

    page_limit = len(work_pages) if max_pages == 0 else max_pages
    source_pages = work_pages[:page_limit]
    if not verbose:
        source_pages = tqdm(
            source_pages,
            desc=f'{layer.key} {year}',
            unit='page',
            leave=False,
        )
    last_page: OpenAlexPage | None = None
    for source_page in source_pages:
        page_number = int(source_page.stem.rsplit('_', 1)[-1])
        output_path = abstract_page_path(layer, year, page_number)
        # if this abstract page already exists, treat it as done
        if output_path.exists():
            continue

        work_ids = work_ids_from_page(source_page)
        if not work_ids:
            continue

        pages = fetch_abstract_pages(client, work_ids)
        write_json(output_path, abstract_payload(pages, layer, year, source_page, work_ids))
        last_page = pages[-1]
        if verbose:
            result_count = sum(len(page.results) for page in pages)
            print(f'wrote {output_path} ({result_count} works)')

        remaining = remaining_request_count(last_page.response_headers)
        if remaining is not None and remaining <= min_remaining:
            if verbose:
                print(f'stopping because only {remaining} requests remain')
            break


#%% main
def main() -> None:
    args = parse_args()
    client = OpenAlexClient.from_env()
    layer = boundary_layer(args.layer)

    years = selected_years(args.year, args.all_years, args.start_year, args.end_year)
    if not args.verbose and len(years) > 1:
        years = tqdm(years, desc=args.layer, unit='year')

    for year in years:
        fetch_year_abstracts(
            client,
            layer,
            year,
            args.max_pages,
            args.min_remaining,
            args.verbose,
        )


if __name__ == '__main__':
    main()
