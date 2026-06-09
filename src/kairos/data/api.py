'''
Created on Fri Jun  5 2026

a toy OpenAlex API client

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

import os
import time
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

from kairos.data.config import OPENALEX_API_KEY_ENV, OPENALEX_BASE_URL, PROJECT_ROOT


#%% exceptions
class OpenAlexError(RuntimeError):
    '''raised when OpenAlex returns an unusable response'''


#%% response container
@dataclass(frozen=True)
class OpenAlexPage:
    endpoint: str
    params: dict[str, Any]
    data: dict[str, Any]
    response_headers: dict[str, str]

    @property
    def results(self) -> list[dict[str, Any]]:
        return list(self.data.get('results', []))

    @property
    def meta(self) -> dict[str, Any]:
        return dict(self.data.get('meta', {}))

    @property
    def groups(self) -> list[dict[str, Any]]:
        return list(self.data.get('group_by', []))


#%% client
class OpenAlexClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = OPENALEX_BASE_URL,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> OpenAlexClient:
        '''create a client from the local environment file'''
        load_dotenv(env_file or PROJECT_ROOT / '.env')
        return cls(api_key=os.getenv(OPENALEX_API_KEY_ENV))

    def get(
        self,
        endpoint: str,
        params: Mapping[str, Any] | None = None,
    ) -> OpenAlexPage:
        '''send one OpenAlex request with retry handling'''
        request_params = dict(params or {})
        if self.api_key:
            request_params['api_key'] = self.api_key

        clean_endpoint = endpoint.lstrip('/')
        url = f'{self.base_url}/{clean_endpoint}'
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = httpx.get(url, params=request_params, timeout=self.timeout_seconds)
                if response.status_code in {429, 500, 502, 503, 504}:
                    raise OpenAlexError(
                        f'OpenAlex returned transient status {response.status_code}'
                    )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise OpenAlexError('OpenAlex response was not a JSON object')
                return OpenAlexPage(
                    endpoint=endpoint,
                    params=safe_params(request_params),
                    data=data,
                    response_headers=dict(response.headers),
                )
            except (httpx.HTTPError, OpenAlexError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(self.backoff_seconds * (2**attempt))

        raise OpenAlexError(f'OpenAlex request failed for {endpoint}') from last_error

    def iter_cursor_pages(
        self,
        endpoint: str,
        params: Mapping[str, Any] | None = None,
        per_page: int = 100,
        max_pages: int | None = None,
        start_cursor: str = '*',
        include_empty: bool = False,
    ) -> Iterator[OpenAlexPage]:
        '''yield cursor pages, optionally starting from a saved cursor'''
        cursor = start_cursor
        pages_seen = 0
        while True:
            page_params = dict(params or {})
            page_params['cursor'] = cursor
            page_params['per-page'] = per_page
            page = self.get(endpoint, page_params)
            if not page.results:
                if include_empty:
                    yield page
                break
            yield page

            pages_seen += 1
            cursor = page.meta.get('next_cursor')
            if not cursor:
                break
            if max_pages is not None and pages_seen >= max_pages:
                break


#%% helpers
def safe_params(params: Mapping[str, Any]) -> dict[str, Any]:
    '''redact secrets before request parameters are stored'''
    safe = dict(params)
    if 'api_key' in safe:
        safe['api_key'] = '<redacted>'
    return safe
