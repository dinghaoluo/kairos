'''
Created on Mon Jun  8 2026

test OpenAlex work normalisation

@author: Dinghao Luo
'''

#%% imports
from kairos.data.work import (
    abstract_from_inverted_index,
    normalise_work,
    search_work,
    search_works,
    work_is_excluded,
)


#%% tests
def test_normalise_work_keeps_topic_hierarchy() -> None:
    '''work records should keep topic, subfield, and field IDs'''
    work = {
        'id': 'https://openalex.org/W123',
        'title': 'test work',
        'primary_topic': {
            'id': 'https://openalex.org/T10320',
            'display_name': 'Neural Networks and Applications',
            'subfield': {
                'id': 'https://openalex.org/subfields/1702',
                'display_name': 'Artificial Intelligence',
            },
            'field': {
                'id': 'https://openalex.org/fields/17',
                'display_name': 'Computer Science',
            },
        },
        'topics': [
            {
                'id': 'https://openalex.org/T10320',
                'display_name': 'Neural Networks and Applications',
                'subfield': {
                    'id': 'https://openalex.org/subfields/1702',
                    'display_name': 'Artificial Intelligence',
                },
                'field': {
                    'id': 'https://openalex.org/fields/17',
                    'display_name': 'Computer Science',
                },
            },
        ],
    }

    row = normalise_work(work)

    assert row['primary_subfield_name'] == 'Artificial Intelligence'
    assert row['primary_field_name'] == 'Computer Science'
    assert row['topic_subfield_ids'] == ['https://openalex.org/subfields/1702']
    assert row['topic_field_ids'] == ['https://openalex.org/fields/17']


def test_abstract_from_inverted_index_rebuilds_text() -> None:
    '''OA abstract indexes should be reversible enough for NLP'''
    abstract_index = {
        'neural': [0],
        'networks': [1, 4],
        'learn': [2],
        'representations': [3],
    }

    abstract = abstract_from_inverted_index(abstract_index)

    assert abstract == 'neural networks learn representations networks'


def test_search_work_prefers_openalex_id() -> None:
    '''curated OpenAlex IDs should bypass title search'''
    class FakePage:
        data = {
            'id': 'https://openalex.org/W123',
            'title': 'test work',
            'publication_year': 2012,
            'topics': [],
        }

    class FakeClient:
        def get(self, endpoint: str, params: dict) -> FakePage:
            self.endpoint = endpoint
            self.params = params
            return FakePage()

    client = FakeClient()
    row = search_work(client, query='ignored', openalex_id='https://openalex.org/W123')

    assert client.endpoint == 'works/W123'
    assert row['openalex_id'] == 'https://openalex.org/W123'


def test_search_works_returns_normalised_rows() -> None:
    '''loose work search should return normalised rows'''
    class FakePage:
        results = [
            {
                'id': 'https://openalex.org/W123',
                'title': 'test work',
                'topics': [],
            },
        ]

    class FakeClient:
        def get(self, endpoint: str, params: dict) -> FakePage:
            self.endpoint = endpoint
            self.params = params
            return FakePage()

    client = FakeClient()
    rows = search_works(client, 'test query', per_page=1)

    assert client.endpoint == 'works'
    assert client.params['search'] == 'test query'
    assert rows[0]['openalex_id'] == 'https://openalex.org/W123'


def test_manual_prehistory_exclusions_are_flagged() -> None:
    '''known false records should not enter feature tables quietly'''
    assert work_is_excluded('https://openalex.org/W3194025661')
