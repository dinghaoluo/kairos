'''
Created on Fri Jun 5 2026

config parameters for fetching from OA and probably feature 
engineering in the future as well 

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
CURATION_DATA_DIR  = DATA_DIR / 'curation'


#%% OpenAlex API
OPENALEX_BASE_URL = 'https://api.openalex.org'
OPENALEX_API_KEY_ENV = 'OPENALEX_API_KEY'


#%% search window
# pull a long prehistory tail before McCulloch and Pitts
START_YEAR = 1800

# start the first model ten years before McCulloch and Pitts
MODEL_START_YEAR = 1933

# keep 2026 out because the current year is still being indexed
END_YEAR = 2025


#%% candidate boundaries
@dataclass(frozen=True)
class BoundaryLayer:
    key: str
    level: str
    ids: tuple[str, ...]
    fetch_works: bool = True


CANDIDATE_TOPIC_QUERIES = (
    'neural networks',
    'artificial neural networks',
    'deep learning',
    'machine learning',
)

# core NN topics
CORE_NEURAL_NETWORK_TOPIC_IDS = (
    'T10320',
    'T10036',
    'T11273',
    'T10775',
)

# nearby machine-learning topics
ADJACENT_ML_TOPIC_IDS = (
    'T12072',
    'T12535',
    'T10028',
    'T10181',
)

# broader boundaries inherited from the neural-network topic checks
COMPARISON_BOUNDARY_SUBFIELD_IDS = (
    '1702',
    '1707',
)

LOGIC_MATH_BACKGROUND_SUBFIELD_IDS = (
    '1703',
)

BROAD_BACKGROUND_FIELD_IDS = (
    '17',
)

BOUNDARY_LAYERS = (
    BoundaryLayer(
        key='core_nn',
        level='primary_topic',
        ids=CORE_NEURAL_NETWORK_TOPIC_IDS,
    ),
    BoundaryLayer(
        key='adjacent_ml',
        level='primary_topic',
        ids=ADJACENT_ML_TOPIC_IDS,
    ),
    BoundaryLayer(
        key='broad_cs',
        level='field',
        ids=BROAD_BACKGROUND_FIELD_IDS,
        fetch_works=False,
    ),
    BoundaryLayer(
        key='ai_cv_background',
        level='subfield',
        ids=COMPARISON_BOUNDARY_SUBFIELD_IDS,
        fetch_works=False,
    ),
    BoundaryLayer(
        key='logic_math_background',
        level='subfield',
        ids=LOGIC_MATH_BACKGROUND_SUBFIELD_IDS,
        fetch_works=False,
    ),
)

# keep one flat candidate union for quick diagnostic checks
CANDIDATE_BOUNDARY_TOPIC_IDS    = CORE_NEURAL_NETWORK_TOPIC_IDS + ADJACENT_ML_TOPIC_IDS
CANDIDATE_BOUNDARY_SUBFIELD_IDS = COMPARISON_BOUNDARY_SUBFIELD_IDS
CANDIDATE_BOUNDARY_FIELD_IDS    = BROAD_BACKGROUND_FIELD_IDS


#%% manual exclusions
SPURIOUS_WORKS_CURATION_FILE = CURATION_DATA_DIR / 'pre_1933_core_nn.csv'

# old hand-typed exclusions, kept here only as a note after moving to CSV
# SPURIOUS_WORKS = {
#     'https://openalex.org/W3194025661': '1800 false hit: title/source do not look like a scholarly work',
#     'https://openalex.org/W3024112564': '1801 false hit: medical case report, not neural-network history',
#     'https://openalex.org/W2042025359': '1827 false hit: optical lens polishing, not neural-network history',
# }


#%% pinned landmark papers
# boundary sanity checks, not final 'breakthrough' labels
@dataclass(frozen=True)
class PinnedLandmarkPaper:
    key: str
    title: str
    publication_year: int
    doi: str | None = None
    openalex_id: str | None = None
    openalex_year: int | None = None
    boundary_required: bool = True


PINNED_LANDMARK_PAPERS = (
    PinnedLandmarkPaper(
        key='mcculloch_pitts_1943',
        title='A logical calculus of the ideas immanent in nervous activity',
        publication_year=1943,
        doi='10.1007/bf02478259',
        openalex_id='W1995341919',
        boundary_required=False,
    ),
    PinnedLandmarkPaper(
        key='rosenblatt_1958',
        title='The perceptron: a probabilistic model for information storage and organization in the brain',
        publication_year=1958,
        doi='10.1037/h0042519',
        openalex_id='W2040870580',
    ),
    PinnedLandmarkPaper(
        key='hopfield_1982',
        title='Neural networks and physical systems with emergent collective computational abilities',
        publication_year=1982,
        doi='10.1073/pnas.79.8.2554',
        openalex_id='W2128084896',
    ),
    PinnedLandmarkPaper(
        key='rumelhart_hinton_williams_1986',
        title='Learning representations by back-propagating errors',
        publication_year=1986,
        doi='10.1038/323533a0',
        openalex_id='W1498436455',
    ),
    PinnedLandmarkPaper(
        key='lecun_bottou_bengio_haffner_1998',
        title='Gradient-based learning applied to document recognition',
        publication_year=1998,
        doi='10.1109/5.726791',
        openalex_id='W2112796928',
    ),
    PinnedLandmarkPaper(
        key='hinton_osindero_teh_2006',
        title='A fast learning algorithm for deep belief nets',
        publication_year=2006,
        doi='10.1162/neco.2006.18.7.1527',
        openalex_id='W2136922672',
    ),
    PinnedLandmarkPaper(
        key='krizhevsky_sutskever_hinton_2012',
        title='ImageNet classification with deep convolutional neural networks',
        publication_year=2012,
        openalex_id='W2163605009',
        openalex_year=2017,
    ),
    PinnedLandmarkPaper(
        key='mikolov_chen_corrado_dean_2013',
        title='Efficient Estimation of Word Representations in Vector Space',
        publication_year=2013,
        doi='10.48550/arxiv.1301.3781',
        openalex_id='W1614298861',
    ),
    PinnedLandmarkPaper(
        key='goodfellow_2014',
        title='Generative Adversarial Networks',
        publication_year=2014,
        doi='10.48550/arxiv.1406.2661',
        openalex_id='W4298289240',
    ),
    PinnedLandmarkPaper(
        key='he_zhang_ren_sun_2016',
        title='Deep Residual Learning for Image Recognition',
        publication_year=2016,
        doi='10.1109/CVPR.2016.90',
        openalex_id='W2194775991',
    ),
)
