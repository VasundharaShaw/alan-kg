# alan-literature-mining

A pipeline that mines the scientific literature on artificial light at night (ALAN) and turns it into a knowledge graph about how light is measured. It is built to answer one question: **how can light measurement methods be harmonized across disciplinary boundaries?** (Q1 of Hölker et al. 2021, "11 pressing research questions on how light pollution affects biodiversity").

> **Status: work in progress.** See [Current status](#current-status) for what works today and what is still planned.

## Why this exists

Astronomers, lighting engineers, ecologists and biologists all measure light, but they use different instruments, quantities and units (lux, cd/m², W/m², mag/arcsec², µmol/m²/s, ...). This makes results hard to compare. This project collects what the literature says about methods, quantities, units, disciplines and studied organisms, and structures it as a graph of linked statements ("triples") that can be queried, for example:

- Which disciplines use which measurement methods?
- Which quantities does each method measure?
- Which units report each quantity, and who reports them?
- Which papers mention a given method?

The graph is intended to be hosted in a Wikibase instance.

## How it works

1. **Fetch** papers from OpenAlex (and later Europe PMC) for a defined search and date window. The current window is two years: 27 October 2024 to 27 October 2026.
2. **Match** the title and abstract of each paper against controlled word lists (rules, no machine learning).
3. **Tabulate** the results as a CSV: one row per paper, with the matched terms per category.
4. **Flag scope** by marking papers about human health, rather than biodiversity, as off-topic (see [Scope: biodiversity, not human health](#scope-biodiversity-not-human-health)).
5. **Mark** duplicate records and peer-review records (decision letters, author responses) in two extra columns, without deleting any rows.
6. **Curate** a seed set of statements by hand from review papers (`kg/seed_statements.csv`).
7. **Map** matched words to knowledge-graph items with `kg/term_map.csv` (a method or discipline word without a row becomes an item of its own), and write one "paper mentions item" statement per match (`data/output/mentions.csv`).
8. **Build** a small local graph (rdflib) from the curated statements plus the paper-mentions statements, and query it for two questions from `questions.md`.

The work is done in rounds: scan with the current word lists, review what was missed, extend the lists, scan again.

## Repository structure

```
alan-literature-mining/
├── README.md
├── plan.md                  # plan and criteria for "enough"
├── questions.md             # questions the graph should answer, with expected answers
├── requirements.txt         # pinned Python packages
├── vocab/
│   └── terms.py             # word lists: search terms, methods, quantities, units, disciplines, taxa, human-health terms
├── src/
│   └── fetch_openalex.py    # downloads papers from OpenAlex into a CSV
├── notebooks/
│   └── 01_explore_openalex.ipynb   # term matching, scope flag, summary numbers, output table
├── kg/
│   ├── seed_statements.csv  # hand-curated statements (subject, property, object, source)
│   ├── items.csv            # class of each item (quantity, instrument, spectral band, ...)
│   └── term_map.csv         # word-list term -> KG item, with match type (exact or broad)
└── data/
    ├── raw/                 # downloaded data (not tracked by Git)
    └── output/              # result tables (not tracked by Git)
```

## Setup

You need Python 3.9 or newer and Git.

```bash
git clone https://github.com/VasundharaShaw/alan-kg.git
cd alan-kg
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data/raw data/output
```

### OpenAlex API key

OpenAlex offers a free API key, which gives a much larger daily budget than anonymous use. Create an account at openalex.org, copy your key from the API settings page, and make it available as an environment variable (never write it into the code or commit it):

```bash
export OPENALEX_API_KEY="your-key"
```

The variable lasts for the current terminal window only.

### Working behind a proxy or VPN

If your institution sets proxy variables in the terminal and downloads fail with "Cannot connect to proxy", you can clear them for the current window:

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
```

## Usage

**1. Download the papers**

```bash
python src/fetch_openalex.py
```

This queries OpenAlex for `"artificial light at night"`, English-language works published between 2024-10-27 and 2026-10-27, pages through all results (100 per request) and writes `data/raw/openalex_alan.csv` with these columns:

| Column | Meaning |
|---|---|
| `first_author` | display name of the first author |
| `year` | publication year |
| `venue` | journal or source |
| `title` | paper title |
| `doi` | DOI |
| `is_open_access` | whether the paper is open access |
| `abstract` | abstract, rebuilt from OpenAlex's word-position index |

**2. Match terms**

Open `notebooks/01_explore_openalex.ipynb` in VS Code, select the `.venv` kernel, and run the cells. The notebook adds one column per category (`methods`, `quantities`, `units`, `disciplines`, `species`) listing the terms found in each paper's title and abstract, then the scope columns `human_health` and `scope` (see below), prints summary numbers, and saves the table to `data/output/table_abstracts.csv`. The table keeps all the columns of the raw download.

After editing `vocab/terms.py`, restart the kernel and run all cells again, because Python keeps the old word lists in memory. A progress log at the top of the notebook records the effect of each change to the word lists.

## Word lists and matching rules

All vocabulary lives in `vocab/terms.py` as plain Python lists, so it can be reviewed and edited without touching the code. The first version was drawn from Hölker et al. (2021) and is extended in rounds using Dickerson et al. (2026).

- Abbreviations in capitals (for example SQM, PAR, DSLR) must match exactly, so that they do not match ordinary words.
- Other terms ignore case and also match a plural ("moth" matches "moths").
- Terms match whole words only, and a term must start at a word boundary: "bird" does not match "seabird" and "fish" does not match "zebrafish". Compounds and irregular plurals ("mouse" and "mice") need their own entries.
- `HUMAN_HEALTH` is not one of the five categories. It is used only for the scope flag below.
- Species are found with a word list of taxa, not with a language model. This is transparent and reproducible, but only finds what is on the list.

## Scope: biodiversity, not human health

The search phrase also returns many papers on human health (sleep, circadian disruption, cancer and similar). The project follows Hölker et al. (2021), which is about biodiversity, so these papers are off-topic unless they are about animals. The notebook flags them with word lists, not with a classifier:

- A paper is **flagged** when its title and abstract contain a word from `HUMAN_HEALTH` in `vocab/terms.py` and no species word from `TAXA`.
- Flagged papers are split three ways in the `scope` column:
  - `off-topic`: two or more health terms, or one strong term (for example cancer, patient, diabetes)
  - `unsure`: one weak term only (for example sleep, participant, clinical); these are read by hand
  - `in scope`: everything else

Because the animal exception depends on the taxa list, an animal paper whose organism is not yet listed can be flagged, which is why animal terms are added to `TAXA` as they turn up. Laboratory rodents (mouse, mice, rat) are currently treated as animals and stay in scope. The notebook prints samples of flagged papers so the rule can be checked by eye.

## The seed knowledge graph

`kg/seed_statements.csv` holds statements entered by hand from review papers, currently Table 1 of Dickerson et al. (2026). Each row is one triple with its source:

```
subject,property,object,source
illuminance,reported_in,lx,Dickerson 2026 Table 1
```

Rules for this file: lowercase spelling throughout, one value per cell, no commas inside values, plain-text units (`W/m2/sr`, `umol/m2/s`).

| Property | Meaning |
|---|---|
| `reported_in` | a quantity is reported in a unit |
| `used_by` | a quantity or instrument is typically used by a discipline or user group |
| `photometric_version_of` | the quantity weighted by human eye sensitivity |
| `spectral_version_of` | the wavelength-resolved version of a quantity |
| `photon_version_of` | the photon-count version of a quantity |
| `expresses` | a quantity or unit expresses another quantity |
| `given_in_band` | a quantity is given in a spectral band |
| `measures` | an instrument measures a quantity |
| `can_derive` | an instrument can derive a quantity |
| `often_reported_for` | a quantity is often reported for a purpose |

## The toy graph at a glance

Two layers are kept apart. Teal boxes are curated by hand from Dickerson et al. (2026), Table 1. Purple boxes are found only by mining abstracts. An arrow from the papers box means "paper mentions item", and its number is how many papers mention it. The mined layer is what connects papers to the curated quantities, units and instrument. The picture is a selection (5 of 9 quantities, one unit each, not every statement), based on the run of 20 November 2026.

```mermaid
flowchart TB
    P["ALAN papers<br/>1,525 used"]

    subgraph mined["Mined only, from abstracts"]
        sat["satellite"]
        rs["remote sensing"]
        radm["radiometer"]
        sqm["Sky Quality Meter"]
        cons["conservation"]
        ns["night sky"]
        sg["skyglow"]
        tour["tourism"]
    end

    subgraph seed["Curated seed graph"]
        ill["illuminance"]
        lum["luminance"]
        rdn["radiance"]
        irr["irradiance"]
        nsb["night sky brightness"]
        lx["lx"]
        cdm2["cd/m2"]
        wsr["W/m2/sr"]
        wm2["W/m2"]
        mag["mag/arcsec2"]
        le["lighting engineers"]
        eco["ecologists"]
        ast["astronomers"]
        msid["multispectral imaging device"]

        ill -- reported_in --> lx
        lum -- reported_in --> cdm2
        rdn -- reported_in --> wsr
        irr -- reported_in --> wm2
        nsb -- reported_in --> mag
        ill -- used_by --> le
        ill -- used_by --> eco
        irr -- used_by --> eco
        rdn -- used_by --> ast
        nsb -- used_by --> ast
        msid -- measures --> rdn
        msid -- measures --> lum
    end

    P -- "68" --> sat
    P -- "36" --> rs
    P -- "20" --> radm
    P -- "10" --> sqm
    P -- "232" --> cons
    P -- "41" --> ns
    P -- "22" --> sg
    P -- "22" --> tour
    P -- "98" --> lx
    P -- "43" --> rdn
    P -- "35" --> ill
    P -- "25" --> nsb
    P -- "8" --> msid

    classDef papers fill:#eeeeee,stroke:#888888,color:#000
    classDef minedc fill:#EEEDFE,stroke:#534AB7,color:#000
    classDef seedc fill:#E1F5EE,stroke:#0F6E56,color:#000
    class P papers
    class sat,rs,radm,sqm,cons,ns,sg,tour minedc
    class ill,lum,rdn,irr,nsb,lx,cdm2,wsr,wm2,mag,le,eco,ast,msid seedc
```

The words "conservation", "night sky", "skyglow" and "tourism" are fields and topics, not measurement items, so a link between them and a method only shows that both words appear in the same abstract.

## Known limitations

- A match in an abstract means a term is **mentioned**, not that a method was **used**. Links derived from word-list matches mean "mentioned together".
- Papers without an abstract (about 9% of the first download) can only be matched on their title.
- Only titles and abstracts are scanned. Instruments, methods and units usually appear in the Methods section, so they are under-reported compared with species and disciplines.
- Word lists match surface forms; unlisted terms, spelling variants and synonyms are missed until they are added.
- Short tokens (for example "bat", "W") can produce false hits and need review.
- Results depend on the search phrase, so some relevant papers may not be retrieved yet.
- The scope flag is rule-based and approximate: an animal missing from the taxa list can be flagged as human health, which is why the `unsure` group is read by hand.
- Duplicates are found only by identical title (after ignoring case and punctuation). A preprint whose title was reworded for publication is not caught. Duplicates and peer-review records are marked in `is_duplicate` and `is_review_record`, not deleted.
- Some papers never mention light in a meaningful way (for example "References" or book reviews) and some titles are not in English. Neither is filtered out yet.
- `term_map.csv` marks each row `exact` or `broad`. Broad rows are approximate (for example "multispectral" for the item "multispectral imaging device"), and a broad match is stored under a separate property, `mentions_broadly`, so it can be left out of a query.
- The "disciplines" list also holds topic words (conservation, tourism, regulation, night sky, skyglow, urban planning, lighting design). Question 2 therefore shows which fields and topics appear together with which methods, which is co-occurrence and not evidence that a field used a method.
- Only quantity, unit and method words with a map row, plus method and discipline words (as items of their own), produce graph statements. In the latest run, 1,069 statements came from 668 of 1,525 papers (44%).
- `dose-response` is in the methods list but is a statistical term, not a measurement method, so it gives a few false hits.

## Progress so far

Snapshot from 20 November 2026. Green boxes are done, grey boxes are still to do.

```mermaid
flowchart TD
    A["Fetch from OpenAlex<br/>2,227 papers, 2 years<br/>(27 Oct 2024 - 27 Oct 2026)"]:::done --> B["Match title + abstract<br/>against word lists"]:::done
    B --> C["1,613 match at least one term (72%)"]:::done
    B --> D["614 match nothing (28%)"]:::done
    A --> E["Scope flag<br/>human health vs biodiversity"]:::done
    E --> F["1,668 in scope"]:::done
    E --> G["455 off-topic"]:::done
    E --> H["104 unsure, read by hand"]:::done
    A --> M1["Mark duplicates (29)<br/>and peer-review records (18)"]:::done
    F --> I["277 of 1,668 in scope still match nothing (17%)"]:::todo
    I --> J["Further word-list rounds, junk and language filter"]:::todo
    S["Seed KG: 40 triples from<br/>Dickerson et al. 2026 Table 1"]:::done --> K["Classify the 16 remaining items"]:::todo
    F --> L["Map matched words to KG items<br/>(kg/term_map.csv)"]:::done
    M1 --> L
    L --> N["1,069 mention statements<br/>from 668 of 1,525 papers"]:::done
    N --> P["Separate fields from topics<br/>(conservation, tourism, ...)"]:::todo
    N --> Q["Local graph (rdflib):<br/>78 curated + 1,796 mined triples"]:::done
    S --> Q
    Q --> R["Q1 and Q2 answered<br/>(methods; fields with methods)"]:::done
    R --> O["Draft note to Franz Hölker"]:::todo
    classDef done fill:#d4edda,stroke:#2d6a4f,color:#000
    classDef todo fill:#eeeeee,stroke:#888888,color:#000
```

Word-list progress, with the effect of each change on the number of papers that match no term:

| Date | Change to the word lists | Papers with no match |
|---|---|---|
| 17 Nov | Starting lists (from Hölker et al. 2021) | 949 of 2,227 |
| 17 Nov | + zebrafish, elasmobranch, shark | 938 |
| 17 Nov | + seabird, petrel, Procellariiformes | 937 |
| 18 Nov | + Drosophila, deer, mouse, mice, rat, lizard, anole, frog, amphipod, chipmunk, epiphyte, wildlife | 804 |
| 19 Nov | + animals (mosquito, cricket, mussel, insect, ...), sky and policy words, first extension of the health list | 637 |
| 19 Nov | Health list pruned (words that also apply to animals removed), seed-item terms added (luminance, cd/m2, ...) | 614 |

Scope on 19 November: 1,668 papers in scope, 455 off-topic, 104 unsure. Of the 1,668 in-scope papers, 277 (17%) match no term in any category.

Duplicates and peer-review records: 29 rows are marked as duplicates (identical title) and 18 as peer-review records. After removing both and the 109 papers without a DOI, 1,525 papers feed the graph.

Paper-mentions statements: the latest run produced 1,069 statements (1,058 exact, 11 broad) from 668 of the 1,525 papers. The most frequent items are conservation (232), regulation (106), ecology (99), lx (98), satellite (68), radiance (43) and illuminance (35); the first three are topic words, not measurement items. Eight map terms were never found in the kept papers (PAR, W/m2, cd/m2, magnitudes per square arcsecond, spectral irradiance, spectral radiance, umol/s, umol photons). A check showed that they are rare or absent in abstracts and not a matching fault, as expected because units and instruments are mostly reported in the Methods section.

First answers from the local graph (78 curated and 1,796 mined triples):
- Question 1, methods mentioned and in how many papers: satellite 68, remote sensing 36, radiometer 20, Sky Quality Meter 10, multispectral imaging device 8, hyperspectral 6, drone 5.
- Question 2, fields and topics with methods in the same paper: conservation with satellite (11) and remote sensing (10); night sky with Sky Quality Meter (7) and satellite (7); tourism with satellite (5).

## Current status

**Working**
- Download of all OpenAlex results for the phrase "artificial light at night" (2,227 papers, 27 Oct 2024 to 27 Oct 2026)
- Term matching on titles and abstracts with an output table
- Scope flag: a simple flag and a three-way `scope` column (human health versus biodiversity)
- Marking of duplicates (`is_duplicate`) and peer-review records (`is_review_record`)
- Word-list changes tracked in a progress log in the notebook
- Seed statements from Dickerson et al. (2026), Table 1: 40 triples, 27 items, 11 of them classified in `kg/items.csv`
- A term map (`kg/term_map.csv`) and "paper mentions item" statements (`data/output/mentions.csv`)
- A small local graph with rdflib (curated and mined statements kept in separate graphs), and questions 1 and 2 of `questions.md` answered against it

**Planned**
- Separate fields from topics in the word lists, and merge more method synonyms in the term map
- Questions 3 to 6 of `questions.md` (for example the change in method mentions from 2024 to 2026)
- Classes for the 16 unclassified seed items, and loading into a Wikibase instance
- Additional search phrases (light pollution, skyglow, night sky brightness, ...), and removal of near-duplicate records
- A flag for papers that never mention light, and a language filter
- Further word-list rounds for the remaining unmatched in-scope papers
- Europe PMC as a second source
- Open versus closed datasets: the `is_open_access` column already marks them, and a second table from the full text of open-access papers is planned
- Seed statements from Table 2 (measurement techniques)
- Validation against hand-read abstracts

## How to tell when it is "enough"

The graph is considered good enough when (1) it reproduces the expected answers in `questions.md`, (2) a new scanning round adds very few new terms, and (3) a hand check of 30 to 50 random abstracts shows an acceptable error rate. Details are in `plan.md`.

## Sources

- Hölker, F. et al. (2021). 11 pressing research questions on how light pollution affects biodiversity. *Frontiers in Ecology and Evolution* 9:767177. https://doi.org/10.3389/fevo.2021.767177
- Dickerson, A. L. et al. (2026). Understanding and managing ecological light pollution. *Nature Reviews Biodiversity*. https://doi.org/10.1038/s44358-026-00206-5
- OpenAlex: https://openalex.org

## Author

Vasundhara Shaw

## License

Released under the [MIT License](LICENSE).