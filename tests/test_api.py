'''
Created on Fri Jun  5 2026

test the small OpenAlex client helpers

@author: Dinghao Luo
'''

#%% imports
from kairos.data.api import OpenAlexClient, OpenAlexPage, safe_params


#%% tests
def test_safe_params_redacts_api_key() -> None:
    '''the API key should not leak into stored logs'''
    params = safe_params({'api_key': 'secret', 'search': 'neural networks'})

    assert params['api_key'] == '<redacted>'
    assert params['search'] == 'neural networks'


def test_cursor_pages_can_start_from_saved_cursor() -> None:
    '''cursor paging should be resumable from a saved cursor'''
    class FakeClient(OpenAlexClient):
        def get(self, endpoint: str, params: dict) -> OpenAlexPage:
            self.endpoint = endpoint
            self.params = params
            return OpenAlexPage(
                endpoint=endpoint,
                params=params,
                data={'results': [{'id': 'W123'}], 'meta': {'next_cursor': None}},
                response_headers={},
            )

    client = FakeClient()
    pages = list(
        client.iter_cursor_pages(
            'works',
            {'filter': 'topics.id:T10320'},
            start_cursor='saved-cursor',
            max_pages=1,
        )
    )

    assert client.endpoint == 'works'
    assert client.params['cursor'] == 'saved-cursor'
    assert len(pages) == 1


def test_cursor_pages_can_expose_empty_final_page() -> None:
    '''exact-multiple cursor pulls should be markable as exhausted'''
    class FakeClient(OpenAlexClient):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        def get(self, endpoint: str, params: dict) -> OpenAlexPage:
            self.calls += 1
            if self.calls == 1:
                return OpenAlexPage(
                    endpoint=endpoint,
                    params=params,
                    data={'results': [{'id': 'W123'}], 'meta': {'next_cursor': 'next'}},
                    response_headers={},
                )
            return OpenAlexPage(
                endpoint=endpoint,
                params=params,
                data={'results': [], 'meta': {'next_cursor': None}},
                response_headers={},
            )

    client = FakeClient()
    pages = list(
        client.iter_cursor_pages(
            'works',
            {'filter': 'topics.id:T10320'},
            include_empty=True,
        )
    )

    assert len(pages) == 2
    assert pages[-1].results == []
