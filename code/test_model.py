# -*- coding: utf-8 -*-
"""Checks run before any result is used: data integrity, regulatory flags, structure/mass agreement with the patent, determinism."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import route_model as M  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


routes = M.load("routes.json")
flags = M.load("flags.json")
prec = M.load("precedents.json")
risks = M.load("risks.json")["risks"]
refkeys = set(json.load(open(os.path.join(HERE, "..", "refs", "ref_keys.json"), encoding="utf-8")))

steps = [s for r in routes["routes"].values() for s in r["steps"]]
check("step ids are unique", len({s["id"] for s in steps}) == len(steps))
check("evidence classes are A-D", all(s["ops_ev"] in "ABCD" and s["cond_ev"] in "ABCD" for s in steps))
check("every flag used is defined", all(f in flags for s in steps for f in s["flags"]))
check("every flag in the model's list is defined", all(f in flags for f in M.HAZARD_FLAGS))
check("every source key resolves to a reference", all(k in refkeys for s in steps for k in s["sources"]) and
      all(k in refkeys for p in prec for k in p["sources"]) and all(k in refkeys for f in [v for kk, v in flags.items() if not kk.startswith("_")] for k in [f["source"]]))
check("risk ratings are integers 1-5", all(isinstance(r["L"], int) and isinstance(r["I"], int) and 1 <= r["L"] <= 5 and 1 <= r["I"] <= 5 for r in risks))
check("R0 has the five exemplified operations in the patent order",
      [s["id"] for s in routes["routes"]["R0"]["steps"]] == ["R0-amide", "R0-suzuki", "R0-boc", "R0-redam", "R0-salt"])
check("R0 steps all carry evidence class A", all(s["ops_ev"] == "A" and s["cond_ev"] == "A" for s in routes["routes"]["R0"]["steps"]))
check("flag types in R1 and R2 are a subset of those in R0", {f for r in ("R1","R2") for s in routes["routes"][r]["steps"] for f in s["flags"]} <= {f for s in routes["routes"]["R0"]["steps"] for f in s["flags"]})
sc = M.structure_checks()
check("PN6047 formula C26H28N4O2S", sc["PN6047 (Example Ib)"]["formula"] == "C26H28N4O2S")
check("[M+H]+ of the three patent compounds agrees with the MS printed in WO2016/099393 (461, 523, 458)", all(v["agrees_to_integer"] for v in sc.values()))

# determinism: two runs give byte-identical results
out = os.path.join(HERE, "..", "results", "results.json")
subprocess.run([sys.executable, os.path.join(HERE, "route_model.py")], check=True, capture_output=True)
a = open(out, "rb").read()
subprocess.run([sys.executable, os.path.join(HERE, "route_model.py")], check=True, capture_output=True)
b = open(out, "rb").read()
check("route_model.py is deterministic (two runs byte-identical)", a == b)
res = json.loads(b)
d = res["routes"]
check("R1 carries no Class 1 solvent flag and R0 does", d["R1"]["default"]["flags"]["Q3C1_solvent"] == 0 and d["R0"]["default"]["flags"]["Q3C1_solvent"] == 1)
check("flag instances: R0 > R1 for every u in the sweep", all(d["R0"]["u_sweep"][u]["flag_instances"] > d["R1"]["u_sweep"][u]["flag_instances"] for u in d["R0"]["u_sweep"]))
be = res["break_even"]
check("break-even: R1 dominates R2 (equal flags, lower burden) under every weighting and u", all(be[w][u]["R1_vs_R2"] == 0 for w in be for u in be[w]))
check("break-even R0 vs R1 recomputed by hand (linear, u=2): (11-3)/(11-2) = 8/9", abs(be["linear"]["2"]["R0_vs_R1"] - 8 / 9) < 1e-12)
rv = res["reversal"]
check("reversal: leaders K1,K2 need 2 rating points to fall to the next cluster, and cluster members 2 to rise", rv["leaders"] == ["K1", "K2"] and set(rv["points_to_bring_leader_to_cluster"].values()) == {2} and set(rv["points_to_bring_cluster_member_to_leader"].values()) == {2})
pr = res["priors"]
check("prior sensitivity: leaders keep the highest top-3 share under all three rating distributions", all(min(p["K1"], p["K2"]) > max(v for k, v in p.items() if k not in ("K1", "K2")) for p in pr.values()))
check("prior sensitivity: widening the distribution lowers the leaders' share", pr["narrow"]["K1"] > pr["base"]["K1"] > pr["wide"]["K1"])
check("monte-carlo probabilities lie in [0,1]", all(0 <= v["p_top3"] <= 1 for v in res["risks"].values()))
print("\n%s" % ("ALL CHECKS PASSED" if not FAILS else "%d FAILED: %s" % (len(FAILS), ", ".join(FAILS))))
sys.exit(1 if FAILS else 0)
