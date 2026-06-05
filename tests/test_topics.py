'''
Created on Fri Jun  5 2026

test OpenAlex topic helpers

@author: Dinghao Luo
'''

#%% imports
from kairos.data.topics import normalise_topic


#%% tests
def test_normalise_topic_keeps_boundary_fields() -> None:
    '''topic records should keep hierarchy information'''
    topic = {
        'id': 'https://openalex.org/T10320',
        'display_name': 'Neural Networks and Applications',
        'works_count': 251872,
        'description': 'test description',
        'subfield': {
            'id': 'https://openalex.org/subfields/1702',
            'display_name': 'Artificial Intelligence',
        },
        'field': {
            'id': 'https://openalex.org/fields/17',
            'display_name': 'Computer Science',
        },
        'domain': {
            'id': 'https://openalex.org/domains/3',
            'display_name': 'Physical Sciences',
        },
    }

    row = normalise_topic(topic)

    assert row['openalex_id'] == 'https://openalex.org/T10320'
    assert row['display_name'] == 'Neural Networks and Applications'
    assert row['works_count'] == 251872
    assert row['subfield_name'] == 'Artificial Intelligence'
    assert row['field_name'] == 'Computer Science'
    assert row['domain_name'] == 'Physical Sciences'

