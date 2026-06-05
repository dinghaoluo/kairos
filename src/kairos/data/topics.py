'''
Created on Fri Jun  5 2026

resolve OpenAlex topics for a candidate field query

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

from typing import Any

from kairos.data.api import OpenAlexClient


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


def search_topics(
        client: OpenAlexClient,
        query: str,
        per_page: int = 5,
        ) -> list[dict[str, Any]]:
    '''search OpenAlex topics for one candidate phrase'''
    params = {
        'search': query,
        'per-page': per_page,
        'select': 'id,display_name,works_count,description,subfield,field,domain',
    }
    page = client.get('topics', params)
    return [normalise_topic(topic) for topic in page.results]

