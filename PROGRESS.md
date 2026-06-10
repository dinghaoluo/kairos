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
    - now we have a boundary-checking script (`diagnostic_check_boundary.py`). This script searches candidate topics, checks pinned landmark papers, runs negative-control searches, compares yearly counts, and prints a small top-cited sample so we can see what the boundary actually outputs
    - the helper scripts are also improved: `api.py` can now read OpenAlex grouped-count responses (see above); `work.py` keeps the topic/subfield/field hierarchy and citation count for each returned work; `search_works()` handles the actual OpenAlex lookup while `search_work()` just returns the first match for specific searches; and `topics.py` can count a topic/subfield/field boundary by year, including a union of topics (see above)
- we should still refrain from a full data pull. Maybe build with a layered approach? Like a core neural-network layer, an adjacent-ML layer, and a wider CS/science background layer on top of each other, and then we can fetch a small sample from each layer and ask whether the layers behave differently over time

## 20260609-20260610
- started the actual data incremental pull and finished the core-nn and adjacent-ml pulls
- we shoudl keep the OA returns as JSON pages since the returns contain nested topic hierarchies, source metadata, authorships, institutions, referenced works, yearly citation histories, and sometimes abstract indexes; we can always flatten them into parquet or csv later 
- the data layout is now: 
    - `data`
        - `raw`
            - `works`
                - `core_nn`
                - `adjacent_ml`
            - `abstracts`
                - `core_nn`
                - `adjacent_ml`
            - `counts`
                - `core_nn`
                - `adjacent_ml`
                - `cs`
                - `ai_cv`
                - `logic_comp_theory`
- changed the boundary from one large topic union into layers. `core_nn` and `adjacent_ml` are close enough to pull as work records, because they may enter the first model directly; however the wider computer-science etc. layers are only yearly counts for now
- revised the time window after checking McCulloch and Pitts. The first model should start in 1933, ten years before the 1943 paper, so that there is some pre-breakthrough lookback
    - we are also pulling the older/prehistoric tail to see what was there but there are some spurious hits in that period; created a curation table for manual labelling of the prehistoric records; should be careful about pulling and trusting older works from OA in the future
- `fetch_boundary.py` pulls the boundary works incrementally into the data layout above and is resumable so that we don't re-pull everything even if budget runs out for the day
    - hit a cursor problem where if a year ends on a full page, OA may still provide another cursor, and the next request can then return an empty final page. The first version of the script saved only real pages, so it could not always know whether the previous page was genuinely exhausted. Now there is a `mark_exhaust()` function that checks the empty cursor and marks the previous page as exhausted
- added `fetch_abstracts.py` as a separate backfill: OA actually returns the abstract in inverted indices which can be reconstructed later so we are storing the same inverted index arrays for now
- added `inventory_works.py` which outputs to `data/processed/inventory_works.csv`
- we can start building the first zeitgeist vector from here
