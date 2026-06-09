'''
Created on Fri Jun  5 2026

resolve OpenAlex topics for a candidate field query

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

from typing import Any

from kairos.data.api import OpenAlexClient


#%% boundary filters
BOUNDARY_FILTER_KEYS = {
    'topic': 'topics.id',
    'primary_topic': 'primary_topic.id',
    'subfield': 'topics.subfield.id',
    'field': 'topics.field.id',
}


def short_openalex_id(openalex_id: str | None) -> str | None:
    if openalex_id is None:
        return None
    return openalex_id.strip().rsplit('/', 1)[-1]


def boundary_filter(
        boundary_level: str,
        boundary_ids: str | tuple[str, ...],
        publication_year: int | None = None,
        ) -> str:
    '''build OA filter from our custom boundary definition'''
    filter_key = BOUNDARY_FILTER_KEYS[boundary_level]
    if isinstance(boundary_ids, str):
        short_ids = (short_openalex_id(boundary_ids),)
    else:
        short_ids = tuple(short_openalex_id(boundary_id) for boundary_id in boundary_ids)

    filter_value = '|'.join(short_ids)
    filter_parts = [f'{filter_key}:{filter_value}']
    if publication_year is not None:
        filter_parts.append(f'publication_year:{publication_year}')
    return ','.join(filter_parts)


#%% topic records
def normalise_topic(topic: dict[str, Any]) -> dict[str, Any]:
    '''extract the topic fields needed for boundary checks'''
    subfield = topic.get('subfield') or {}
    field = topic.get('field') or {}
    domain = topic.get('domain') or {}

    return {
        'openalex_id': topic.get('id'),
        'display_name': topic.get('display_name'),
        'works_count': topic.get('works_count'),
        'description': topic.get('description'),
        'subfield_id': subfield.get('id'),
        'subfield_name': subfield.get('display_name'),
        'field_id': field.get('id'),
        'field_name': field.get('display_name'),
        'domain_id': domain.get('id'),
        'domain_name': domain.get('display_name'),
    }


def normalise_year_count(group: dict[str, Any]) -> dict[str, int]:
    return {
        'publication_year': int(group['key']),
        'works_count': group['count'],
    }


def search_topics(
        client: OpenAlexClient,
        query: str,
        per_page: int = 5,
        ) -> list[dict[str, Any]]:
    '''search OA topics for one candidate phrase'''
    params = {
        'search': query,
        'per-page': per_page,
        'select': 'id,display_name,works_count,description,subfield,field,domain',
    }
    page = client.get('topics', params)
    return [normalise_topic(topic) for topic in page.results]


def count_boundary_works_by_year(
        client: OpenAlexClient,
        boundary_level: str,
        boundary_ids: str | tuple[str, ...],
        start_year: int,
        end_year: int,
        ) -> list[dict[str, int]]:
    '''count works by year for one topic, subfield, or field boundary'''
    page = client.get(
        'works',
        {
            'filter': boundary_filter(boundary_level, boundary_ids),
            'group_by': 'publication_year',
            'per-page': 100,
        },
    )
    rows = [normalise_year_count(group) for group in page.groups]
    rows = [
        row for row in rows
        if start_year <= row['publication_year'] <= end_year
    ]
    return sorted(rows, key=lambda row: row['publication_year'])
