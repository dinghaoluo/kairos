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
- OpenAlex topic search seems to be quite noisy. For example, 'neural networks' gives a central topic but the related phrases produce application-heavy results that do not pertain that much to the pillar papers... We therefore need to do some landmark checking tomorrow to make sure that the main works are within bounds

## 20260608
- deciding what is meant by the 'neural-network field' has been harder than I had expected because OpenAlex topics are not following clean historical definitions of the field:
    - landmark lookup was a big problem, as loose title/year searches for things like 'AlexNet' could return low-citation record classified under really niche subfields... (e.g. brain-tumour work). Therefore we decided to curated all the 'pinned' landmark papers instead of relying purely on research results
    - also had to make a decision on category granularity. The topic `T10320` works well for Rosenblatt and backpropagation, but was too narrow for later neural-network history (AlexNet 2012 did not fall in `T10320`) and therefore we needed a union list of the main topics around neural networks, advanced neural-network applications, ML classification/algorithms, GANs etc.
- code-wise:
    - now we have a comprehensive preprocessing script (`preprocessing_check_boundary.py`). This script searches candidate topics, checks pinned landmark papers, runs negative-control searches, compares yearly counts, and prints a small top-cited sample so we can see what the boundary actually outputs
    - the helper scripts are also improved: `api.py` can now read OpenAlex grouped-count responses (see above); `work.py` keeps the topic/subfield/field hierarchy and citation count for each returned work; `search_works()` handles the actual OpenAlex lookup while `search_work()` just returns the first match for specific searches; and `topics.py` can count a topic/subfield/field boundary by year, including a union of topics (see above)
- we should still refrain from a full data pull. Maybe build with a layered approach? Like a core neural-network layer, an adjacent-ML layer, and a wider CS/science background layer on top of each other, and then we can fetch a small sample from each layer and ask whether the layers behave differently over time
