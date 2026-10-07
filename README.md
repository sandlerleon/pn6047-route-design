# A literature-based modular route-design strategy for scalable manufacture of PN6047

Leon Sandler, Independent Researcher — sandler.leon@gmail.com
ORCID [0009-0007-4584-808X](https://orcid.org/0009-0007-4584-808X)

This repository holds the data, screening model, tests, figure scripts and manuscript builder behind the paper *"A Literature-Based Modular Route-Design
Strategy for Scalable Manufacture of PN6047"* (prepared for the **Journal of Pharmaceutical Innovation**). Every number and figure of the manuscript
is produced by the scripts here from the plain JSON inputs in `data/`.

**No synthesis was performed and nothing here predicts a yield, impurity level, cost or timeline.** The study inventories the operations that are *publicly
exemplified* for the drug substance of PN6047 (patent documents WO 2016/099393 and WO 2022/013153, PharmNovo AB), grades the public evidence for each, flags
documented regulatory and hazard attributes, screens two proposed variants, and tests how robust a risk ranking is to the author's own uncertainty. The author is
not affiliated with the patent applicant, and no freedom-to-operate analysis was made.

## What the screening shows

| | R0 (exemplified route) | R1 (process-oriented variant) | R2 (alternative ordering) |
|---|---|---|---|
| Steps *N* (*u* = 2 undisclosed upstream steps) | 7 | 6 | 5 |
| Documented flag instances | **11** | 3 | 3 |
| Evidence of conditions (A/B/C/D) | 5/0/0/0 | 0/1/1/2 | 0/0/0/3 |
| Validation burden (linear weights) | 2 | **11** | **15** |

The ordering of the routes by flags (R0 highest) and by validation burden (R0 lowest) holds for every weighting scheme and for *u* = 1–4. Removing documented flags
(a Class 1 solvent, a benzotriazole-derived coupling reagent, preparative HPLC, lyophilisation) raises the burden of proof, because the replacement conditions are
unvalidated. Of twelve risks, two stay in the top three in about 87 % of ±1 perturbations of the author's ratings: impurity purge when crystallisation replaces
chromatography (K1) and the undisclosed upstream route to the vinyl bromide building block (K2); no other risk exceeds 24 %.

**A correction.** Pramipexole is a benchmark for manufacture of a basic thiazole-containing API, not a source of fragments: its tetrahydrobenzothiazole-diamine core is
not a substructure of PN6047, whose thiazole is an unsubstituted thiazol-5-yl attached through a methylene group to the piperidine nitrogen.

## Layout

```
data/routes.json       route inventories R0-R2: steps, conditions, scale, evidence class of transformation and conditions, flags, sources
data/flags.json        the documented flags and what each was checked against (ICH Q3C(R8), Q3D(R2), patent examples, Wehrstedt 2005)
data/precedents.json   the precedent map (what the public record shows, remaining uncertainty)
data/risks.json        the risk register (author's likelihood/impact ratings, basis, validation experiment)
code/route_model.py    metrics, evidence-weighted burden under three weightings, risk-ranking perturbation analysis -> results/results.json
code/test_model.py     15 checks: data integrity, regulatory flags, formula and [M+H]+ against the masses printed in the patent, determinism
code/make_figures.py   Figures 1-3 (RDKit structures; 300 dpi)
refs/build_refs.py     harvests every journal reference from Crossref (nothing typed by hand) -> refs/refs_cache.json
manuscript/            builder (reads results.json), cover letter builder, manuscript v1 and cover letter
tools/                 Zenodo deposit scripts (token read from ZENODO_TOKEN, never stored)
```

## Reproducing

```bash
pip install -r requirements.txt
python refs/build_refs.py            # needs internet (Crossref)
python code/test_model.py            # runs route_model.py twice and checks the output is byte-identical
python code/route_model.py
python code/make_figures.py
cd manuscript && python build_manuscript.py && python build_manuscript.py && python build_cover_letter.py
```

The risk analysis uses a fixed seed (20261006, 20 000 draws), so the output is deterministic.

## What was and was not verified

The text of the two patents (Google Patents) was searched and read for the passages on synthesis, purification and salt forms; the ICH guidelines were consulted for the
limits quoted (Q3A(R2), Q3C(R8), Q3D(R2), Q11). For most journal articles the Crossref/Europe PMC record and abstract were examined, not the full text; the search was
purposive, not systematic. The machine-readable text of WO 2016/099393 has an inconsistency in the compound named for its Example III, which is why only the reagent
class of that example is used.

## Citation

Software: [10.5281/zenodo.23200174](https://doi.org/10.5281/zenodo.23200174) (concept DOI 10.5281/zenodo.23200173). Manuscript preprint:
[10.5281/zenodo.23200178](https://doi.org/10.5281/zenodo.23200178).

MIT licence.
