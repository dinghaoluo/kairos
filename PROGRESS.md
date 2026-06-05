# Progress 

## 20260605 
- properly started the coding side of the project; created the main scripts handling queries:
    - `config.py` contains the choices of papers, topics etc.
    - `api.py` is a wrapper for the API calls to OpenAlex 
    - `work.py` normalises returned work record (e.g. papers) into simple rows
    - `topics.py` is boundary checks after flattening returned topics from OpenAlex
- some chore scripts...
    - `.env` contains the API key 
    - `.gitignore` of course 
    - `pyproject.toml` for dependencies and packaging
- two test scripts that have been run successfully 
    - `test_api.py` tests the API wrapper and returned data correctly 
    - `test_topics.py`
- OpenAlex topic search seems to be quite noisy. For example, 'neural networks' gives a central topic but the related phrases produce application-heavy results that do not pertain that much to the pillar papers... We there fore need to do some sentinel checking tomorrow to make sure that the main works are within bounds