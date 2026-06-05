'''
Created on Fri Jun 5 2026

normalise OpenAlex work records into simple rows

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

from typing import Any


#%% work-level normalisation
def normalise_work(work: dict[str, Any]) -> dict[str, Any]:
    # pull nested objects once so missing topic/source metadata becomes harmless
    primary_topic = work.get('primary_topic') or {}
    source = work.get('primary_location', {}).get('source') or {}

    return {
        'openalex_id': work.get('id'),
        'doi': work.get('doi'),
        'title': work.get('title') or work.get('display_name'),
        'publication_year': work.get('publication_year'),
        'publication_date': work.get('publication_date'),
        'primary_topic_id': primary_topic.get('id'),
        'primary_topic_name': primary_topic.get('display_name'),
        'source_id': source.get('id'),
        'source_name': source.get('display_name'),
        'referenced_work_count': len(work.get('referenced_works') or []),
        'authorship_count': len(work.get('authorships') or []),
        'topic_count': len(work.get('topics') or []),
        'counts_by_year': work.get('counts_by_year') or [],
    }
