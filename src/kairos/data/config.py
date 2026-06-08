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


#%% candidate boundaries
# these strings are only used to resolve candidate OpenAlex topics
CANDIDATE_TOPIC_QUERIES = (
    'neural networks',
    'artificial neural networks',
    'deep learning',
    'machine learning',
)

# topic IDs to test as a first candidate union
CANDIDATE_BOUNDARY_TOPIC_IDS = (
    'T10320',
    'T10036',
    'T11273',
    'T12072',
    'T12535',
    'T10775',
    'T10028',
    'T10181',
)

# broader boundaries inherited from the neural-network topic candidate
CANDIDATE_BOUNDARY_SUBFIELD_IDS = (
    '1702',
    '1707',
)

CANDIDATE_BOUNDARY_FIELD_IDS = (
    '17',
)


#%% landmark papers
@dataclass(frozen=True)
class LandmarkPaper:
    key: str
    title: str
    publication_year: int
    doi: str | None = None
    openalex_id: str | None = None


LANDMARK_PAPERS = (
    LandmarkPaper(
        key='rosenblatt_1958',
        title='The perceptron: a probabilistic model for information storage and organization in the brain',
        publication_year=1958,
        doi='10.1037/h0042519',
        openalex_id='W2040870580',
    ),
    LandmarkPaper(
        key='hopfield_1982',
        title='Neural networks and physical systems with emergent collective computational abilities',
        publication_year=1982,
        doi='10.1073/pnas.79.8.2554',
        openalex_id='W2128084896',
    ),
    LandmarkPaper(
        key='rumelhart_hinton_williams_1986',
        title='Learning representations by back-propagating errors',
        publication_year=1986,
        doi='10.1038/323533a0',
        openalex_id='W1498436455',
    ),
    LandmarkPaper(
        key='lecun_bottou_bengio_haffner_1998',
        title='Gradient-based learning applied to document recognition',
        publication_year=1998,
        doi='10.1109/5.726791',
        openalex_id='W2112796928',
    ),
    LandmarkPaper(
        key='hinton_osindero_teh_2006',
        title='A fast learning algorithm for deep belief nets',
        publication_year=2006,
        doi='10.1162/neco.2006.18.7.1527',
        openalex_id='W2136922672',
    ),
    LandmarkPaper(
        key='krizhevsky_sutskever_hinton_2012',
        title='ImageNet classification with deep convolutional neural networks',
        publication_year=2012,
        openalex_id='W2163605009',
    ),
    LandmarkPaper(
        key='mikolov_chen_corrado_dean_2013',
        title='Efficient Estimation of Word Representations in Vector Space',
        publication_year=2013,
        doi='10.48550/arxiv.1301.3781',
        openalex_id='W1614298861',
    ),
    LandmarkPaper(
        key='goodfellow_2014',
        title='Generative Adversarial Networks',
        publication_year=2014,
        doi='10.48550/arxiv.1406.2661',
        openalex_id='W4298289240',
    ),
    LandmarkPaper(
        key='he_zhang_ren_sun_2016',
        title='Deep Residual Learning for Image Recognition',
        publication_year=2016,
        doi='10.1109/CVPR.2016.90',
        openalex_id='W2194775991',
    ),
)


#%% boundary exclusions
BOUNDARY_EXCLUSION_QUERIES = (
    'experimental organic synthesis',
    'relational database systems',
    'quantum chromodynamics',
    'literary criticism',
)
