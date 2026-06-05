'''
Created on Fri Jun  5 2026

resolve candidate OpenAlex topic boundaries

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

from kairos.data.api import OpenAlexClient
from kairos.data.config import CANDIDATE_TOPIC_QUERIES
from kairos.data.topics import search_topics


#%% display
def print_topic_candidates(query: str, rows: list[dict]) -> None:
    '''print topic candidates for one search phrase'''
    print(f'\n# {query}')
    for idx, row in enumerate(rows, start=1):
        topic_id = row['openalex_id']
        name = row['display_name']
        works = row['works_count']
        subfield = row['subfield_name']
        field = row['field_name']
        print(f'{idx:>2}. {topic_id} | {name} | {works} works | {subfield} | {field}')


#%% main
def main() -> None:
    '''search all configured candidate topic phrases'''
    client = OpenAlexClient.from_env()
    for query in CANDIDATE_TOPIC_QUERIES:
        rows = search_topics(client, query, per_page=5)
        print_topic_candidates(query, rows)


if __name__ == '__main__':
    main()
