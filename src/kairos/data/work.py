'''
Created on Fri Jun 5 2026

normalise OpenAlex work records into simple rows

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

from typing import Any

from kairos.data.api import OpenAlexClient


#%% fields
WORK_SELECT_FIELDS = (
    'id,doi,title,display_name,publication_year,publication_date,cited_by_count,'
    'primary_topic,topics,primary_location,referenced_works,authorships,counts_by_year'
)


#%% work-level normalisation
def normalise_work(work: dict[str, Any]) -> dict[str, Any]:
    '''normalise one OpenAlex work into a flat row'''
    primary_topic = work.get('primary_topic') or {}
    primary_subfield = primary_topic.get('subfield') or {}
    primary_field = primary_topic.get('field') or {}
    primary_domain = primary_topic.get('domain') or {}
    source = work.get('primary_location', {}).get('source') or {}
    topics = work.get('topics') or []
    topic_subfields = [(topic.get('subfield') or {}) for topic in topics]
    topic_fields = [(topic.get('field') or {}) for topic in topics]
    topic_domains = [(topic.get('domain') or {}) for topic in topics]

    return {
        'openalex_id': work.get('id'),
        'doi': work.get('doi'),
        'title': work.get('title') or work.get('display_name'),
        'publication_year': work.get('publication_year'),
        'publication_date': work.get('publication_date'),
        'cited_by_count': work.get('cited_by_count'),
        'primary_topic_id': primary_topic.get('id'),
        'primary_topic_name': primary_topic.get('display_name'),
        'primary_subfield_id': primary_subfield.get('id'),
        'primary_subfield_name': primary_subfield.get('display_name'),
        'primary_field_id': primary_field.get('id'),
        'primary_field_name': primary_field.get('display_name'),
        'primary_domain_id': primary_domain.get('id'),
        'primary_domain_name': primary_domain.get('display_name'),
        'source_id': source.get('id'),
        'source_name': source.get('display_name'),
        'topic_ids': [topic.get('id') for topic in topics],
        'topic_names': [topic.get('display_name') for topic in topics],
        'topic_subfield_ids': [subfield.get('id') for subfield in topic_subfields],
        'topic_subfield_names': [subfield.get('display_name') for subfield in topic_subfields],
        'topic_field_ids': [field.get('id') for field in topic_fields],
        'topic_field_names': [field.get('display_name') for field in topic_fields],
        'topic_domain_ids': [domain.get('id') for domain in topic_domains],
        'topic_domain_names': [domain.get('display_name') for domain in topic_domains],
        'referenced_work_count': len(work.get('referenced_works') or []),
        'authorship_count': len(work.get('authorships') or []),
        'topic_count': len(work.get('topics') or []),
        'counts_by_year': work.get('counts_by_year') or [],
    }


def search_work(
        client: OpenAlexClient,
        query: str | None = None,
        openalex_id: str | None = None,
        doi: str | None = None,
        publication_year: int | None = None,
        ) -> dict[str, Any] | None:
    '''return one matching OpenAlex work'''
    rows = search_works(
        client,
        query=query,
        openalex_id=openalex_id,
        doi=doi,
        publication_year=publication_year,
        per_page=1,
    )
    return rows[0] if rows else None


def search_works(
        client: OpenAlexClient,
        query: str | None = None,
        openalex_id: str | None = None,
        doi: str | None = None,
        publication_year: int | None = None,
        per_page: int = 3,
        ) -> list[dict[str, Any]]:
    '''return matching OpenAlex works as flat rows'''
    if openalex_id is not None:
        page = client.get(
            f'works/{short_work_id(openalex_id)}',
            {'select': WORK_SELECT_FIELDS},
        )
        return [normalise_work(page.data)]

    params = {
        'per-page': per_page,
        'select': WORK_SELECT_FIELDS,
    }
    if doi is not None:
        params['filter'] = f'doi:{clean_doi(doi)}'
    elif query is not None:
        params['search'] = query
        if publication_year is not None:
            params['filter'] = f'publication_year:{publication_year}'
    else:
        return []

    page = client.get('works', params)
    return [normalise_work(work) for work in page.results]


def clean_doi(doi: str) -> str:
    '''strip DOI URL prefixes before OpenAlex filtering'''
    return (
        doi.strip()
        .removeprefix('https://doi.org/')
        .removeprefix('http://doi.org/')
        .removeprefix('https://dx.doi.org/')
        .removeprefix('http://dx.doi.org/')
    )


def short_work_id(openalex_id: str) -> str:
    '''strip OpenAlex URL prefixes before direct work lookup'''
    return openalex_id.strip().rsplit('/', 1)[-1]
