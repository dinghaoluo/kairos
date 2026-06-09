'''
Created on Fri Jun 5 2026

normalise work records into simple rows

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

import csv
from functools import lru_cache
from typing import Any

from kairos.data.api import OpenAlexClient
from kairos.data.config import SPURIOUS_WORKS_CURATION_FILE


#%% fields
# keep nested fields here because the feature table is not fixed yet
WORK_SELECT_FIELDS = (
    'id,doi,title,display_name,publication_year,publication_date,cited_by_count,'
    'primary_topic,topics,primary_location,referenced_works,authorships,counts_by_year,'
    'abstract_inverted_index'  # what OA stores instead of the abstract text 
)

#%% work-level normalisation
def normalise_work(work: dict[str, Any]) -> dict[str, Any]:
    '''flatten one selected work record for diagnostics'''
    primary_topic = work.get('primary_topic') or {}
    primary_subfield = primary_topic.get('subfield') or {}
    primary_field = primary_topic.get('field') or {}
    primary_domain = primary_topic.get('domain') or {}
    source = work.get('primary_location', {}).get('source') or {}
    topics = work.get('topics') or []
    abstract_index = work.get('abstract_inverted_index') or {}
    topic_subfields = [(topic.get('subfield') or {}) for topic in topics]
    topic_fields = [(topic.get('field') or {}) for topic in topics]
    topic_domains = [(topic.get('domain') or {}) for topic in topics]
    openalex_id = work.get('id')

    return {
        'openalex_id': openalex_id,
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
        'has_abstract': bool(abstract_index),
        'abstract_word_count': abstract_word_count(abstract_index),
        'spurious_work': work_is_excluded(openalex_id),
        'spurious_reason': spurious_work_reason(openalex_id),
    }


def abstract_from_inverted_index(
        abstract_index: dict[str, list[int]] | None,
        ) -> str | None:
    '''rebuild an OA abstract from its inverted index'''
    if not abstract_index:
        return None

    words = [
        (position, word)
        for word, positions in abstract_index.items()
        for position in positions
    ]
    return ' '.join(word for _, word in sorted(words))


def abstract_word_count(abstract_index: dict[str, list[int]] | None) -> int:
    if not abstract_index:
        return 0
    return sum(len(positions) for positions in abstract_index.values())


def search_works(
        client: OpenAlexClient,
        query: str | None = None,
        openalex_id: str | None = None,
        doi: str | None = None,
        publication_year: int | None = None,
        per_page: int = 3,
        ) -> list[dict[str, Any]]:
    '''search works for diagnostics and return flattened rows'''
    # a curated OpenAlex ID should bypass loose title search
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


def search_work(
        client: OpenAlexClient,
        query: str | None = None,
        openalex_id: str | None = None,
        doi: str | None = None,
        publication_year: int | None = None,
        ) -> dict[str, Any] | None:
    '''return one landmark-style match from the same lookup path'''
    rows = search_works(
        client,
        query=query,
        openalex_id=openalex_id,
        doi=doi,
        publication_year=publication_year,
        per_page=1,
    )
    return rows[0] if rows else None


def clean_doi(doi: str) -> str:
    return (
        doi.strip()
        .removeprefix('https://doi.org/')
        .removeprefix('http://doi.org/')
        .removeprefix('https://dx.doi.org/')
        .removeprefix('http://dx.doi.org/')
    )


def short_work_id(openalex_id: str) -> str:
    return openalex_id.strip().rsplit('/', 1)[-1]


def work_is_excluded(openalex_id: str | None) -> bool:
    return openalex_id in spurious_work_reasons()


def spurious_work_reason(openalex_id: str | None) -> str | None:
    if openalex_id is None:
        return None
    return spurious_work_reasons().get(openalex_id)


@lru_cache(maxsize=1)
def spurious_work_reasons() -> dict[str, str]:
    '''read the curated spurious-work table'''
    # reasons = dict(SPURIOUS_WORKS)
    reasons = {}
    if not SPURIOUS_WORKS_CURATION_FILE.exists():
        return reasons

    with SPURIOUS_WORKS_CURATION_FILE.open(newline='', encoding='utf-8') as file:
        for row in csv.DictReader(file):
            if row.get('decision') == 'ignore':
                openalex_id = row.get('openalex_id')
                if openalex_id:
                    reasons[openalex_id] = (
                        row.get('notes') or row.get('note') or 'marked as spurious'
                    )
    return reasons
