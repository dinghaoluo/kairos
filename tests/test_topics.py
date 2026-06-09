'''
Created on Fri Jun  5 2026

test OpenAlex topic helpers

@author: Dinghao Luo
'''

#%% imports
from kairos.data.topics import boundary_filter, count_boundary_works_by_year, normalise_topic


#%% tests
def test_boundary_filter_keeps_level_and_year() -> None:
    '''boundary filters should combine IDs before adding the year'''
    text = boundary_filter(
        'primary_topic',
        ('https://openalex.org/T10320', 'T10036'),
        publication_year=2012,
    )

    assert text == 'primary_topic.id:T10320|T10036,publication_year:2012'


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


def test_count_boundary_works_by_year_uses_requested_level() -> None:
    '''boundary counts should use the selected OpenAlex hierarchy level'''
    class FakePage:
        groups = [
            {'key': '1950', 'count': 1},
            {'key': '2012', 'count': 42},
        ]

    class FakeClient:
        def get(self, endpoint: str, params: dict) -> FakePage:
            self.endpoint = endpoint
            self.params = params
            return FakePage()

    client = FakeClient()
    rows = count_boundary_works_by_year(
        client,
        'topic',
        ('T10320', 'T10036'),
        1955,
        2025,
    )

    assert client.endpoint == 'works'
    assert client.params['filter'] == 'topics.id:T10320|T10036'
    assert rows == [{'publication_year': 2012, 'works_count': 42}]
