'''
Created on Mon Jun  8 2026

diagnose candidate OpenAlex boundaries

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

from kairos.data.api import OpenAlexClient
from kairos.data.config import (
    BOUNDARY_LAYERS,
    CANDIDATE_BOUNDARY_FIELD_IDS,
    CANDIDATE_BOUNDARY_SUBFIELD_IDS,
    CANDIDATE_BOUNDARY_TOPIC_IDS,
    CANDIDATE_TOPIC_QUERIES,
    END_YEAR,
    PinnedLandmarkPaper,
    PINNED_LANDMARK_PAPERS,
    START_YEAR,
)
from kairos.data.topics import (
    boundary_filter,
    count_boundary_works_by_year,
    search_topics,
    short_openalex_id,
)
from kairos.data.work import WORK_SELECT_FIELDS, normalise_work, search_work, search_works


#%% settings
SAMPLE_SIZE = 20

BOUNDARY_EXCLUSION_QUERIES = (
    'experimental organic synthesis',
    'relational database systems',
    'quantum chromodynamics',
    'literary criticism',
)


#%% small helpers
def simple_text(text: str | None) -> str:
    if text is None:
        return ''
    return ''.join(char.lower() if char.isalnum() else ' ' for char in text)


def boundary_hits(row: dict) -> dict[str, list[str]]:
    topic_ids = [
        short_openalex_id(topic_id)
        for topic_id in row['topic_ids']
        if topic_id is not None
    ]
    subfield_ids = [
        short_openalex_id(subfield_id)
        for subfield_id in row['topic_subfield_ids']
        if subfield_id is not None
    ]
    field_ids = [
        short_openalex_id(field_id)
        for field_id in row['topic_field_ids']
        if field_id is not None
    ]

    return {
        'topic': [
            topic_id for topic_id in CANDIDATE_BOUNDARY_TOPIC_IDS
            if topic_id in topic_ids
        ],
        'subfield': [
            subfield_id for subfield_id in CANDIDATE_BOUNDARY_SUBFIELD_IDS
            if subfield_id in subfield_ids
        ],
        'field': [
            field_id for field_id in CANDIDATE_BOUNDARY_FIELD_IDS
            if field_id in field_ids
        ],
    }


def layer_hits(row: dict) -> dict[str, list[str]]:
    ids_by_level = {
        'primary_topic': [
            short_openalex_id(row['primary_topic_id'])
        ],
        'topic': [
            short_openalex_id(topic_id)
            for topic_id in row['topic_ids']
            if topic_id is not None
        ],
        'subfield': [
            short_openalex_id(subfield_id)
            for subfield_id in row['topic_subfield_ids']
            if subfield_id is not None
        ],
        'field': [
            short_openalex_id(field_id)
            for field_id in row['topic_field_ids']
            if field_id is not None
        ],
    }
    return {
        layer.key: [
            boundary_id for boundary_id in layer.ids
            if boundary_id in ids_by_level[layer.level]
        ]
        for layer in BOUNDARY_LAYERS
    }


def warnings_for_pinned_paper(paper: PinnedLandmarkPaper, row: dict) -> list[str]:
    warnings = []
    hits = boundary_hits(row)
    expected_year = paper.openalex_year or paper.publication_year

    if row['publication_year'] != expected_year:
        publication_year = row['publication_year']
        warnings.append(
            f'expected OpenAlex year {expected_year}, OpenAlex gives {publication_year}'
        )

    if row['cited_by_count'] is not None and row['cited_by_count'] < 1000:
        cited_by_count = row['cited_by_count']
        warnings.append(f'low citation count for a landmark: {cited_by_count}')

    expected_words = {
        word for word in simple_text(paper.title).split()
        if len(word) > 2
    }
    returned_words = set(simple_text(row['title']).split())
    if not expected_words.issubset(returned_words):
        warnings.append('title does not contain all expected title words')

    if paper.boundary_required and not any(hits.values()):
        warnings.append('no overlap with candidate topic, subfield, or field boundary')

    return warnings


#%% topic search
def check_topic_searches(client: OpenAlexClient) -> None:
    for query in CANDIDATE_TOPIC_QUERIES:
        print(f'\n----- topic search: {query}')
        rows = search_topics(client, query, per_page=5)
        for idx, row in enumerate(rows, start=1):
            topic_id = short_openalex_id(row['openalex_id'])
            subfield_id = short_openalex_id(row['subfield_id'])
            field_id = short_openalex_id(row['field_id'])
            display_name = row['display_name']
            works_count = row['works_count']
            subfield_name = row['subfield_name']
            field_name = row['field_name']
            print(
                f'{idx:>2}. {topic_id} | '
                f'{display_name} | {works_count} works | '
                f'{subfield_id} {subfield_name} | '
                f'{field_id} {field_name}'
            )


#%% landmark works
def check_pinned_landmarks(client: OpenAlexClient) -> None:
    for paper in PINNED_LANDMARK_PAPERS:
        print(f'\n----- pinned landmark: {paper.key}')
        row = search_work(
            client,
            query=paper.title,
            openalex_id=paper.openalex_id,
            doi=paper.doi,
            publication_year=paper.publication_year,
        )
        if row is None:
            print('no OpenAlex match found')
            continue

        work_id = row['openalex_id']
        year = row['publication_year']
        title = row['title']
        doi = row['doi']
        cited_by_count = row['cited_by_count']
        primary_topic = row['primary_topic_name']
        primary_subfield = row['primary_subfield_name']
        primary_field = row['primary_field_name']

        print(f'work: {work_id}')
        print(
            f'year: {year} '
            f'(historical {paper.publication_year}, '
            f'OpenAlex expected {paper.openalex_year or paper.publication_year})'
        )
        print(f'title: {title}')
        print(f'doi: {doi}')
        print(f'cited by: {cited_by_count}')
        print(f'primary topic: {primary_topic}')
        print(f'primary subfield: {primary_subfield}')
        print(f'primary field: {primary_field}')
        print(f'boundary hits: {boundary_hits(row)}')
        print(f'layer hits: {layer_hits(row)}')
        print(f'warnings: {warnings_for_pinned_paper(paper, row)}')
        print('topics:')
        for topic_id, topic_name, subfield_id, subfield_name, field_id, field_name in zip(
                row['topic_ids'],
                row['topic_names'],
                row['topic_subfield_ids'],
                row['topic_subfield_names'],
                row['topic_field_ids'],
                row['topic_field_names'],
                ):
            print(
                f'  - {short_openalex_id(topic_id)} | {topic_name} | '
                f'{short_openalex_id(subfield_id)} {subfield_name} | '
                f'{short_openalex_id(field_id)} {field_name}'
            )


#%% negative controls
def check_exclusion_queries(client: OpenAlexClient) -> None:
    for query in BOUNDARY_EXCLUSION_QUERIES:
        print(f'\n----- exclusion query: {query}')
        rows = search_works(client, query, per_page=3)
        for row in rows:
            year = row['publication_year']
            cited_by_count = row['cited_by_count']
            title = row['title']
            primary_topic = row['primary_topic_name']
            print(f'  - {year} | cited by {cited_by_count} | {title}')
            print(f'    primary topic: {primary_topic}')
            print(f'    boundary hits: {boundary_hits(row)}')


#%% top-cited sample
def check_boundary_sample(client: OpenAlexClient) -> None:
    topic_union = boundary_filter('topic', CANDIDATE_BOUNDARY_TOPIC_IDS)
    page = client.get(
        'works',
        {
            'filter': topic_union,
            'sort': 'cited_by_count:desc',
            'per-page': SAMPLE_SIZE,
            'select': WORK_SELECT_FIELDS,
        },
    )
    rows = [normalise_work(work) for work in page.results]

    print(f'\n----- boundary sample: top {len(rows)} by citation count')
    print(f'filter: {topic_union}')
    for idx, row in enumerate(rows, start=1):
        year = row['publication_year']
        cited_by_count = row['cited_by_count']
        title = row['title']
        primary_topic = row['primary_topic_name']
        print(f'\n{idx:>2}. {year} | cited by {cited_by_count} | {title}')
        print(f'    primary topic: {primary_topic}')
        print(f'    boundary hits: {boundary_hits(row)}')
        print(f'    layer hits: {layer_hits(row)}')


#%% yearly counts
def check_year_counts(client: OpenAlexClient) -> None:
    boundaries = (
        *(
            (f'layer {layer.key}', layer.level, layer.ids)
            for layer in BOUNDARY_LAYERS
        ),
        ('topic union', 'topic', CANDIDATE_BOUNDARY_TOPIC_IDS),
        *(('topic', 'topic', topic_id) for topic_id in CANDIDATE_BOUNDARY_TOPIC_IDS),
        *(
            ('subfield', 'subfield', subfield_id)
            for subfield_id in CANDIDATE_BOUNDARY_SUBFIELD_IDS
        ),
        *(('field', 'field', field_id) for field_id in CANDIDATE_BOUNDARY_FIELD_IDS),
    )

    for boundary_name, boundary_level, boundary_ids in boundaries:
        rows = count_boundary_works_by_year(
            client,
            boundary_level,
            boundary_ids,
            START_YEAR,
            END_YEAR,
        )
        print(f'\n----- yearly counts: {boundary_name} {boundary_ids}')
        for row in rows:
            year = row['publication_year']
            count = row['works_count']
            print(f'{year}: {count}')


#%% main
def main() -> None:
    client = OpenAlexClient.from_env()
    check_topic_searches(client)
    check_pinned_landmarks(client)
    check_exclusion_queries(client)
    check_boundary_sample(client)
    check_year_counts(client)


if __name__ == '__main__':
    main()
