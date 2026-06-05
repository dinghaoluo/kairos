'''
Created on Fri Jun  5 2026

test the small OpenAlex client helpers

@author: Dinghao Luo
'''

#%% imports
from kairos.data.api import safe_params


#%% tests
def test_safe_params_redacts_api_key() -> None:
    '''the API key should not leak into stored logs'''
    params = safe_params({'api_key': 'secret', 'search': 'neural networks'})

    assert params['api_key'] == '<redacted>'
    assert params['search'] == 'neural networks'
