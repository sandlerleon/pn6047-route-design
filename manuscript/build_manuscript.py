# -*- coding: utf-8 -*-
"""Builds the manuscript for the Journal of Pharmaceutical Innovation (Springer, Research Article) from results/results.json and data/*.json.

Every number in the text is read from the model output (tokens @name@); the text asserts the relations it states (orderings, ranges).

    python build_manuscript.py          (run twice so that table numbers resolve)   ->  out/PN6047_Route_Design_v2.docx
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import docx_helpers as H  # noqa: E402

OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
RES = json.load(open(os.path.join(ROOT, "results", "results.json"), encoding="utf-8"))
ROUTES = json.load(open(os.path.join(ROOT, "data", "routes.json"), encoding="utf-8"))
RISKS = json.load(open(os.path.join(ROOT, "data", "risks.json"), encoding="utf-8"))["risks"]
PREC = json.load(open(os.path.join(ROOT, "data", "precedents.json"), encoding="utf-8"))
REFS = json.load(open(os.path.join(ROOT, "refs", "refs_cache.json"), encoding="utf-8"))
ZEN = json.load(open(os.path.join("C:" + os.sep, "YouTube", "_pn6047_zenodo_state.json"))) if os.path.exists(
    os.path.join("C:" + os.sep, "YouTube", "_pn6047_zenodo_state.json")) else None
SW_DOI = (ZEN.get("software_1.1.0") or ZEN["software"])["doi"] if ZEN else "10.5281/zenodo.XXXX"
PP_DOI = (ZEN.get("publication_v2") or ZEN["publication"])["doi"] if ZEN else "10.5281/zenodo.YYYY"
REPO = "https://github.com/sandlerleon/pn6047-route-design"
VERSION = os.environ.get("MS_VERSION", "2")

# ---------------------------------------------------------------- numbers from the model
D = {k: v["default"] for k, v in RES["routes"].items()}
SW = {k: v["u_sweep"] for k, v in RES["routes"].items()}
ORD = RES["burden_order_least_to_most"]
assert all(o == ["R0", "R1", "R2"] for sc in ORD.values() for o in sc.values()), "burden ordering changed: revise the Results text"
assert all(SW["R0"][u]["flag_instances"] > SW["R1"][u]["flag_instances"] == SW["R2"][u]["flag_instances"] for u in SW["R0"]), "flag relation changed"
RK = RES["risks"]
top2 = RES["risk_order_by_score"][:2]
assert sorted(top2) == ["K1", "K2"] and all(RK[k]["p_top3"] > 0.8 for k in top2) and all(RK[k]["p_top3"] < 0.3 for k in RK if k not in top2)
BE, RV, PR = RES["break_even"], RES["reversal"], RES["priors"]
# propositions stated in Section 2.7; the build stops if the output contradicts them
assert D["R0"]["flag_instances"] > D["R1"]["flag_instances"] and D["R0"]["validation_burden"]["linear"] < D["R1"]["validation_burden"]["linear"], "P1 fails"
assert all(BE[sc][u]["R1_vs_R2"] == 0 for sc in BE for u in BE[sc]), "R2 no longer dominated by R1"
assert RV["leaders"] == ["K1", "K2"] and set(RV["points_to_bring_leader_to_cluster"].values()) == {2} and set(RV["points_to_bring_cluster_member_to_leader"].values()) == {2}
assert min(PR["narrow"][k] for k in top2) > 0.9 and PR["wide"][top2[0]] > max(v for k, v in PR["wide"].items() if k not in top2), "P3 fails"
BEMIN = min(BE[sc][u]["R0_vs_R1"] for sc in BE for u in BE[sc])
BEMAX = max(BE[sc][u]["R0_vs_R1"] for sc in BE for u in BE[sc])
V = {
    "be01": "%.2f" % BE["linear"]["2"]["R0_vs_R1"], "be01min": "%.2f" % BEMIN, "be01max": "%.1f" % BEMAX,
    "be02lo": "%.2f" % min(BE["linear"][u]["R0_vs_R2"] for u in BE["linear"]), "be02hi": "%.2f" % max(BE["linear"][u]["R0_vs_R2"] for u in BE["linear"]),
    "rvgap": RV["points_to_bring_leader_to_cluster"]["K1"], "rvlead": RV["leader_score"], "rvclus": RV["cluster_score"],
    "pnar": "%d" % round(100 * min(PR["narrow"][k] for k in top2)), "pwide": "%d" % round(100 * min(PR["wide"][k] for k in top2)),
    "pwidemax": "%d" % round(100 * max(v for k, v in PR["wide"].items() if k not in top2)),
    "pnarmax": "%d" % round(100 * max(v for k, v in PR["narrow"].items() if k not in top2)),
    "n0": D["R0"]["steps_total"], "n1": D["R1"]["steps_total"], "n2": D["R2"]["steps_total"],
    "nr0": "%d–%d" % (SW["R0"]["1"]["steps_total"], SW["R0"]["4"]["steps_total"]),
    "nr1": "%d–%d" % (SW["R1"]["1"]["steps_total"], SW["R1"]["4"]["steps_total"]),
    "nr2": "%d–%d" % (SW["R2"]["1"]["steps_total"], SW["R2"]["4"]["steps_total"]),
    "f0": D["R0"]["flag_instances"], "f1": D["R1"]["flag_instances"], "f2": D["R2"]["flag_instances"],
    "df0": D["R0"]["distinct_flags"], "sf0": D["R0"]["steps_with_any_flag"],
    "b0": D["R0"]["validation_burden"]["linear"], "b1": D["R1"]["validation_burden"]["linear"], "b2": D["R2"]["validation_burden"]["linear"],
    "c0": D["R0"]["validation_burden"]["convex"], "c1": D["R1"]["validation_burden"]["convex"], "c2": D["R2"]["validation_burden"]["convex"],
    "d0": D["R0"]["validation_burden"]["binary_D"], "d1": D["R1"]["validation_burden"]["binary_D"], "d2": D["R2"]["validation_burden"]["binary_D"],
    "i0": "%.2f" % D["R0"]["ideality"], "i1": "%.2f" % D["R1"]["ideality"], "i2": "%.2f" % D["R2"]["ideality"],
    "p1": "%d" % round(100 * (RK["K1"]["p_top3"] + RK["K2"]["p_top3"]) / 2), "p2": "%d" % round(100 * RK["K2"]["p_top3"]),
    "pmax": "%d" % round(100 * max(RK[k]["p_top3"] for k in RK if k not in top2)),
    "nhigh": RES["n_high_risks"], "mc": "{:,}".format(RES["n_monte_carlo"]),
    "u": RES["default_u"], "seed": RES["seed"],
    "sw": SW_DOI, "pp": PP_DOI,
}
SC = RES["structure_checks"]
V["mh1"], V["mh2"], V["mh3"] = (SC[k]["mh_calc"] for k in SC)
V["mw"] = SC["PN6047 (Example Ib)"]["mw"]

# ---------------------------------------------------------------- citations and numbering
CITE = []
LABFILE = os.path.join(OUT, "labels.json")
TLAB = json.load(open(LABFILE)) if os.path.exists(LABFILE) else {}
TLAB_NEW = {}
FIGN, TABN = [0], [0]


def compress(nums):
    nums = sorted(set(nums))
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append("%d–%d" % (nums[i], nums[j]) if j - i >= 2 else ", ".join(str(n) for n in nums[i:j + 1]))
        i = j + 1
    return ", ".join(out)


def cites(text):
    def rep(m):
        nums = []
        for k in m.group(1).split(","):
            k = k.strip()
            assert k in REFS, "unknown reference key " + k
            if k not in CITE:
                CITE.append(k)
            nums.append(CITE.index(k) + 1)
        return "[" + compress(nums) + "]"
    return re.sub(r"\[\[([^\]]+)\]\]", rep, text)


def sub(text):
    text = re.sub(r"@(\w+)@", lambda m: str(V[m.group(1)]), text)
    text = re.sub(r"@T:(\w+)@", lambda m: "Table %s" % TLAB.get(m.group(1), "?"), text)
    return text


doc = H.new_document(size=11, line=1.5)
H.page_numbers_and_line_numbers(doc)


def P(text, **kw):
    kw.setdefault("align", "justify")
    return H.para(doc, cites(sub(text)), **kw)


def HD(text, level=1):
    return H.heading(doc, text, level)


def FIG(path, caption):
    FIGN[0] += 1
    H.figure(doc, os.path.join(ROOT, "figures", path), width_in=6.5, cap="**Fig. %d** %s" % (FIGN[0], cites(sub(caption))))


def TAB(rows, caption, widths=None, size=8, label=None):
    TABN[0] += 1
    if label:
        TLAB_NEW[label] = TABN[0]
    H.caption(doc, "**Table %d** %s" % (TABN[0], cites(sub(caption))), keep_next=True)
    H.table(doc, [[cites(sub(c)) for c in r] for r in rows], widths=widths, size=size)


TITLE = "An Evidence-Graded Framework for Pharmaceutical Route Selection and Process-Risk Prioritisation: A PN6047 Case Study"
p = doc.add_paragraph()
H.add_rich(p, TITLE, size=16, bold=True)
for line in ("Leon Sandler", "Independent researcher, Northbrook, Illinois, USA", "Corresponding author: sandler.leon@gmail.com",
             "ORCID: 0009-0007-4584-808X"):
    q = doc.add_paragraph()
    H.add_rich(q, line, size=10.5)
    q.paragraph_format.space_after = H.Pt(0)
doc.add_paragraph()

# ================================================================== abstract, summary, teaser, keywords
HD("Abstract")
ABS = [
    ("Purpose", "To develop and demonstrate an evidence-graded framework for screening discovery-scale synthetic routes before experimental process development, using the "
                "publicly disclosed route to PN6047, a clinical-stage δ-opioid receptor agonist, as a case study."),
    ("Methods", "No synthesis was performed. Operations exemplified in two patent documents were inventoried; each transformation and its conditions were graded A–D by the "
                "strength of public evidence; documented regulatory and hazard attributes were flagged; two process-oriented variants were screened by step count, flags and an "
                "evidence-weighted validation burden; and a twelve-item risk register was ranked, with the sensitivity of the prioritisation to the author-assigned ratings tested by perturbation."),
    ("Results", "The exemplified route (milligram to gram scale; final N-functionalisation isolated in 16 % by preparative HPLC) carries @f0@ documented flags, including an ICH Q3C "
                "Class 1 solvent, palladium and a benzotriazole-derived coupling reagent. Variants R1 and R2 carry @f1@ flags each but a higher validation burden (@b1@ and @b2@ "
                "against @b0@, linear scale): fewer documented flags did not mean lower development uncertainty. Impurity purge when crystallisation replaces chromatography, and "
                "the undisclosed route to the vinyl bromide, stayed in the top three in about @p1@ % of perturbations, conditional on the initial risk model."),
    ("Conclusion", "The framework converts public route information into an auditable experimental-prioritisation strategy while explicitly separating documented process "
                   "liabilities from unvalidated alternatives. It does not select a best route; it shows where the evidence is strong or assumed and which experiments carry the "
                   "highest information value."),
]
abs_words = 0
for lab, txt in ABS:
    t = sub(txt)
    abs_words += len((lab + " " + t).split())
    pp = H.para(doc, "**%s:** %s" % (lab, cites(t)), align="justify")
print("abstract words:", abs_words)
assert 150 <= abs_words <= 250, abs_words
P("**Keywords:** pharmaceutical process development; synthetic route design; evidence grading; process risk assessment; drug substance manufacturing; PN6047", align="left")
P("**Summary (about 100 words).** Discovery-scale synthetic routes are often public only as small-scale examples, yet decisions about process development must be "
  "made from them. We present an evidence-graded framework that inventories the operations of a route, grades the public evidence for each, flags documented regulatory and "
  "hazard attributes, screens alternative routes, ranks process risks and tests the sensitivity of that ranking. Applied to the δ-opioid agonist PN6047, it showed that variants "
  "with fewer documented flags carry a higher burden of proof, and that impurity purge and an undisclosed building-block route dominate. No experiments were run; the output is "
  "a stage-gated plan for what to test first.", align="justify")
P("**Teaser (25–30 words).** An evidence-graded framework turns a public discovery-scale route into an auditable plan: what the record supports, which documented risks matter, "
  "and which experiments to run first.", align="justify")

# ================================================================== 1 Introduction
HD("1 Introduction")
HD("1.1 PN6047 and its development context", 2)
P("PN6047, 4-[(3-carbamoylphenyl)[1-(1,3-thiazol-5-ylmethyl)piperidin-4-ylidene]methyl]-*N*,*N*-dimethylbenzamide (C_{26}H_{28}N_{4}O_{2}S, relative molecular mass @mw@), "
  "is a selective δ-opioid receptor agonist that is G protein-biased in cell-based assays and effective in rodent models of chronic pain [[conibear2020]]. It belongs to "
  "the diarylmethylidene-piperidine class that Wei and colleagues described as formally derived from SNC-80 by replacing the piperazine ring with a piperidine ring "
  "carrying an exocyclic double bond [[wei2000]]. The compound was disclosed in a patent application of PharmNovo AB [[wo2016]], and crystalline forms of its hydrochloride "
  "salt were claimed in a later application [[wo2022]]. A European Innovation Council project coordinated by the same company describes completed phase I trials and a planned "
  "phase IIa proof-of-concept study [[cordis]]. The author has no affiliation with the company.")
HD("1.2 The manufacturing problem", 2)
P("A synthesis that supplies a discovery programme is rarely a manufacturing route. Federsel describes the handover from medicinal chemistry to process research as the point "
  "where technical, safety and scalability questions that were invisible at the bench become decisive [[federsel2009]], and surveys of the chemistry used in process research "
  "show a different reaction distribution from that of discovery chemistry [[carey2006]]. In discovery chemistry the most frequently used reactions are amide-bond formation, "
  "Suzuki–Miyaura coupling and nucleophilic aromatic substitution, chosen for reagent availability, chemoselectivity and speed of delivery [[brown2016]]; drug molecules "
  "additionally contain amines and nitrogen heterocycles that make synthesis harder [[blakemore2018,vitaku2014]]. The route that is public for PN6047 is of exactly this "
  "kind: the patent examples use a benzotriazole-derived coupling reagent, a palladium-catalysed coupling, trifluoroacetic acid, a chlorinated solvent that is a Class 1 "
  "solvent under ICH Q3C, and preparative HPLC [[wo2016,ich_q3c]]. What the public record does not contain is any yield, impurity profile or palladium level at a scale "
  "relevant to manufacture.")
HD("1.3 Research question and contribution", 2)
P("The general question is how the public information on a discovery-scale route can be converted into an auditable plan for process development: which of its operations "
  "carry documented liabilities, how strong is the evidence for the alternatives that would replace them, and which experiment would be most informative to run first. PN6047 "
  "is the case study; the contribution is the framework. It consists of (i) an evidence-grading scheme that separates what is shown for the compound from what is inferred "
  "from the scaffold class, from general pharmaceutical practice, or only hypothesised; (ii) a screening of the exemplified route and two process-oriented variants by step count, "
  "documented flags and an evidence-weighted validation burden, reported as two separate axes; (iii) a risk register whose prioritisation is tested for sensitivity to the "
  "ratings and to the choice of weighting; and (iv) a stage-gated validation plan that is the principal actionable output (@T:valid@). The case study also corrects a mapping that "
  "an earlier form of the idea relied on: pramipexole, a commercial thiazole-containing amine, is a useful benchmark for manufacture and salt formation of a basic API "
  "[[zivec2010]], but its tetrahydrobenzothiazole-diamine core is not a substructure of PN6047 and is not used here as a fragment source.")
P("The paper does not claim that any proposed route works. No synthesis was performed, no yield, impurity level, cost or timeline is predicted, and no freedom-to-operate "
  "analysis was made. Each claim below is labelled by the strength of its public support.")

# ================================================================== 2 Methods
HD("2 Methods")
HD("2.1 Design and scope", 2)
P("The study is a literature- and document-based screening exercise with a small computational layer. It uses no laboratory data of the author. The computation counts and "
  "classifies documented operations; it does not simulate chemistry. All inputs are in plain JSON files (route inventories, flags, precedents, risk ratings) and all outputs are "
  "regenerated by a single script, so that every number in the text can be traced to an input.")
HD("2.2 Sources and how they were used", 2)
P("The primary sources are the two patent documents above [[wo2016,wo2022]], whose text as published on Google Patents was searched and read for the passages on synthesis, purification and salt forms, and the ICH guidelines on impurities, "
  "residual solvents, elemental impurities and development of drug substances [[ich_q3a,ich_q3c,ich_q3d,ich_q11]], whose texts were consulted for the limits quoted. "
  "Journal articles were located through Crossref and Europe PMC and chosen for the precedent they provide for a named operation. For the journal precedents, including "
  "those that support classes B and C, the bibliographic record and abstract were examined and the full texts were not accessible to the author; statements about them are "
  "therefore limited to what the record supports (for example, that a transformation class is reported for a scaffold or in general practice), not to the specific conditions "
  "proposed here. The precedent map (@T:prec@) is accordingly a screening map, and confirming each journal precedent against its full text is the first item of the "
  "experimental programme (@T:valid@, stage 0). The search was purposive, not systematic, and the paper should not be read as a systematic review. All DOIs were resolved through Crossref and the reference list was built from the returned records. "
  "The machine-readable text of WO 2016/099393 contains transcription irregularities; in particular, the starting material named for its Example III is not the compound "
  "that Example IV requires. The reagent classes of that example are used here, but not its compound names.")
HD("2.3 Retrosynthetic decomposition and the five-stage framework", 2)
P("PN6047 was decomposed into five stages (Fig. 1): the thiazol-5-ylmethyl unit (S1), the diarylmethylidene-piperidine core (S2), N-functionalisation joining them (S3), the "
  "dimethylamide (S4) and the hydrochloride salt (S5). Three bond disconnections define the framework: (a) the N–CH_{2} bond, by reductive amination with "
  "thiazole-5-carbaldehyde; (b) the vinylic carbon–aryl bond to the carbamoylphenyl ring, by Suzuki–Miyaura coupling of a vinyl bromide with an arylboronic acid; and (c) the "
  "amide C–N bond. The exocyclic double bond joins a carbon bearing two different aryl groups to C-4 of a piperidine ring with identical arms, so no geometric (E/Z) "
  "isomerism arises.")
FIG("Fig1_architecture.png", "Retrosynthetic framework for PN6047. Highlighted bonds are the three disconnections: a, N–CH_{2} (reductive amination with "
                           "thiazole-5-carbaldehyde); b, vinylic carbon–aryl (Suzuki–Miyaura coupling of an N-Boc vinyl bromide with an arylboronic acid, after Boc "
                           "protection of the amine core); c, amide C–N. Structures were drawn from SMILES with RDKit. The scheme is a proposal and is experimentally unvalidated; "
                           "evidence colours refer to the transformations as exemplified in WO 2016/099393 and by Wei et al. [[wei2000]].")
HD("2.4 Evidence classes", 2)
P("Each operation received two grades (@T:evid@): one for the transformation itself and one for its conditions as written in the route. A route step that reuses a published "
  "transformation under changed conditions can therefore carry class A for the former and class D for the latter. Class A means that the transformation is reported for "
  "PN6047 or its immediate precursor in the public record examined; B, a close precedent in the same scaffold class; C, a general pharmaceutical precedent; D, a hypothesis. "
  "Classes map to the labels established (A), inferred (B, C) and proposed (D); none of them is a validation at manufacturing scale, which is absent for every step.")
rows = [["Class", "Label", "Definition used", "Example in this paper"],
        ["A", "Established (public record)", "Reported for PN6047 or its immediate precursor in the public record examined", "Reductive amination with thiazole-5-carbaldehyde (WO 2016/099393, Example Ib)"],
        ["B", "Inferred", "Reported for the same scaffold class (diarylmethylidene-piperidine δ agonists)", "Suzuki coupling of a vinyl bromide in the series [[wei2000,qian2010]]"],
        ["C", "Inferred (class level)", "Established pharmaceutical practice for the transformation class, not on this scaffold", "Boc removal with HCl in a Class 3 solvent [[isidro2009]]"],
        ["D", "Proposed", "Adaptation with no direct or close precedent in the sources examined", "Crystallisation as the impurity-purging step in place of preparative HPLC"]]
TAB(rows, "Evidence classes used to grade the transformation and the conditions of each step. None of the classes implies validation at manufacturing scale.",
    widths=[0.45, 1.35, 2.5, 2.2], label="evid")
HD("2.5 Route inventories", 2)
P("Route R0 is the sequence exemplified in the patent documents (amide formation, Suzuki–Miyaura coupling, Boc removal, reductive amination, salt formation). Route R1 keeps the "
  "same disconnections but pre-installs the amide in a purchased aryl building block, specifies palladium control, removes the Boc group with HCl in a Class 3 solvent, replaces "
  "1,2-dichloroethane in the reductive amination by a solvent that Abdel-Magid and colleagues list as an alternative [[abdelmagid1996]], and uses crystallisation of the hydrochloride "
  "[[wo2022]] as the purification step. Route R2 changes the order: the thiazol-5-ylmethyl group is installed on a piperidone before the alkene is built, which removes the "
  "protecting group and the late N-functionalisation but rests entirely on hypotheses. The preparation of the vinyl bromide is not described in the portion of WO 2016/099393 "
  "examined, so a number *u* of undisclosed upstream steps is added to all routes: *u* = @u@ by default and 1–4 in a sensitivity sweep. R0 and R1 grade this upstream "
  "block as class B (two general approaches are described for the scaffold [[wei2000]]); R2 grades it D.")
HD("2.6 Screening metrics", 2)
P("For each route the model reports the number of steps *N* and the longest linear sequence; the number of construction steps (forming a C–C or C–N bond) against concession "
  "steps (deprotection, salt formation), whose ratio follows Baran's notion of ideality [[gaich2010]]; the number of steps that are in-house convergent in the sense of Hendrickson "
  "[[hendrickson1977]]; the documented flags of @T:flags@ (each a screening marker with a cited source, not a hazard or regulatory determination); and a validation burden, the "
  "sum over steps of a weight for the evidence class of the conditions. Three weightings are used because no weighting is canonical: linear (A, B, C, D = 0, 1, 2, 3), convex "
  "(0, 1, 3, 9) and binary (1 for class D only).")
rows = [["Flag", "What it marks", "Source"],
        ["Cl1", "Step uses an ICH Q3C Class 1 solvent (1,2-dichloroethane; limit 5 ppm)", "[[ich_q3c]]"],
        ["Cl2", "Step uses an ICH Q3C Class 2 solvent (e.g. DMF, DME, dichloromethane, THF, acetonitrile)", "[[ich_q3c]]"],
        ["Pd", "Palladium catalyst; ICH Q3D Class 2B, oral permitted daily exposure 100 μg/day", "[[ich_q3d]]"],
        ["HOAt", "Coupling reagent containing a hydroxybenzotriazole-type unit; the class is associated with explosive properties", "[[wehrstedt2005]]"],
        ["HPLC", "Preparative HPLC used for purification in the disclosed example", "[[wo2016]]"],
        ["2 d / 16 %", "Reaction time of two days and reported isolated yield of 16 % in the disclosed example", "[[wo2016]]"],
        ["lyo", "Lyophilisation and drying at 80 °C for three days to isolate the amorphous salt (screening scale)", "[[wo2022]]"]]
TAB(rows, "Documented flags used in the screening. Flags are markers taken from cited documents; they are not hazard assessments or regulatory conclusions.",
    widths=[0.8, 4.5, 1.2], label="flags")
HD("2.7 Requirements of the framework", 2)
P("A framework for screening routes before process development has to satisfy four requirements, which also serve as criteria for judging it in the Discussion. "
  "*Traceability*: every statement about a route leads to a source document or is labelled as an assumption; here each step of each inventory carries its source keys and two "
  "evidence grades, and each flag cites the guideline or example it was checked against. *Discrimination*: it must separate options that differ in a way that matters for a "
  "decision; here routes are described on two axes that are kept apart, documented flags and validation burden, and risks are ranked rather than averaged. *Robustness*: its "
  "conclusions must survive reasonable changes of choices that cannot be justified uniquely; here three weightings of the evidence classes, one to four undisclosed upstream "
  "steps and three distributions of rating uncertainty are used. *Actionability*: its output must be a decision, namely which experiment to run first and what it would decide, "
  "not a score; here the output is the stage-gated programme of @T:valid@.")
P("Three propositions were stated so that the output could contradict them, and the build of this paper stops if they do not hold. P1: the exemplified route has the most "
  "documented flags and the lowest validation burden, so that the two axes order the routes in opposite directions. P2: this order is the same under every weighting and for "
  "every number of undisclosed steps tested. P3: the two leading risks remain the most frequent members of the top three when the rating uncertainty is widened. P1 and P2 "
  "are properties of the inventories, P3 of the register; none is a statement about chemistry that has been run.")
HD("2.8 Risk register and sensitivity of risk prioritisation to rating uncertainty", 2)
P("Twelve development risks of the proposed routes were listed, each with a likelihood (L) and an impact (I) on a 1–5 scale. The ratings are author-assigned ratings based on "
  "the evidence inventory; they are not measurements and there is no calibration. To test how much the prioritisation depends on them, each rating was perturbed by −1, 0 or +1 "
  "(probabilities 0.25, 0.50, 0.25, clipped to 1–5) in @mc@ random draws with a fixed seed, ties being broken at random, and the share of draws in which each risk ranks in the "
  "top three or five was recorded. This evaluates the stability of the ranking conditional on the initial risk model; the shares are not empirical probabilities that any risk "
  "will occur. Two other distributions were used to see whether the conclusion depends on that choice: a narrow one (probabilities 0.1, 0.8, 0.1) and a wide one (−2 to +2, equal "
  "probabilities). The smallest change of ratings that would reverse the leading order was also found by enumeration: the least value of |ΔL| + |ΔI| that brings each of the two "
  "leading risks down to the score of the next cluster, and each member of that cluster up to the score of the leaders. The approach follows the general principle of quality "
  "risk management [[ich_q9]] but is not a formal FMEA.")
P("Because flags and validation burden are different quantities, no single score is reported. To show what a combined score would imply, the exchange rate λ* at which two routes "
  "score equally on flags + λ × burden was computed for each weighting and each number of undisclosed steps. A sponsor that values one unit of burden at more than λ* flags "
  "prefers the route with the lower burden; one that values it at less prefers the route with fewer flags. The value of λ* is a statement about preferences, not a result about the chemistry.")
HD("2.9 Software, checks and reproducibility", 2)
P("Calculations use Python with NumPy and, for structures, RDKit. The structure of PN6047 and of two patent analogues was drawn from SMILES strings and its formula and "
  "[M+H]^{+} value recomputed to confirm the mass-spectrometric values printed in the patent. A test suite checks the integrity of the inputs (unique step identifiers, evidence "
  "classes, flags defined, every source key resolving to a reference), the order of the exemplified operations, the formula, the agreement with the printed masses and the "
  "determinism of the output. Code, inputs, outputs and the manuscript builder are public (Declarations).")
HD("2.10 Use of artificial intelligence tools", 2)
P("A large language model (Claude, Anthropic) was used to assist literature retrieval, data-file preparation, code, figures and drafting. The author reviewed and edited the "
  "content, checked every quoted value in the patent texts and guidelines against the source, resolved every reference through Crossref, and takes full responsibility for the "
  "paper. No such tool is an author, and none was used to generate or alter data.")

# ================================================================== 3 Results
HD("3 Results")
HD("3.1 Consistency of the structural data with the patent", 2)
P("The structure of PN6047 corresponds to C_{26}H_{28}N_{4}O_{2}S with a relative molecular mass of @mw@. Recomputed [M+H]^{+} values were @mh1@ for PN6047, @mh2@ for the "
  "6-(trifluoromethyl)pyridin-3-ylmethyl analogue and @mh3@ for the 4-methylimidazol-5-ylmethyl analogue, which agree to the nearest integer with the values 461, 523 and 458 "
  "printed in WO 2016/099393 for Examples Ib, Ia and Ic. The framework therefore describes the compounds that the patent actually makes.")
HD("3.2 What the public record shows", 2)
P("@T:prec@ maps each operation to the public evidence. All five operations of the exemplified route reach class A for the transformation, but only at discovery scale: the "
  "reductive amination started from 40 mg of amine and delivered 8.2 mg (16 %) after preparative HPLC; the Suzuki–Miyaura step used 0.533 g of the vinyl bromide and the crude "
  "product was taken on without purification, so no yield or purity is reported; the Boc removal used 0.630 g; the amide formation used 1.00 g of acid. The amorphous hydrochloride "
  "was made from 500.5 mg of free base by lyophilisation, and crystalline hydrochloride forms are described but no scale is reported [[wo2022]]. The preparation of the vinyl bromide "
  "is not described in the portion examined. No published synthesis of PN6047 at a scale relevant to manufacture was found in the sources examined.")
AUTH = [("Wei et al. 2000", "Wei et al. [[wei2000]]"), ("Qian et al. 2010", "Qian et al. [[qian2010]]"), ("Dunetz et al. 2016", "Dunetz et al. [[dunetz2016]]"),
        ("Wehrstedt et al. 2005", "Wehrstedt et al. [[wehrstedt2005]]"), ("Isidro-Llobet et al. 2009", "Isidro-Llobet et al. [[isidro2009]]"),
        ("Abdel-Magid et al. 1996", "Abdel-Magid et al. [[abdelmagid1996]]"), ("Bastin et al. 2000", "Bastin et al. [[bastin2000]]"),
        ("Federsel 2009", "Federsel [[federsel2009]]"), ("Carey et al. 2006", "Carey et al. [[carey2006]]"),
        ("Brown and Bostrom 2016", "Brown and Boström [[brown2016]]"), ("ICH Q3D sets", "ICH Q3D [[ich_q3d]] sets")]


def auth(t):
    for a_, b_ in AUTH:
        t = t.replace(a_, b_)
    return t


rows = [["Operation (stage)", "Evidence", "What the public record shows", "Remaining uncertainty"]]
for p_ in PREC:
    rows.append(["%s (S%d)" % (p_["operation"], p_["stage"]) if p_["stage"] else p_["operation"], p_["evidence"], auth(p_["shows"]), auth(p_["uncertainty"])])
TAB(rows, "Precedent map: each operation with the strength of the public evidence, what the sources show and what remains uncertain for PN6047. Stage 0 denotes the "
          "general premise (discovery-to-process handover). Journal precedents were assessed from the record and abstract, not the full text.", widths=[1.35, 0.55, 2.55, 2.1], size=7, label="prec")
HD("3.3 Documented attributes of the exemplified route", 2)
r0 = ROUTES["routes"]["R0"]["steps"]
rows = [["Step", "Conditions as written", "Scale in the example", "Flags"]]
FA = {"Q3C1_solvent": "Cl1", "Q3C2_solvent": "Cl2", "Pd_catalyst": "Pd", "BTZ_reagent": "HOAt", "Prep_HPLC": "HPLC", "Long_reaction": "2 d",
      "Low_reported_yield": "16 %", "Lyophilisation_long_drying": "lyo"}
for s in r0:
    rows.append([s["name"], s["conditions"], s["scale"], ", ".join(FA[f] for f in s["flags"])])
TAB(rows, "Inventory of route R0, the operations exemplified in WO 2016/099393 and WO 2022/013153, with documented flags (see the flag table).",
    widths=[1.5, 2.9, 1.2, 1.0], size=7.5, label="r0")
P("Route R0 carries @f0@ flag instances in @df0@ distinct flags, distributed over @sf0@ of its five steps (@T:r0@). The reductive amination alone carries five, including the "
  "Class 1 solvent, preparative HPLC, the two-day reaction and the 16 % yield. The Suzuki step carries the palladium flag and the amide formation the benzotriazole-reagent "
  "flag. The flags mark where process development would warrant particular evaluation or modification; they do not show that the exemplified route is unsafe or non-compliant at the scale at which it was run.")
HD("3.4 Screening of the variants", 2)
rows = [["Metric", "R0", "R1", "R2"],
        ["Steps *N* (*u* = @u@; range for *u* = 1–4)", "@n0@ (@nr0@)", "@n1@ (@nr1@)", "@n2@ (@nr2@)"],
        ["Longest linear sequence", "@n0@", "@n1@", "@n2@"],
        ["In-house convergent steps", "0", "0", "0"],
        ["Construction / concession steps (disclosed or proposed)", "%d / %d" % (D["R0"]["construction_steps"], D["R0"]["concession_steps"]),
         "%d / %d" % (D["R1"]["construction_steps"], D["R1"]["concession_steps"]), "%d / %d" % (D["R2"]["construction_steps"], D["R2"]["concession_steps"])],
        ["Ideality (construction share)", "@i0@", "@i1@", "@i2@"],
        ["Flag instances (distinct)", "@f0@ (@df0@)", "@f1@ (%d)" % D["R1"]["distinct_flags"], "@f2@ (%d)" % D["R2"]["distinct_flags"]],
        ["Evidence class of conditions (A/B/C/D)", "%d/%d/%d/%d" % tuple(D["R0"]["cond_evidence"][k] for k in "ABCD"),
         "%d/%d/%d/%d" % tuple(D["R1"]["cond_evidence"][k] for k in "ABCD"), "%d/%d/%d/%d" % tuple(D["R2"]["cond_evidence"][k] for k in "ABCD")],
        ["Validation burden, linear weights", "@b0@", "@b1@", "@b2@"],
        ["Validation burden, convex weights", "@c0@", "@c1@", "@c2@"],
        ["Validation burden, binary (class D only)", "@d0@", "@d1@", "@d2@"]]
TAB(rows, "Screening metrics for the three routes at the default number of undisclosed upstream steps. The ordering of the routes by burden and by flags is the same for every "
          "weighting and for *u* = 1–4.", widths=[3.0, 1.1, 1.1, 1.1], size=8, label="metrics")
P("Two relations hold in every case tested (@T:metrics@, Fig. 2). First, the exemplified route carries the most flags (@f0@ against @f1@ for R1 and @f2@ for R2, for every "
  "*u* from 1 to 4): the Class 1 solvent, the benzotriazole-derived reagent, preparative HPLC and lyophilisation do not appear in R1 or R2. Second, the validation burden runs "
  "in the opposite direction, R0 < R1 < R2 under all three weightings and for every *u*: @b0@, @b1@ and @b2@ on the linear scale (@c0@, @c1@, @c2@ convex; @d0@, @d1@, @d2@ "
  "binary). R0's low burden reflects that every one of its conditions has been run, once, at a small scale; R1 and R2 have lower flag counts only because their conditions are "
  "not yet tested. The step count itself differs by one step between routes (@n0@, @n1@, @n2@), and ideality is mixed (@i0@, @i1@, @i2@). The gain is not shorter chemistry but "
  "the removal of documented flags, at the price of evidence that must still be generated.")
P("None of the routes is convergent in the sense that matters for manufacturing cycle time. The thiazole carbaldehyde and the arylboronic acid enter as purchased building "
  "blocks, so, in the accounting of the manufacturer, the counted steps form one linear sequence. A convergent architecture, in which two fragments are made in parallel and "
  "joined, exists only if both fragments are prepared in-house, which moves the registered starting-material boundary upstream (Discussion).")
FIG("Fig2_routes.png", "Routes R0, R1 and R2 as step sequences. Box colour is the evidence class of the conditions as written; dashed boxes are the undisclosed upstream steps "
                       "(*u* = 2). Red labels are documented flags (Cl1, Cl2: ICH Q3C Class 1 and 2 solvents; Pd: palladium catalyst; HOAt: hydroxybenzotriazole-type reagent; HPLC: "
                       "preparative HPLC; 2 d and 16 %: reaction time and yield of the disclosed reductive amination; lyo: lyophilisation). *N* is the number of steps, "
                       "flags the number of flag instances and burden the validation burden on the linear scale.")
HD("3.5 Risk register and sensitivity of its prioritisation", 2)
rows = [["ID", "Risk", "L", "I", "L×I", "Top 3 (% of draws)", "Top 5 (% of draws)"]]
for k in RES["risk_order_by_score"]:
    r = RK[k]
    rows.append([k, r["name"], str(r["L"]), str(r["I"]), str(r["score"]), "%d" % round(100 * r["p_top3"]), "%d" % round(100 * r["p_top5"])])
TAB(rows, "Risk register for the proposed routes with the author's likelihood (L) and impact (I) ratings (1–5) and the probability that each risk ranks in the top three or five "
          "when every rating is perturbed by −1, 0 or +1 (@mc@ random draws; conditional on the initial risk model, not an empirical probability). The ratings are author-assigned "
          "on the basis of the evidence inventory, not data.", widths=[0.4, 3.9, 0.3, 0.3, 0.45, 0.65, 0.65], size=7.5, label="risk")
P("Of the twelve risks, @nhigh@ have a baseline score of at least 12 (@T:risk@). Two stand apart (Fig. 3): the impurity profile and purge when crystallisation replaces preparative "
  "HPLC (K1) and the undisclosed upstream route to the vinyl bromide (K2). Each keeps a top-three position in about @p1@ % of the perturbed rankings, whereas no other risk "
  "exceeds @pmax@ %. These shares describe the stability of the ranking given the initial ratings; they are not probabilities of the risks themselves. The other four high-scoring risks (palladium control, performance of the coupling, the reductive amination, and regulatory change of route) are "
  "interchangeable within the uncertainty of the ratings, so their order should not be interpreted. The ranking of the two leading risks is a property of the structure of "
  "the evidence (the only disclosed purification is chromatography; the upstream route is undisclosed) and not of a fine choice of scores.")
HD("3.6 What would change the conclusions", 2)
P("Three checks ask what it would take to reverse the findings. First, the exchange rate between the two axes. Between R0 and R1, λ* is @be01@ on the linear scale at *u* = @u@ "
  "(@be01min@ to @be01max@ across the three weightings and all *u*): a sponsor that values one unit of linear burden at more than @be01@ documented flag instances would prefer R0 "
  "as the route to test with least new evidence, and one that values it at less would prefer R1. Between R0 and R2, λ* is @be02lo@–@be02hi@ over *u* = 1–4. Between R1 and R2, "
  "λ* is zero for every weighting: R2 never has fewer flags or a lower burden than R1, and its only advantage is one step fewer. R2 is therefore dominated on the two axes by R1, "
  "and its shorter sequence is bought with hypotheses. Second, the reversal of the leading risks needs a combined change of @rvgap@ rating points: moving K1 or K2 (score @rvlead@) "
  "down to the next cluster (score @rvclus@) needs a change of @rvgap@ in |ΔL| + |ΔI|, and so does moving one of the four risks in that cluster up to the leaders. The "
  "prioritisation is therefore stable to a one-point disagreement about a single rating but not to a disagreement of two points about the same risk, which is the kind of "
  "challenge the validation programme is designed to settle. Third, widening the rating uncertainty does not erase the order but weakens it: under the narrow distribution "
  "the two leading risks stay in the top three in at least @pnar@ % of draws (no other risk above @pnarmax@ %), under the wide distribution (−2 to +2) in about @pwide@ % "
  "(no other risk above @pwidemax@ %). That they remain the most frequent members of the top three under every distribution tried supports examining them first, but it "
  "remains a conclusion conditional on the initial ratings.")
FIG("Fig3_risks.png", "Risk register. (a) Position of the twelve risks on the likelihood–impact grid (the author's ratings). (b) Share of perturbed draws in which each risk ranks in the top three "
                      "or top five when every rating is perturbed by −1, 0 or +1 (conditional on the initial risk model; not an empirical probability).")

# ================================================================== 4 Discussion
HD("4 Discussion")
HD("4.1 Pramipexole as benchmark, not as source of fragments", 2)
P("The idea that prompted this study took pramipexole as a template whose thiazole-amine core would be built on and extended. The structures do not support that mapping. "
  "Pramipexole is a 2-amino-4,5,6,7-tetrahydrobenzothiazole bearing a propylamino group [[schneider1987]], whereas the thiazole of PN6047 is an unsubstituted thiazol-5-yl "
  "attached through a methylene group to the piperidine nitrogen; the benzothiazole core of pramipexole is not a fragment of PN6047. What pramipexole offers is "
  "different: a published scalable synthesis of a thiazole-containing, basic CNS drug [[zivec2010]], and a precedent for salt formation of a basic amine. The thiazol-5-ylmethyl "
  "unit itself occurs in other drugs, for example as a carbamate in ritonavir [[kempf1998]], and thiazole chemistry in approved drugs has been reviewed [[niu2023]]; these "
  "are the more relevant precedents for the supply of that unit, but the sources examined do not document its supply, quality or registered-starting-material status "
  "(risk K10). Cost figures for pramipexole were not used.")
HD("4.2 Convergence is a property of the starting-material boundary", 2)
P("An argument for modular synthesis is that fragments made in parallel shorten the cycle time to the longer of the two branches. That argument applies to steps the manufacturer "
  "performs. Where the thiazole carbaldehyde or the arylboronic acid is a purchased material, the branch does not exist in the manufacturer's step count, and the "
  "route is linear (@T:metrics@). ICH Q11 states that each branch of a convergent process begins with one or more starting materials, that GMP applies from their first use, "
  "that a starting material \"should be a substance of defined chemical properties and structure\" incorporated \"as a significant structural fragment\", "
  "and that enough of the process must be described for authorities \"to understand how impurities are formed in the process\" and how they are purged [[ich_q11]]. "
  "Whether the thiazole carbaldehyde and the arylboronic acid qualify as registered starting materials is therefore a regulatory judgement that depends on the control "
  "strategy. A genuinely convergent design would have to be defined together with a starting-material proposal; it cannot be asserted from the chemistry alone, and the "
  "framework treats the boundary as an explicit assumption.")
HD("4.3 Flags removed, evidence owed", 2)
P("The trade-off in @T:metrics@ is the central finding of the case study: fewer documented flags did not mean lower development uncertainty. The exemplified route carries @f0@ "
  "flags and a validation burden of @b0@; R1 carries @f1@ flags and a burden of @b1@, and R2 @f2@ flags and a burden of @b2@ (linear scale). A reader who counted flags alone would "
  "rank the routes in the reverse of the order in which they could be trusted. The Class 1 solvent of the exemplified reductive amination has documented alternatives for the reaction class, "
  "because the original description of the reagent lists tetrahydrofuran and acetonitrile besides 1,2-dichloroethane [[abdelmagid1996]], but both are Class 2 solvents "
  "[[ich_q3c]] and the change has not been shown for this substrate. Replacing the benzotriazole-derived coupling reagent by a purchased building block that already "
  "carries the amide removes the reagent and its hazard class [[wehrstedt2005,dunetz2016]], but moves the question to the availability and quality of that building block. "
  "Palladium cannot be removed from a route that uses a cross-coupling for the C–C bond; it can only be controlled, and removal methods are well documented as a class "
  "[[garrett2004,galaffu2007]] without evidence for this substrate. Finally, crystallisation of the hydrochloride is described in the patent as a way to obtain a "
  "stable crystalline form [[wo2022]]; its use to purge the impurities of the whole sequence, which is what would replace preparative HPLC, is the least supported element "
  "of R1 and carries the highest-ranked risk. Thus the variants reduce what can be named, and increase what must be shown.")
HD("4.4 Economic considerations without a cost model", 2)
P("No manufacturing cost is estimated. A defensible estimate would need yields and mass balances of each step, from which process mass intensity [[jimenez2011]] and the E factor "
  "[[sheldon2017]] could be computed, a solvent assessment [[alfonsi2008,prat2016]], quotations for the building blocks and a model of scale. None of these exists for PN6047 "
  "in the sources examined. The screening supports a qualitative statement only: the documented cost drivers of the exemplified route are its reported 16 % isolated yield in the "
  "last step, chromatography, the Class 1 solvent and its control, a palladium catalyst and its removal, and an undisclosed upstream sequence; each is addressed "
  "in R1 by a proposal, not by a result. Supply concentration of the building blocks (risks K10 and K12) is an assumption of the register, because no supplier or price data were "
  "collected.")
HD("4.5 Experimental validation requirements", 2)
rows = [["Stage", "Experiment to be done (not done here)", "Decision it informs", "Risks addressed"],
        ["0 Upstream", "Confirm the journal precedents of the precedent map against their full texts; define and test a route to the N-Boc vinyl bromide (benzhydryl alcohol dehydration or alternative); propose registered starting materials under ICH Q11", "Whether the grades B and C stand; whether the building blocks exist at acceptable quality; the starting-material boundary", "K2, K6, K10"],
        ["1 Coupling", "Screen catalyst, base, solvent and temperature of the Suzuki–Miyaura step at laboratory scale; quantify palladium by ICP-MS after work-up, scavenging and crystallisation", "Whether the coupling gives a purity and palladium level compatible with the ICH Q3D limit", "K3, K4"],
        ["2 Deprotection", "Remove the Boc group with HCl in a Class 3 solvent and isolate the amine hydrochloride by crystallisation", "Whether an isolated intermediate improves purge of coupling by-products", "K1, K7"],
        ["3 N-functionalisation", "Screen solvent (THF, acetonitrile, ester solvents) and reductant for the reductive amination; in-process control of conversion; quench and gas-evolution assessment; compare with alkylation under ICH M7 assessment [[ich_m7]]", "Whether the Class 1 solvent can be removed without loss of conversion; which reagent leaves the fewer controlled impurities", "K5, K7, K8"],
        ["4 Salt", "Crystallise the hydrochloride (Form HCl2 solvents from the patent); XRPD, residual solvent, hygroscopicity", "Whether crystallisation alone purges impurities and delivers the intended polymorph", "K1, K9"],
        ["5 Impurities", "Impurity mapping by LC-MS across all stages; spiking and purge studies; working thresholds from ICH Q3A (for doses up to 2 g/day: identification 0.10 %, qualification 0.15 %, or lower daily-intake limits)", "Whether the impurity profile of the new route is acceptable or needs further qualification", "K1, K6"],
        ["6 Safety and scale", "Reaction calorimetry and thermal-stability screening of each step before any scale-up", "Safe operating limits; go/no-go for scale", "K7"]]
TAB(rows, "Principal actionable output: stage-gated experimental programme required before any proposed route could be considered validated. Stage 0 also includes confirming the journal precedents of @T:prec@ against their full texts. The acceptance criteria other than the cited ICH values are "
          "for the development team to set.", widths=[1.05, 2.6, 2.0, 0.85], size=7.2, label="valid")
P("@T:valid@ is the principal actionable output of the framework. The programme is ordered so that the two dominant risks are met first (@T:valid@): the upstream route and the starting-material question, and the purge of impurities in the "
  "isolation steps. Calorimetry precedes every scale-up step, and all numerical go/no-go criteria are left to the sponsor, because inventing them without data would "
  "give a false precision. The route should be regarded as validated only when the laboratory work above has been completed on PN6047 intermediates.")
HD("4.6 A reusable workflow, and what the method does not do", 2)
P("No new chemical transformation is proposed. The contribution is a workflow that can be applied to any compound whose discovery route is public and that needs no "
  "laboratory data to start: (1) reconstruct the public discovery route and its scale; (2) inventory its operations and conditions; (3) classify the evidence for each "
  "transformation and each set of conditions; (4) attach documented process flags with their sources; (5) generate alternative routes that change as little as possible; "
  "(6) calculate the validation burden of each alternative under more than one weighting; (7) rank the risks and test the ranking against the ratings; (8) test the sensitivity "
  "of the conclusions to the choices that cannot be justified uniquely; and (9) convert the result into a stage-gated experimental plan. Steps 1–4 can be done from public "
  "documents, steps 5–8 are computed by the code that accompanies the paper, and step 9 is the part that must be done by a development team.")
P("The method does not select the best route. A route is not better because it has fewer flags, nor worse because it carries a higher burden; the two axes answer different "
  "questions, the first what has already been identified as a liability in the public record, the second how much of a proposed alternative has still to be shown. What the method "
  "gives is a map of where the evidence is strong (the exemplified route has been run once at each step, at a small scale), where it is assumed (all conditions of the "
  "proposed variants), and which experiments have the highest information value (those that address the leading risks and move class D conditions to class A). The word "
  "selection in the title refers to deciding which route to test first, not to declaring a route chosen.")
P("Return to the four requirements of Section 2.7. Traceability is met by the source keys and the two grades; its weak point is that, for the journal precedents, the grades rest "
  "on abstracts. Discrimination is met by the separation of flags and burden, which gave opposite orderings, and by the dominance of R1 over R2, which a single score would "
  "have hidden. Robustness is met for the weighting, *u* and the rating distributions, but not for the structure of the register itself, which one author defined. Actionability "
  "is met by @T:valid@, whose acceptance criteria remain to be set by a development team. The framework is therefore a way to organise and challenge a decision, not to make it.")
HD("4.7 Limitations", 2)
P("No synthesis was performed and no yield, impurity profile, scale-up experiment or manufacturing cost was measured or predicted. The regulatory acceptability of the proposed "
  "routes has not been assessed, and no freedom-to-operate analysis was made for a compound that is the subject of patent filings. The exemplified route is the discovery route in "
  "the patent texts; the clinical-supply route of the developer is not public and may differ. The patent text examined contains an inconsistency (Example III) that "
  "could not be resolved from the available text. The evidence grading and the risk ratings are author-assigned on the basis of the evidence inventory; the sensitivity "
  "analysis evaluates the stability of the ranking conditional on the initial risk model and is not an empirical probability, and the exchange rates λ* express preferences, "
  "not measurements. The literature search was purposive; for the journal precedents only the record and abstract were examined, so the grades B and C are provisional until "
  "the full texts have been checked. The number of "
  "undisclosed upstream steps is a parameter, not a finding. The screening metrics count documented attributes and do not measure safety, cost or sustainability. The chemical "
  "compatibility of the proposed conditions with the PN6047 intermediates, including the coupling in route R2 of a basic, heteroatom-rich substrate, remains untested.")

# ================================================================== 5 Conclusions
HD("5 Conclusions")
P("The paper presents a framework that converts public information on a discovery-scale route into evidence grades, documented process flags, a sensitivity-tested ranking of "
  "development risks and a stage-gated experimental plan, and demonstrates it on PN6047. The only public route to PN6047 drug substance is exemplified at milligram-to-gram "
  "scale, and its documented attributes (a Class 1 solvent, a palladium-catalysed coupling, a benzotriazole-derived reagent, preparative HPLC, a 16 % isolated yield in the final "
  "N-functionalisation) show where process development would warrant particular evaluation or modification. The central result is that fewer documented flags did not mean lower "
  "development uncertainty: the variants that remove most flags carry a higher validation burden, because every one of their conditions is unvalidated. Impurity purge by "
  "crystallisation and the route to the vinyl bromide building block are the dominant uncertainties and should be tested first. The framework converts public route information "
  "into an auditable experimental-prioritisation strategy while explicitly separating documented process liabilities from unvalidated alternatives; it does not identify a best "
  "route, and it is not a validated process.")

# ================================================================== declarations and references
HD("Statements and Declarations")
P("**Funding.** The author received no funding for this work.")
P("**Competing interests.** The author declares no competing interests. The author has no affiliation with PharmNovo AB or with the project partners named in the "
  "cited project description. An earlier, shorter, unpublished outline of the route concept was submitted by the author to an open-innovation challenge "
  "(Wazoku challenge idea 141585, 2026); no part of it has been published elsewhere.")
P("**Author contributions.** Leon Sandler: conceptualisation, methodology, software, formal analysis, investigation, data curation, writing – original draft, writing – review and "
  "editing, visualisation.")
P("**Data and code availability.** The inventories, flags, precedents, risk ratings, model code, tests, figure scripts and the manuscript builder are available at %s "
  "and archived on Zenodo at https://doi.org/@sw@; this manuscript is archived as a preprint at https://doi.org/@pp@. The two patent documents and the ICH guidelines "
  "are public." % REPO)
P("**Ethics.** This study uses only published documents; no human participants, animals or personal data were involved.")
P("**Use of artificial intelligence.** See Section 2.10.")
HD("References")
for k in CITE:
    q = doc.add_paragraph()
    H.add_rich(q, "[%d] %s" % (CITE.index(k) + 1, REFS[k]["entry"]), size=10)
    q.paragraph_format.space_after = H.Pt(3)

# ---------------------------------------------------------------- figure numbering tokens and output
doc.core_properties.author = "Leon Sandler"
doc.core_properties.title = TITLE
outp = os.path.join(OUT, "PN6047_Route_Design_v%s.docx" % VERSION)
doc.save(outp)
json.dump(TLAB_NEW, open(LABFILE, "w"))
text_words = 0
body = False
for q in doc.paragraphs:
    t = q.text.strip()
    if t == "1 Introduction":
        body = True
    if t == "Statements and Declarations":
        body = False
    if body and t:
        text_words += len(t.split())
print("saved", outp, "| figures:", FIGN[0], "| tables:", TABN[0], "| references:", len(CITE), "| body words (excl. tables):", text_words, "| labels:", TLAB_NEW)
