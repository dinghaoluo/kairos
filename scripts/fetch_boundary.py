'''
Created on Tue Jun  9 2026

pull boundary-layer records by year

examples:
python scripts/fetch_boundary.py --layer core_nn --year 2012 --max-pages 5
python scripts/fetch_boundary.py --layer adjacent_ml --all-years --start-year 2024 --end-year 2025 --verbose

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
from kairos.data.config import BOUNDARY_LAYERS, BoundaryLayer, END_YEAR, RAW_DATA_DIR, START_YEAR
from kairos.data.topics import boundary_filter
from kairos.data.work import WORK_SELECT_FIELDS


#%% settings
DEFAULT_LAYER = 'core_nn'
DEFAULT_MAX_PAGES = 1  # so that we don't accidentally burn through usage
DEFAULT_MIN_REMAINING = 20


#%% command line
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--layer', default=DEFAULT_LAYER)
    parser.add_argument('--year', type=int)
    parser.add_argument('--start-year', type=int, default=START_YEAR)
    parser.add_argument('--end-year', type=int, default=END_YEAR)
    parser.add_argument('--all-years', action='store_true')
    parser.add_argument('--per-page', type=int, default=100)
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


#%% output paths
def works_dir(layer: BoundaryLayer, year: int) -> Path:
    return RAW_DATA_DIR / 'works' / layer.key / str(year)


def count_dir(layer: BoundaryLayer) -> Path:
    return RAW_DATA_DIR / 'counts' / layer.key


def existing_json_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob('*.json'))


def existing_page_state(directory: Path) -> tuple[int, str | None]:
    page_files = existing_json_files(directory)
    if not page_files:
        return 0, '*'  # * is the OA cursor starting point

    last_payload = json.loads(page_files[-1].read_text(encoding='utf-8'))
    next_cursor = last_payload.get('metadata', {}).get('next_cursor')
    return len(page_files), next_cursor


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )


def mark_page_exhausted(path: Path) -> None:
    '''mark prev page as exhausted if a next-page fetch returns nichts'''
    payload = json.loads(path.read_text(encoding='utf-8'))
    payload['metadata']['next_cursor'] = None
    write_json(path, payload)


#%% metadata
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


def page_payload(
        page: OpenAlexPage,
        layer: BoundaryLayer,
        year: int,
        page_number: int,
        ) -> dict[str, Any]:
    '''store one work page with the fetch context needed for later checks'''
    return {
        'metadata': {
            'fetched_at_utc': datetime.now(timezone.utc).isoformat(),
            'boundary_layer': asdict(layer),
            'publication_year': year,
            'page_number': page_number,
            'endpoint': page.endpoint,
            'params': page.params,
            'works_count': page.meta.get('count'),
            'result_count': len(page.results),
            'next_cursor': page.meta.get('next_cursor'),
            'rate_limit': rate_limit_headers(page.response_headers),
        },
        'results': page.results,
    }


def count_payload(
        page: OpenAlexPage,
        layer: BoundaryLayer,
        year: int,
        ) -> dict[str, Any]:
    '''store the yearly denominator for a broad background layer'''
    return {
        'metadata': {
            'fetched_at_utc': datetime.now(timezone.utc).isoformat(),
            'boundary_layer': asdict(layer),
            'publication_year': year,
            'endpoint': page.endpoint,
            'params': page.params,
            'rate_limit': rate_limit_headers(page.response_headers),
        },
        'works_count': page.meta.get('count', 0),
    }


#%% fetching
def fetch_work_pages(
        client: OpenAlexClient,
        layer: BoundaryLayer,
        year: int,
        per_page: int,
        max_pages: int,
        min_remaining: int,
        verbose: bool,
        ) -> None:
    '''
    fetch one layer-year of full work records

    inputs:
        client: OA client with the local API key already loaded
        layer: boundary layer, e.g. core_nn or adjacent_ml
        year: publication year to fetch
        per_page: number of OA works requested per cursor page
        max_pages: page cap for this run; 0 = keep going until exhausted
        min_remaining: stop when OA says this many requests remain
        verbose: print every written page instead of just showing tqdm

    directly writes page_XXX.json files under data/raw/works/<layer>/<year>
    '''
    output_dir = works_dir(layer, year)
    pages_already_fetched, start_cursor = existing_page_state(output_dir)
    if pages_already_fetched:
        if start_cursor is None:
            if verbose:
                print(f'skipping {layer.key} {year}; this layer-year is already exhausted')
            return
        if verbose:
            print(f'resuming {layer.key} {year} from page {pages_already_fetched + 1}')

    # keep the raw pull narrow and leave feature decisions for later
    params = {
        'filter': boundary_filter(layer.level, layer.ids, publication_year=year),
        'sort': 'publication_date:asc',
        'select': WORK_SELECT_FIELDS,
    }
    page_limit = None if max_pages == 0 else max_pages
    last_output_path: Path | None = None
    pages = client.iter_cursor_pages(
        'works',
        params,
        per_page=per_page,
        max_pages=page_limit,
        start_cursor=start_cursor,
        include_empty=True,  # ask for empty page too so prev page can be marked as done
    )
    if not verbose:
        pages = tqdm(
            pages,
            total=page_limit,
            desc=f'{layer.key} {year}',
            unit='page',
            leave=False,
        )
    for page_offset, page in enumerate(pages, start=1):
        if not page.results:
            if last_output_path is not None:
                mark_page_exhausted(last_output_path)
            elif pages_already_fetched:
                page_files = existing_json_files(output_dir)
                if page_files:
                    mark_page_exhausted(page_files[-1])
            break

        page_number = pages_already_fetched + page_offset
        output_path = output_dir / f'page_{page_number:03}.json'
        write_json(output_path, page_payload(page, layer, year, page_number))
        last_output_path = output_path
        if verbose:
            print(f'wrote {output_path} ({len(page.results)} records)')

        # stop before OA usage gets too Close to the Edge
        remaining = remaining_request_count(page.response_headers)
        if remaining is not None and remaining <= min_remaining:
            if verbose:
                print(f'stopping because only {remaining} requests remain')
            break


def fetch_count(
        client: OpenAlexClient,
        layer: BoundaryLayer,
        year: int,
        verbose: bool,
        ) -> None:
    '''fetch only the work count for one broad layer-year'''
    output_path = count_dir(layer) / f'{year}.json'
    if output_path.exists():
        if verbose:
            print(f'skipping {layer.key} {year}; count already exists')
        return

    # broad layers are denominators, not full modelling corpora
    page = client.get(
        'works',
        {
            'filter': boundary_filter(layer.level, layer.ids, publication_year=year),
            'per-page': 1,
            'select': 'id',
        },
    )
    write_json(output_path, count_payload(page, layer, year))
    count = page.meta.get('count', 0)
    if verbose:
        print(f'wrote {output_path} ({count} works)')


def fetch_layer_year(
        client: OpenAlexClient,
        layer: BoundaryLayer,
        year: int,
        per_page: int,
        max_pages: int,
        min_remaining: int,
        verbose: bool,
        ) -> None:
    if layer.fetch_works:
        fetch_work_pages(
            client,
            layer,
            year,
            per_page,
            max_pages,
            min_remaining,
            verbose,
        )
    else:
        fetch_count(client, layer, year, verbose)


#%% main
def main() -> None:
    args = parse_args()
    client = OpenAlexClient.from_env()
    layer = boundary_layer(args.layer)

    years = selected_years(args.year, args.all_years, args.start_year, args.end_year)
    if not args.verbose and len(years) > 1:
        years = tqdm(years, desc=args.layer, unit='year')

    for year in years:
        fetch_layer_year(
            client,
            layer,
            year,
            args.per_page,
            args.max_pages,
            args.min_remaining,
            args.verbose,
        )


if __name__ == '__main__':
    main()
