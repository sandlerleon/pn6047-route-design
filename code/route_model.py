# -*- coding: utf-8 -*-
"""Evidence-graded route screening for PN6047: computes everything reported in the manuscript from data/*.json.

No chemistry is simulated and no yield, cost or impurity level is predicted. The model counts and classifies the operations of three
route inventories (R0 as exemplified in the public patent record, R1 and R2 proposed), applies documented flags, weights the evidence class of the
conditions under three weighting schemes, and tests how stable the ranking of an expert-judgement risk register is to +/-1 perturbations of its ratings.

    python route_model.py        ->  ../results/results.json
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
RES = os.path.join(HERE, "..", "results")
os.makedirs(RES, exist_ok=True)
SEED = 20261006
N_MC = 20000

WEIGHTS = {"linear": {"A": 0, "B": 1, "C": 2, "D": 3},
           "convex": {"A": 0, "B": 1, "C": 3, "D": 9},
           "binary_D": {"A": 0, "B": 0, "C": 0, "D": 1}}
UPSTREAM_EVIDENCE = {"R0": "B", "R1": "B", "R2": "D"}      # undisclosed preparation of the vinyl bromide: general approaches exist (Wei 2000); none known for the N-substituted halide
HAZARD_FLAGS = ["Q3C1_solvent", "Q3C2_solvent", "Pd_catalyst", "BTZ_reagent", "Prep_HPLC", "Long_reaction", "Low_reported_yield", "Lyophilisation_long_drying"]


def load(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))


def structure_checks():
    """Formula and mass of PN6047 and of the patent analogues recomputed from SMILES; compared with the MS values printed in WO2016/099393."""
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
    core = "NC(=O)c1cccc(c1)C(=C1CCN({sub})CC1)c1ccc(cc1)C(=O)N(C)C"
    cases = {"PN6047 (Example Ib)": ("Cc2cncs2", 461), "Example Ia (6-CF3-pyridin-3-ylmethyl)": ("Cc2ccc(nc2)C(F)(F)F", 523),
             "Example Ic (4-methylimidazol-5-ylmethyl)": ("Cc2[nH]cnc2C", 458)}
    out = {}
    for name, (sub, ms) in cases.items():
        m = Chem.MolFromSmiles(core.format(sub=sub))
        mh = Descriptors.ExactMolWt(m) + 1.007276
        out[name] = {"formula": rdMolDescriptors.CalcMolFormula(m), "mw": round(Descriptors.MolWt(m), 2),
                     "mh_calc": round(mh, 3), "ms_patent": ms, "agrees_to_integer": int(round(mh)) == ms}
    return out


def evidence_tally(steps, key):
    t = {"A": 0, "B": 0, "C": 0, "D": 0}
    for s in steps:
        t[s[key]] += 1
    return t


def route_metrics(rid, steps, u):
    n = u + len(steps)
    kinds = [s["kind"] for s in steps]
    flags = {f: sum(f in s["flags"] for s in steps) for f in HAZARD_FLAGS}
    burden = {}
    for sc, w in WEIGHTS.items():
        burden[sc] = sum(w[s["cond_ev"]] for s in steps) + u * w[UPSTREAM_EVIDENCE[rid]]
    return {"steps_total": n, "longest_linear_sequence": n, "in_house_convergent_steps": 0,
            "disclosed_or_proposed_steps": len(steps), "undisclosed_upstream_steps": u,
            "construction_steps": kinds.count("construction"), "concession_steps": kinds.count("concession"),
            "ideality": round(kinds.count("construction") / len(steps), 3),
            "flags": flags, "flag_instances": sum(flags.values()), "distinct_flags": sum(v > 0 for v in flags.values()),
            "steps_with_any_flag": sum(bool(s["flags"]) for s in steps),
            "ops_evidence": evidence_tally(steps, "ops_ev"), "cond_evidence": evidence_tally(steps, "cond_ev"),
            "validation_burden": burden}


def risk_stability(risks, rng):
    L = np.array([r["L"] for r in risks])
    I = np.array([r["I"] for r in risks])
    base = L * I
    d = rng.choice([-1, 0, 1], size=(N_MC, len(risks), 2), p=[0.25, 0.5, 0.25])
    Ls = np.clip(L + d[:, :, 0], 1, 5)
    Is = np.clip(I + d[:, :, 1], 1, 5)
    sc = Ls * Is + rng.random(Ls.shape) * 1e-6          # random tie-break
    rank = (-sc).argsort(axis=1).argsort(axis=1) + 1
    out = {}
    for j, r in enumerate(risks):
        out[r["id"]] = {"name": r["name"], "L": r["L"], "I": r["I"], "score": int(base[j]),
                        "p_top3": float((rank[:, j] <= 3).mean()), "p_top5": float((rank[:, j] <= 5).mean()),
                        "mean_rank": float(rank[:, j].mean())}
    order = sorted(out, key=lambda k: (-out[k]["score"], k))
    return out, order


def main():
    routes = load("routes.json")
    risks = load("risks.json")["risks"]
    u0 = routes["undisclosed_upstream"]["default_u"]
    res = {"seed": SEED, "n_monte_carlo": N_MC, "weights": WEIGHTS, "upstream_evidence": UPSTREAM_EVIDENCE, "default_u": u0}
    res["structure_checks"] = structure_checks()
    res["routes"] = {}
    for rid, r in routes["routes"].items():
        res["routes"][rid] = {"name": r["name"], "default": route_metrics(rid, r["steps"], u0),
                              "u_sweep": {str(u): route_metrics(rid, r["steps"], u) for u in routes["undisclosed_upstream"]["u_range"]}}
    # the ordering of the three routes under each weighting scheme, over the u sweep
    orders = {}
    for sc in WEIGHTS:
        orders[sc] = {str(u): sorted(res["routes"], key=lambda k: res["routes"][k]["u_sweep"][str(u)]["validation_burden"][sc])
                      for u in routes["undisclosed_upstream"]["u_range"]}
    res["burden_order_least_to_most"] = orders
    rng = np.random.default_rng(SEED)
    stab, order = risk_stability(risks, rng)
    res["risks"] = stab
    res["risk_order_by_score"] = order
    # the share of the 12 risks that rate 'high' (score >= 12) at the baseline ratings
    res["n_high_risks"] = sum(1 for k in stab if stab[k]["score"] >= 12)
    json.dump(res, open(os.path.join(RES, "results.json"), "w", encoding="utf-8"), indent=1)
    d = {k: v["default"] for k, v in res["routes"].items()}
    print("default u =", u0)
    for k, v in d.items():
        print(k, "N =", v["steps_total"], "flags =", v["flag_instances"], "burden =", v["validation_burden"], "flags by type =", {a: b for a, b in v["flags"].items() if b})
    print("structure checks:", {k: (v["formula"], v["mh_calc"], v["ms_patent"], v["agrees_to_integer"]) for k, v in res["structure_checks"].items()})
    print("risk order:", order[:5], {k: round(stab[k]["p_top3"], 2) for k in order[:6]})


if __name__ == "__main__":
    main()
