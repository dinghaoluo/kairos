'''
Created on Fri Jun 5 2026

configuration for the first Kairos fetch boundary

@author: Dinghao Luo
'''

#%% imports
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


#%% paths
PROJECT_ROOT       = Path(__file__).resolve().parents[3]
DATA_DIR           = PROJECT_ROOT / 'data'
RAW_DATA_DIR       = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'


#%% OpenAlex API
OPENALEX_BASE_URL = 'https://api.openalex.org'
OPENALEX_API_KEY_ENV = 'OPENALEX_API_KEY'


#%% search window
# define the search window for neural network papers
START_YEAR = 1955
END_YEAR   = 2025


#%% candidate field boundaries
# these strings are only used to resolve candidate OpenAlex topics
CANDIDATE_TOPIC_QUERIES = (
    'neural networks',
    'artificial neural networks',
    'deep learning',
    'machine learning',
)


#%% sentinel papers
@dataclass(frozen=True)
class SentinelPaper:
    key: str
    title: str
    publication_year: int
    doi: str | None = None
    openalex_id: str | None = None


SENTINEL_PAPERS = (
    SentinelPaper(
        key='rosenblatt_1958',
        title='The perceptron: a probabilistic model for information storage and organization in the brain',
        publication_year=1958,
        doi='10.1037/h0042519',
    ),
    SentinelPaper(
        key='rumelhart_hinton_williams_1986',
        title='Learning representations by back-propagating errors',
        publication_year=1986,
        doi='10.1038/323533a0',
    ),
    SentinelPaper(
        key='krizhevsky_sutskever_hinton_2012',
        title='ImageNet classification with deep convolutional neural networks',
        publication_year=2012,
    ),
)


#%% sentinel exclusions
SENTINEL_EXCLUSION_QUERIES = (
    'pure chemistry',
    'literary criticism',
)
