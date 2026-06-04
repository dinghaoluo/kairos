# Kairos: *Sternstunden der Menschheit*

*Can the structural state of a scientific field predict whether a breakthrough is coming?*

*Work started on 3 June 2026.*

**Working title:** Kairos (καιρός), 3 June 2026
**Author:** Dinghao Luo
**Repo:** `kairos`

---

## The big questions

Revolutionary ideas do not succeed solely because of individual genius. They rely on the right intellectual, societal, and methodological conditions. Many significant findings were first met with inopportune conditions and only later became rediscovered and recognised. For example, Mendel published in 1866 and was ignored for 34 years; when de Vries, Correns, and Tschermak independently 'renaissanced' his laws in 1900, the field had caught up. Similarly, Wegener proposed continental drift in 1912 and was ridiculed; plate tectonics was accepted in the 1960s when new evidence from ocean-floor spreading made the field receptive.

[Kuhn (*The Structure of Scientific Revolutions*, 1962)](https://press.uchicago.edu/ucp/books/book/chicago/S/bo13179781.html) described this as the structure of scientific revolutions: normal science accumulates anomalies until conditions are ripe for a paradigm shift. The Kuhnian paradigm shift refers to drastic changes in people's thinking that break open the at-the-time established ideas. Going back to the plate tectonics example. The Earth's surface had been interpreted as a fixed arrangement; Wegener's drift hypothesis lacked a convincing mechanism, but [Hess's seafloor-spreading model (1962)](https://doi.org/10.1130/petrologic.1962.599) and the [Vine-Matthews magnetic-anomaly evidence (1963)](https://doi.org/10.1038/199947a0) supplied one, and the whole discipline reoriented within a decade. Moments like these are, in Zweig's words, 'Sternstunden der Menschheit': *kairos* that steer the course of human knowledge.

However, Kuhn's account is qualitative, and qualitative analyses can only go so far. That is why I want to ask: **can we measure the 'ripeness' of a field, of a social environment, from publication data? Can we predict, from the structural features of the environment, whether conditions favour scientific breakthroughs?** The data infrastructure to test this seriously did not exist until recently: [OpenAlex](https://openalex.org/) indexes hundreds of millions of works with citation links, author affiliations, and topic tags at multiple granularities. From this, it is now possible to construct a quantitative snapshot of a field's structural state at a given time: how fragmented the community is, how concentrated attention has become, how rapidly new subtopics are emerging, whether recent work consolidates or disrupts the *status quo*. I call this snapshot the 'zeitgeist vector' (following the accidental German theme... from Zweig's *Sternstunden* mentioned above). Should the zeitgeist vector carry a predictive signal, the consequences would extend beyond historiography. It would suggest that some part of scientific 'ripeness' is not merely a retrospective narrative, but a measurable structural property of a field. In the long run, this could matter for funding bodies, institutional planners, and researchers themselves, as a way to diagnose when a field's structure is shifting in ways that have historically preceded major work. It may also help reinterpret delayed-recognition cases like Mendel's not simply as 'bad luck', but as a measurable mismatch between idea and environment.

This question is all the more relevant now: many are asking whether breakthroughs are becoming rarer. (Appropriating Fukuyama's sociological term: are we reaching 'the end of history' in science?) [Park, Leahey, & Funk (*Nature*, 2023)](https://doi.org/10.1038/s41586-022-05543-x) found declining average disruption in science over 65 years (1945–2010), noting that the absolute number of disruptive papers may be constant, but diluted by the growing volume. This nonetheless is far from the consensus. For instance, [Petersen, Arroyave, & Pammolli (*Quantitative Science Studies*, 2024)](https://doi.org/10.1162/qss_a_00333) argued that citation inflation and secular growth had mechanically deflated Park *et al.*'s disruption index over time. If the preliminary pipeline works, I will extend it to two related questions: whether top-percentile disruptive papers are becoming rarer in frequency, and whether delayed-recognition papers 'awaken' under measurable field-state changes.

---

## Method summary

The core project:

1. **Feature engineering** (zeitgeist vector): for each field-year, I will compute structural features of the publication record (publication dynamics, network topology, topic diversity, disruption/impact proxies, plus case-by-case social/industrial annotations for interpretation). An exploratory phase on the field of neural networks (1955–2025) will decide which features enter the model.
2. **Predictive modelling**: I will train a paper-level breakthrough classifier (logistic regression, gradient-boosted trees) on labelable publication years (1970–~2020, constrained by the 5-year observation window needed for labels), evaluated with temporal expanding-window cross-validation.
3. **Case-study interpretation and visualisation**: overlay model predictions on historical narrative for the primary cases; an interactive Astro site (similar to how [the-zone-site](https://dinghaoluo.github.io/the-zone-site/) has been implemented) can be used for storytelling.

Possible extensions (if the core pipeline works):

- **Survival analysis**: for delayed-recognition papers, model time-to-recognition as a function of field-state covariates using Cox proportional hazards with time-varying covariates.
- **Causal inference**: difference-in-differences around the NIH 2008 open-access mandate to test whether open access shortens recognition time.
- **Velocity analysis**: change-point detection on annual breakthrough frequency to engage with the Park *et al.* (2023) declining-disruption debate.

---

## Detailed methods

### The zeitgeist vector: operationalising field-state features

At the centre of this project will be the zeitgeist vector, which is a quantitative snapshot of a field's structural state at a given time. The question, then, is which features matter. I will begin with an exploratory phase on neural networks (1955–2025), computing every reasonable candidate feature over time and inspecting which ones change visibly before known breakthroughs. If time allows, I will repeat for information theory (1948–2020) as a sanity check. I will use this phase to narrow the candidate feature set.

Some candidate features, grouped by source, are as follows:

**1. Publication dynamics**

- Publication count and growth rate (log year-on-year change)
- New-author influx rate (proportion of authors publishing in the field for the first time)
- Institutional diversity (Herfindahl index of author affiliations)
- Geographic spread (entropy of country distribution)

**2. Network topology** ([Traag, Waltman, & van Eck, 2019](https://doi.org/10.1038/s41598-019-41695-z) for community detection)

- Community modularity (Traag *et al.*'s Leiden algorithm cited above)
- Citation Gini coefficient ([Nielsen & Andersen, 2021](https://doi.org/10.1073/pnas.2012208118))
- Average shortest path length in the citation graph
- Proportion of cross-community edges (boundary-spanning work)

**3. Topic landscape** ([Uzzi *et al.*'s 2013 *Science* paper](https://doi.org/10.1126/science.1240474) for novelty measures)

- Topic diversity (entropy of OpenAlex topic tags)
- Novelty index (average cosine distance of recent papers from the field's topic centroid)
- Emergence rate of new subtopics (new topic tags appearing per year)
- Atypical combination rate (papers citing unusual pairs of topics, following Uzzi *et al.*)

**4. Disruption and consolidation** ([Funk & Owen-Smith, 2017](https://doi.org/10.1287/mnsc.2015.2366) originated the CD index; [Wu, Wang, & Evans's 2019 *Nature* work](https://doi.org/10.1038/s41586-019-0941-9) applied it to science; [Xu *et al.*'s 2025 paper](https://doi.org/10.1038/s41597-025-06232-w) for CrossDI dataset)

- Disruption-related labels: CD5/CD10 where available from CrossDI as a benchmark; otherwise citation-spike and cross-field uptake proxies (included only for domains/subsamples where CD scores are available or computed)
- Proportion of consolidating vs. disruptive papers per year (where CD is computable)
- Mean and tail (95th percentile) of disruption scores (where CD is computable)

**5. External signals**

- Open-access proportion (from OpenAlex metadata)
- Industry vs. academic author ratio (via affiliation type)
- Funding-adjacent signals (where available in OpenAlex funder data)

**6. Social and industrial context** (not computable from OpenAlex; will not enter the preliminary predictive model)

- Enabling technologies (GPU computing for deep learning, sonar mapping for plate tectonics, MCMC algorithms for Bayesian revival)
- Economic conditions (compute cost, cloud availability, funding climate)
- Institutional shifts (new journals, conferences, research centres)

These will be used to interpret model output in the case studies, not as features in the first model.

### A predictive model of scientific breakthrough

A scientific 'breakthrough' is operationalised as any paper meeting the following curated set of criteria:

- CD5/CD10 above threshold where available; otherwise a separate breakthrough proxy based on field-normalised citation spike and cross-field uptake
- Citation spike exceeding 3 standard deviations above the field's baseline within 5 years of publication
- Cross-disciplinary uptake (cited by at least N distinct fields within 5 years; 10-year uptake reserved for robustness checks on older papers)
- Additional domain-specific markers (e.g. methodological papers, Nobel-linked papers, papers that spawn new subfields)

I will manually inspect a sample of papers meeting these thresholds to check they actually look like breakthroughs. If the label yields enough positives across fields, I will train a multi-field model; otherwise the first version stays at the case-study level (neural networks only).

**Feature engineering**: For each paper, I will compute the zeitgeist vector for the field-year in which the paper was published. Additional paper-level features:

- Author experience (mean publications per author at time of publication)
- Institutional prestige (*via* affiliation; included as a control, not a feature I expect to celebrate)
- Interdisciplinarity of the paper's reference list
- Novelty of the paper's topic combination, following [Uzzi *et al.* (*Science*, 2013)](https://doi.org/10.1126/science.1240474)

**Model comparison**: I need to distinguish genuine predictive signal from artefacts of model complexity. I will therefore compare a hierarchy of models, each adding flexibility:

- Null baseline: predict breakthrough at the base rate, which is the floor; if no model beats it, the zeitgeist vector has no signal.
- Logistic regression with L1 regularisation: a linear model that selects features by shrinking uninformative ones to zero. If this already beats the null, the signal is simple and interpretable.
- Gradient-boosted trees (XGBoost/LightGBM) with class-weight adjustment for imbalance: captures non-linear interactions between features. If this substantially outperforms logistic regression, the signal has structure that linear models miss.

If the question turns out to be better posed as 'when' rather than 'whether', a random survival forest (reframing the target as time-to-breakthrough) is a natural extension.

**Validation**: Temporal expanding-window cross-validation: train on all data up to year Y, predict Y+1 to Y+N, slide forward. The reason is straightforward: citation-derived features encode post-publication history, so a paper's 2020 citation profile cannot be used to predict events at its 2005 publication date. Features must be frozen at the observation date. Temporally shuffled k-fold violates this by letting later observations leak into the training set.

**Evaluation**: The dataset is heavily imbalanced (breakthroughs are rare), so standard accuracy is meaningless and ROC-AUC can remain deceptively high because the false-positive rate is diluted by the enormous negative class. I will use precision-recall curves and average precision as the primary metrics, supplemented by calibration plots and Brier score decomposition. The criterion is whether the model outperforms the null at useful precision levels.

**Interpretability**: I will use SHAP feature importance, following [Lundberg & Lee (*NeurIPS*, 2017)](https://proceedings.neurips.cc/paper_files/paper/2017/file/8a20a8621978632d76c43dfd28b67767-Paper.pdf). Which features of the intellectual environment predict breakthroughs? I will report partial dependence plots for the top features and test whether interaction effects (e.g. high topic diversity combined with high community fragmentation) improve prediction.

And lastly, **what if the model fails?** If the zeitgeist vector has no predictive signal above base rate, I take that seriously: it would mean breakthroughs are not predictable from field-state features alone, and the Kuhnian 'ripeness' hypothesis might be weaker than people expect.

### Sensitivity and robustness

There is an abundance of arbitrariness in the criterion set used in feature engineering here, and if a result only holds at one specific parameter setting, it is an artefact of that setting. I will therefore vary the main operationalisation choices: breakthrough threshold (disruption cutoff, citation spike multiplier, cross-field uptake count), temporal aggregation window (1-year vs 3-year vs 5-year), and field boundary level in the OpenAlex hierarchy (subfield vs topic). The question is whether the same zeitgeist features remain predictive across reasonable parameter ranges.

### Extension sketches

These are sketches. I will build them if the core works.

### Survival analysis: time-to-recognition for delayed-recognition papers

For papers that were ignored initially but later recognised (the phenomenon catalogued by [van Raan (*Scientometrics*, 2004)](https://doi.org/10.1023/B:SCIE.0000018543.82441.f1) and [Ke *et al.* (*PNAS*, 2015)](https://doi.org/10.1073/pnas.1424329112)), I will model time-to-recognition as a function of field-state covariates at the time of original publication.

Kaplan-Meier curves stratified by field fragmentation can answer the basic question: do ideas published during consolidated periods wait longer? The risk set includes all eligible low-initial-attention papers, with non-awakened papers right-censored at the end of observation. For multivariate analysis I will compare two specifications: baseline field-state covariates measured at publication, and time-varying field-state covariates updated during the dormancy period. I will test the proportional hazards assumption with Schoenfeld residuals ([Grambsch & Therneau, 1994](https://doi.org/10.1093/biomet/81.3.515)) and adjust the model accordingly if violated. Concordance index (Harrell's C) will be the primary evaluation metric. [Burrell, 2002](https://doi.org/10.1023/A:1019671808921) and [Eom & Fortunato, 2011](https://doi.org/10.1371/journal.pone.0024926) provide precedent for survival/hazard modelling of citation dynamics.

### Causal inference: does open access speed recognition?

The open-access citation advantage is widely claimed but poorly established causally (most studies compare self-selected OA papers to non-OA papers, conflating quality with access). The NIH Public Access Policy, which became mandatory on 7 April 2008 after being voluntary from 2005, provides a natural experiment: NIH-funded papers published after that date must be deposited in PubMed Central within 12 months, regardless of the authors' preference. I will use difference-in-differences ([Angrist & Pischke, *Mostly Harmless Econometrics*, 2009](https://press.princeton.edu/books/paperback/9780691120355/mostly-harmless-econometrics)) to compare citation trajectories of NIH-funded papers (treatment) to non-NIH-funded papers in the same fields and journals (control) around the 2008 mandate date. The outcome variable is citation count at 5 years post-publication. Limitations: the 12-month embargo blurs the access discontinuity, and compliance ramped up gradually rather than switching overnight; I will discuss these in the analysis.

I will use event-study pre-trends and placebo tests to assess the parallel-trends assumption. If I construct a matched treated/control design, I will add Rosenbaum bounds ([Rosenbaum, *Observational Studies*, 2002](https://doi.org/10.1007/978-1-4757-3692-2)) as a hidden-bias sensitivity check; otherwise I will rely on alternative control groups and robustness to matching specifications.

### Velocity analysis: are breakthroughs becoming rarer?

Park *et al.* found that average disruption in science has declined over 65 years. But averages can mislead: if extreme events (the top 0.01% most disruptive papers) are constant while the denominator of total publications grows, the average falls even though breakthroughs are not becoming rarer. I want to test this directly.

I will construct a time-series of breakthrough frequency per year (1970–2025, giving 56 annual data points). Change-point detection can identify whether there is a structural break in this series: did something shift at a particular moment, or has the rate been stable? I will use PELT ([Killick, Fearnhead, & Eckley, 2012](https://doi.org/10.1080/01621459.2012.737745)) as the primary method and Bayesian online change-point detection ([Adams & MacKay, 2007](https://arxiv.org/abs/0710.3742)) as a robustness check. If a change-point is detected, I will characterise the regime shift: did breakthrough frequency drop, or did it plateau while volume exploded? I will attempt a restricted reproduction of the Park *et al.* finding using available disruption datasets or a sampled OpenAlex citation network, then re-run on the tails only to see if it holds.

### Visualisation

The visualisation will be presented on an interactive Astro site similar to how [the-zone-site](https://dinghaoluo.github.io/the-zone-site/) is presented.

The first version will show:

- Timeline of each field's evolution with zeitgeist features as background layers
- Breakthrough moments annotated with the model's prediction at that point
- Network evolution snapshots at key moments (pre-breakthrough vs. post-breakthrough community structure)
- SHAP waterfall plots showing which features drove the prediction

If extensions get built:

- Kaplan-Meier curves for time-to-recognition
- Velocity dashboard: breakthrough frequency over time, with the Park *et al.* debate visualised

---

## Data sources and feasibility

### OpenAlex ([Priem, Piwowar, & Orr, 2022](https://arxiv.org/abs/2205.01833))

I will use OpenAlex as the primary data source; it is freemium, with free bulk snapshots and a daily free-quota API sufficient for prototyping, and covers 480M+ works with citation links, author affiliations, topics at four hierarchical levels (domain → field → subfield → topic), venues, open-access status, and funder data.

However the problem is that coverage is strong from ~1950 onward but gets thin before that. [Culbert *et al.* (*Scientometrics*, 2025)](https://doi.org/10.1007/s11192-025-05293-3) looked at this: metadata (titles, authors, years) exists back to the 1600s, but citation links for pre-1950 papers are very incomplete. Mendel's 1866 paper exists in OpenAlex (W3119707353, 556 citations) but inbound citations are mostly from post-2000 papers with DOIs — the historical citation chain (papers from the 1900s citing Mendel) is largely absent because those citing papers lack machine-readable reference lists.

What this means is that post-1950 cases (neural networks, information theory, place cells) have all the features I need to compute the zeitgeist vector, while pre-1950 cases (Mendel, continental drift) work for reception analysis but not for computing the zeitgeist vector at time of original publication.

### CrossDI ([Xu *et al.* (*Scientific Data*, 2025)](https://doi.org/10.1038/s41597-025-06232-w))

Pre-computed disruption indices (CD5/CD10) across Web of Science, Dimensions, and OpenCitations for selected domains. Computing CD5 from scratch via OpenAlex is impractical (three-hop citation queries per paper, hundreds of thousands of API calls for a single field-year). I will use CrossDI as a validation benchmark, not as the primary label source, and for OpenAlex-scale modelling I will need to approximate disruption with citation-spike and cross-field uptake criteria.

### The hard parts

The hardest problem is label construction. 'Breakthrough' is not a natural kind; it is a retrospective judgement I am trying to operationalise with proxy metrics (disruption scores, citation spikes, cross-field uptake). These proxies do not agree with each other, and they probably do not fully agree with historians' lists either. My preliminary model will use a deliberately crude composite label and I will treat it as a working approximation instead of ground truth.

The second hard problem is that disruption indices are expensive to compute at scale from OpenAlex (three-hop citation queries per paper) and CrossDI only covers selected domains in Web of Science, Dimensions, and OpenCitations. For most of the OpenAlex corpus, I will not have pre-computed CD5 values. I may end up approximating disruption with citation-spike and cross-field uptake criteria alone, which loses the precise Funk & Owen-Smith construction.

Third, the pre-1950 cases (Mendel, Wegener) have thin citation data. I can tell the story of their reception after 1950, but the zeitgeist vector at the time of original publication will have missing features. For this reason, these cases will be more about narrative and reception analysis.

---

## Case studies

Neural networks is the testbed — everything gets built and validated there first (the field-year table, the zeitgeist vector, the breakthrough label, the classifier), and if the pipeline produces nonsense on neural networks, where I know the history well enough to smell a bad result, it fails early and I do not waste time extending it. Place cells are the second case, one I know from the Wang lab, and a test of whether the pipeline generalises to a smaller field with different dynamics. Mendel and continental drift are narrative anchors and reception analyses; I am not pretending I can compute a full zeitgeist vector for 1866.

### Primary cases

**1. Neural networks (1958 / 1986 / 2012)**
Three waves: Rosenblatt's perceptron (1958), killed by Minsky/Papert (1969); backpropagation revival (Rumelhart/Hinton/Williams, 1986), faded by late 1990s; deep learning explosion (Krizhevsky/Sutskever/Hinton, 2012). The same core idea proposed three times under radically different conditions, and what distinguished the moments is precisely the structural question this project asks: compute availability, dataset sizes, adjacent-field progress, and institutional support all varied across the three waves. OpenAlex coverage is strong across all three periods, making this ideal for the exploratory phase.

**2. Place cells and the cognitive map (O'Keefe 1971 / Nobel 2014)**
O'Keefe discovered place cells in 1971; the work was respected but niche for decades, then became central to neuroscience once spatial cognition, memory consolidation, and navigation research converged around it (Nobel Prize in 2014). I know this case intimately from the Wang lab, and the question here is whether the zeitgeist vector picks up the convergence before the Nobel committee does.

**3. Information theory across disciplines (Shannon 1948 onwards)**
Shannon published in the Bell System Technical Journal, and information theory crossed into linguistics (1950s), biology (genetic code as information, 1960s), neuroscience (neural coding, 1970s-80s), and machine learning (1990s-2000s), each crossing at a different pace under different conditions. This is the 'immediately picked-up' case: Shannon was recognised quickly in engineering but took decades to diffuse elsewhere, which makes it useful for testing whether the zeitgeist vector can distinguish fast uptake from slow diffusion.

**4. Mendel's genetics (1866 / 1900)**
The archetypal delayed-recognition case: Mendel published in a reputable journal to no effect, and thirty-four years later three scientists independently rediscovered the same laws within months. What changed? Cell biology had matured; chromosomes had been observed; Weismann had theorised about hereditary material — the field built the scaffolding Mendel's ideas needed to land on. The zeitgeist vector at 1866 will be partial (publication counts and institutional diversity are computable, but citation networks and topic tags are not), so this is a narrative case, not a quantitative test case.

**5. Continental drift / plate tectonics (1912 / 1960s)**
Wegener proposed drift in 1912 with substantial evidence, but was rejected for decades — not because the evidence was weak, but because no mechanism was known and the geological establishment was hostile — until Hess (1962), Vine-Matthews (1963), and Wilson's transform faults created a mechanistic framework in the 1960s. Sonar mapping (developed during WWII) enabled the ocean-floor evidence, a classic case of military-funded instrumentation enabling breakthrough. Like Mendel, this is primarily a narrative and reception analysis.

### Additional cases (will not be analysed individually)

- Bayesian statistics (Bayes 1763 / Laplace 1810s / computational revival 1990s-2000s with MCMC)
- Germ theory / Semmelweis (1847 / Pasteur & Koch 1870s-80s)
- CRISPR-Cas9 (Mojica 1993 / Doudna & Charpentier 2012)
- Quantum mechanics (Planck 1900 / Heisenberg & Schrödinger 1925-26)
- Transformer architecture (Vaswani *et al.* 2017)
- Prions (Prusiner 1982 / Nobel 1997)

If the velocity analysis is implemented, these may appear as high-disruption or citation-spike examples, but they will not receive individual case-study pages.

---

## Existing literature, differentiation, and significance statement

The closest precedent is [Prabhakaran *et al.* (*Scientometrics*, 2018)](https://doi.org/10.1007/s11192-018-2931-3), who attempted paradigm shift prediction from bibliometric features. Their approach was limited by small N; the zeitgeist vector addresses that. [Zhang & Evans (*arXiv*, 2025)](https://arxiv.org/abs/2509.05591) predict paper-level surprise using LLM perplexity, but the unit of analysis is the individual paper, not the field-state moment. [Davis *et al.* (*bioRxiv*, 2025)](https://doi.org/10.64898/2025.12.16.694385) showed co-citation signals can predict biomedical breakthroughs 12 years early; I use a broader feature set across all domains rather than co-citation topology alone.

On the disruption debate: [Park, Leahey, & Funk (*Nature*, 2023)](https://doi.org/10.1038/s41586-022-05543-x) found declining average disruption over 65 years. I am not interested in the average; I want to know whether the tails (top 0.01%) are also declining in frequency. [Kim, Kojaku, & Ahn (*Science Advances*, 2026)](https://doi.org/10.1126/sciadv.adx3420) connect simultaneous breakthroughs to Merton's multiple discovery thesis using a robust disruption measure; I take the next step and ask what conditions predict when multiples happen.

I use [Uzzi *et al.* (*Science*, 2013)](https://doi.org/10.1126/science.1240474) only for the intuition that atypical combinations can be quantified; I am not reproducing their exact z-score construction. [Ke *et al.* (*PNAS*, 2015)](https://doi.org/10.1073/pnas.1424329112) identified delayed-recognition papers at scale; I model time-to-recognition as a function of field conditions, asking why some papers wait rather than cataloguing which ones did.

I have not found work that asks the prior question: what was the state of the field *before* the breakthrough, and can that state predict whether one is coming? Existing work either measures disruption at the paper level, identifies delayed-recognition papers after the fact, or predicts impact from textual novelty. That is what this project tries to do.