'''
Created on Mon Jun  8 2026

check candidate OpenAlex boundaries

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

from kairos.data.api import OpenAlexClient
from kairos.data.config import (
    BOUNDARY_EXCLUSION_QUERIES,
    CANDIDATE_BOUNDARY_FIELD_IDS,
    CANDIDATE_BOUNDARY_SUBFIELD_IDS,
    CANDIDATE_BOUNDARY_TOPIC_IDS,
    CANDIDATE_TOPIC_QUERIES,
    END_YEAR,
    LandmarkPaper,
    LANDMARK_PAPERS,
    START_YEAR,
)
from kairos.data.topics import count_boundary_works_by_year, search_topics
from kairos.data.work import WORK_SELECT_FIELDS, normalise_work, search_work, search_works


#%% settings
SAMPLE_SIZE = 20


#%% helpers
def short_openalex_id(openalex_id: str | None) -> str | None:
    '''drop OpenAlex URL prefixes for compact printing'''
    if openalex_id is None:
        return None
    return openalex_id.rsplit('/', 1)[-1]


def format_hits(hits: list[str]) -> str:
    '''format matched boundary IDs for printing'''
    return ', '.join(hits) if hits else 'none'


def format_boundary_ids(boundary_ids: str | tuple[str, ...]) -> str:
    '''format one or more boundary IDs for printing'''
    if isinstance(boundary_ids, str):
        return boundary_ids
    return '|'.join(boundary_ids)


def topic_union_filter() -> str:
    '''build the current topic-union filter'''
    topic_ids = '|'.join(CANDIDATE_BOUNDARY_TOPIC_IDS)
    return f'topics.id:{topic_ids}'


def simple_text(text: str | None) -> str:
    '''normalise titles enough for rough matching'''
    if text is None:
        return ''
    return ''.join(char.lower() if char.isalnum() else ' ' for char in text)


def candidate_boundary_hits(row: dict) -> tuple[list[str], list[str], list[str]]:
    '''find configured boundary IDs attached to one work'''
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
    candidate_topic_hits = [
        topic_id for topic_id in CANDIDATE_BOUNDARY_TOPIC_IDS
        if topic_id in topic_ids
    ]
    candidate_subfield_hits = [
        subfield_id for subfield_id in CANDIDATE_BOUNDARY_SUBFIELD_IDS
        if subfield_id in subfield_ids
    ]
    candidate_field_hits = [
        field_id for field_id in CANDIDATE_BOUNDARY_FIELD_IDS
        if field_id in field_ids
    ]
    return candidate_topic_hits, candidate_subfield_hits, candidate_field_hits


#%% topic search
def print_topic_candidates(query: str, rows: list[dict]) -> None:
    '''print topic candidates for one search phrase'''
    print(f'\n# topic search: {query}')
    for idx, row in enumerate(rows, start=1):
        topic_id = short_openalex_id(row['openalex_id'])
        name = row['display_name']
        works = row['works_count']
        subfield_id = short_openalex_id(row['subfield_id'])
        subfield = row['subfield_name']
        field_id = short_openalex_id(row['field_id'])
        field = row['field_name']
        print(
            f'{idx:>2}. {topic_id} | {name} | {works} works | '
            f'{subfield_id} {subfield} | {field_id} {field}'
        )


def check_topic_searches(client: OpenAlexClient) -> None:
    '''search the configured candidate topic phrases'''
    for query in CANDIDATE_TOPIC_QUERIES:
        rows = search_topics(client, query, per_page=5)
        print_topic_candidates(query, rows)


#%% landmark works
def landmark_warnings(
        paper: LandmarkPaper,
        row: dict,
        candidate_topic_hits: list[str],
        candidate_subfield_hits: list[str],
        candidate_field_hits: list[str],
        ) -> list[str]:
    '''flag landmark records that need manual checking'''
    warnings = []
    publication_year = row['publication_year']
    cited_by_count = row['cited_by_count']
    title = row['title']

    if publication_year != paper.publication_year:
        warnings.append(
            f'expected year {paper.publication_year}, OpenAlex gives {publication_year}'
        )

    if cited_by_count is not None and cited_by_count < 1000:
        warnings.append(f'low citation count for a landmark: {cited_by_count}')

    expected_words = {
        word for word in simple_text(paper.title).split()
        if len(word) > 2
    }
    returned_words = set(simple_text(title).split())
    if not expected_words.issubset(returned_words):
        warnings.append('title does not contain all expected title words')

    if not candidate_topic_hits and not candidate_subfield_hits and not candidate_field_hits:
        warnings.append('no overlap with candidate topic, subfield, or field boundary')

    return warnings


def print_landmark_work(paper: LandmarkPaper, row: dict | None) -> None:
    '''print one matched landmark work'''
    print(f'\n# landmark work: {paper.key}')
    if row is None:
        print('no OpenAlex match found')
        return

    (
        candidate_topic_hits,
        candidate_subfield_hits,
        candidate_field_hits,
    ) = candidate_boundary_hits(row)
    work_id = row['openalex_id']
    year = row['publication_year']
    title = row['title']
    doi = row['doi']
    cited_by_count = row['cited_by_count']
    primary_topic = row['primary_topic_name']
    primary_subfield = row['primary_subfield_name']
    primary_field = row['primary_field_name']
    warnings = landmark_warnings(
        paper,
        row,
        candidate_topic_hits,
        candidate_subfield_hits,
        candidate_field_hits,
    )

    print(f'work: {work_id}')
    print(f'year: {year} (expected {paper.publication_year})')
    print(f'title: {title}')
    print(f'doi: {doi}')
    print(f'cited by: {cited_by_count}')
    print(f'primary topic: {primary_topic}')
    print(f'primary subfield: {primary_subfield}')
    print(f'primary field: {primary_field}')
    print(f'candidate topic hits: {format_hits(candidate_topic_hits)}')
    print(f'candidate subfield hits: {format_hits(candidate_subfield_hits)}')
    print(f'candidate field hits: {format_hits(candidate_field_hits)}')
    warning_text = '; '.join(warnings) if warnings else 'none'
    print(f'warnings: {warning_text}')
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


def check_landmark_works(client: OpenAlexClient) -> None:
    '''search configured landmark papers in OpenAlex'''
    for paper in LANDMARK_PAPERS:
        row = search_work(
            client,
            query=paper.title,
            openalex_id=paper.openalex_id,
            doi=paper.doi,
            publication_year=paper.publication_year,
        )
        print_landmark_work(paper, row)


#%% exclusion works
def print_exclusion_work(row: dict) -> None:
    '''print one negative-control work compactly'''
    (
        candidate_topic_hits,
        candidate_subfield_hits,
        candidate_field_hits,
    ) = candidate_boundary_hits(row)
    year = row['publication_year']
    title = row['title']
    cited_by_count = row['cited_by_count']
    primary_topic = row['primary_topic_name']

    print(f'  - {year} | cited by {cited_by_count} | {title}')
    print(f'    primary topic: {primary_topic}')
    print(f'    candidate topic hits: {format_hits(candidate_topic_hits)}')
    print(f'    candidate subfield hits: {format_hits(candidate_subfield_hits)}')
    print(f'    candidate field hits: {format_hits(candidate_field_hits)}')


def check_exclusion_queries(client: OpenAlexClient) -> None:
    '''search negative-control queries for accidental boundary hits'''
    for query in BOUNDARY_EXCLUSION_QUERIES:
        print(f'\n# exclusion query: {query}')
        rows = search_works(client, query, per_page=3)
        for row in rows:
            print_exclusion_work(row)


#%% boundary sample
def fetch_boundary_sample(
        client: OpenAlexClient,
        sample_size: int = SAMPLE_SIZE,
        ) -> list[dict]:
    '''fetch a small top-cited sample from the topic union'''
    page = client.get(
        'works',
        {
            'filter': topic_union_filter(),
            'sort': 'cited_by_count:desc',
            'per-page': sample_size,
            'select': WORK_SELECT_FIELDS,
        },
    )
    return [normalise_work(work) for work in page.results]


def print_boundary_sample(rows: list[dict]) -> None:
    '''print fetched works compactly'''
    print(f'\n# boundary sample: top {len(rows)} by citation count')
    print(f'filter: {topic_union_filter()}')
    for idx, row in enumerate(rows, start=1):
        (
            candidate_topic_hits,
            _,
            _,
        ) = candidate_boundary_hits(row)
        year = row['publication_year']
        cited_by_count = row['cited_by_count']
        title = row['title']
        primary_topic = row['primary_topic_name']

        print(f'\n{idx:>2}. {year} | cited by {cited_by_count} | {title}')
        print(f'    primary topic: {primary_topic}')
        print(f'    topic-union hits: {format_hits(candidate_topic_hits)}')


def check_boundary_sample(client: OpenAlexClient) -> None:
    '''fetch and print a small boundary sample'''
    rows = fetch_boundary_sample(client)
    print_boundary_sample(rows)


#%% yearly counts
def print_year_counts(
        boundary_name: str,
        boundary_ids: str | tuple[str, ...],
        rows: list[dict[str, int]],
        ) -> None:
    '''print yearly works counts for one boundary'''
    print(f'\n# yearly counts: {boundary_name} {format_boundary_ids(boundary_ids)}')
    for row in rows:
        year = row['publication_year']
        count = row['works_count']
        print(f'{year}: {count}')


def check_year_counts(client: OpenAlexClient) -> None:
    '''count configured boundaries across the search window'''
    boundaries = (
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
        print_year_counts(boundary_name, boundary_ids, rows)


#%% main
def main() -> None:
    '''run the first OpenAlex boundary checks'''
    client = OpenAlexClient.from_env()
    check_topic_searches(client)
    check_landmark_works(client)
    check_exclusion_queries(client)
    check_boundary_sample(client)
    check_year_counts(client)


if __name__ == '__main__':
    main()
