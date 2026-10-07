# -*- coding: utf-8 -*-
"""Figures 1-3 of the manuscript, from data/*.json and results/results.json (run route_model.py first).

    python make_figures.py        ->  ../figures/Fig1_architecture.png, Fig2_routes.png, Fig3_risks.png   (300 dpi)
"""
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"], "font.size": 8,
                     "axes.linewidth": 0.6})
EV = {"A": "#009E73", "B": "#56B4E9", "C": "#E69F00", "D": "#D55E00"}          # Okabe-Ito
EVTINT = {"A": "#CDEFE5", "B": "#DDF0FA", "C": "#FBEBC8", "D": "#F7D8C6"}
EVNAME = {"A": "A direct", "B": "B close precedent", "C": "C general precedent", "D": "D hypothesis"}


def load(p):
    return json.load(open(os.path.join(HERE, "..", p), encoding="utf-8"))


def mol_png(smiles, w=520, h=340, highlight=None, colors=None, atoms=()):
    """Draw a molecule filling its canvas; returns (image, {atom_index: (x_frac, y_frac)}) with y measured from the bottom."""
    from rdkit import Chem
    from rdkit.Chem.Draw import rdMolDraw2D
    from PIL import Image
    m = Chem.MolFromSmiles(smiles)
    d = rdMolDraw2D.MolDraw2DCairo(w, h)
    o = d.drawOptions()
    o.bondLineWidth = 2.2
    o.padding = 0.04
    o.clearBackground = True
    o.annotationFontScale = 0.8
    if highlight:
        d.DrawMolecule(m, highlightAtoms=[], highlightBonds=highlight, highlightBondColors={b: colors[i] for i, b in enumerate(highlight)})
    else:
        d.DrawMolecule(m)
    d.FinishDrawing()
    pts = {}
    for i in atoms:
        p = d.GetDrawCoords(i)
        pts[i] = (p.x / w, 1 - p.y / h)
    return np.array(Image.open(io.BytesIO(d.GetDrawingText()))), pts


def fig1():
    from rdkit import Chem
    pn = "NC(=O)c1cccc(c1)C(=C1CCN(Cc2cncs2)CC1)c1ccc(cc1)C(=O)N(C)C"
    m = Chem.MolFromSmiles(pn)

    def bond(smarts, i, j):
        mt = m.GetSubstructMatch(Chem.MolFromSmarts(smarts))
        return m.GetBondBetweenAtoms(mt[i], mt[j]).GetIdx(), (mt[i], mt[j])
    ba, ata = bond("[NX3;R][CH2]c1cncs1", 0, 1)
    bb, atb = bond("[CX3](=C)-c1cccc(c1)C(=O)[NX3H2]", 0, 2)
    bc, atc = bond("c[CX3](=O)[NX3]([CH3])[CH3]", 1, 3)
    green = (0.0, 0.62, 0.45)
    W, H = 1500, 1000
    img_pn, pts = mol_png(pn, W, H, [ba, bb, bc], [green] * 3, atoms=ata + atb + atc)
    img_ald, _ = mol_png("O=Cc1cncs1", 600, 420)
    img_am, _ = mol_png("NC(=O)c1cccc(c1)C(=C1CCNCC1)c1ccc(cc1)C(=O)N(C)C", 1200, 760)
    img_vb, _ = mol_png("CC(C)(C)OC(=O)N1CCC(=C(Br)c2ccc(cc2)C(=O)N(C)C)CC1", 1200, 760)
    img_bor, _ = mol_png("NC(=O)c1cccc(c1)B(O)O", 800, 560)
    fig = plt.figure(figsize=(7.2, 4.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 7.2)
    ax.set_ylim(0, 4.4)
    ax.axis("off")

    def put(img, x, y, w):
        h = w * img.shape[0] / img.shape[1]
        ax.imshow(img, extent=(x, x + w, y, y + h), aspect="auto", zorder=1)
        return x, y, w, h

    X, Y, Wd, Hd = put(img_pn, 0.05, 1.25, 2.9)
    ax.text(X + Wd / 2, Y + Hd + 0.05, "PN6047 (C$_{26}$H$_{28}$N$_4$O$_2$S)", ha="center", fontsize=8.5, weight="bold")

    def mid(at):
        (x1, y1), (x2, y2) = pts[at[0]], pts[at[1]]
        return X + Wd * (x1 + x2) / 2, Y + Hd * (y1 + y2) / 2

    for lab, at, off in (("a", ata, (0.0, -0.32)), ("b", atb, (-0.05, 0.3)), ("c", atc, (-0.33, -0.12))):
        x, y = mid(at)
        ax.text(x + off[0], y + off[1], lab, fontsize=9, weight="bold", color="#006B4F", ha="center", va="center",
                bbox=dict(boxstyle="circle,pad=0.15", fc="white", ec="#009E73", lw=1.0), zorder=5)
    ox, oy, ow, oh = put(img_ald, 3.75, 3.2, 1.0)
    ax.text(ox + ow / 2, oy + oh + 0.04, "thiazole-5-carbaldehyde", ha="center", fontsize=7.3)
    mx, my, mw, mh = put(img_am, 3.45, 1.55, 1.7)
    ax.text(mx + mw / 2, my + mh + 0.04, "secondary amine core (N-H)", ha="center", fontsize=7.3)
    vx, vy, vw, vh = put(img_vb, 5.6, 1.5, 1.6)
    ax.text(vx + vw / 2, vy + vh + 0.04, "N-Boc vinyl bromide", ha="center", fontsize=7.3)
    bx, by, bw, bh = put(img_bor, 5.95, 3.15, 1.1)
    ax.text(bx + bw / 2, by + bh + 0.04, "(3-carbamoylphenyl)boronic acid", ha="center", fontsize=7.0)
    ax.text(6.5, 2.98, "+", fontsize=12, ha="center", va="center")
    arr = dict(arrowstyle="-|>", lw=1.3, color="#444444")
    ax.annotate("", xy=(3.7, 3.55), xytext=(3.05, 2.75), arrowprops=arr)
    ax.annotate("", xy=(3.4, 2.05), xytext=(3.05, 2.55), arrowprops=arr)
    ax.annotate("", xy=(5.55, 2.05), xytext=(5.2, 2.05), arrowprops=arr)
    ax.text(2.88, 3.25, "a", fontsize=9, weight="bold", color="#006B4F", ha="center", va="center",
            bbox=dict(boxstyle="circle,pad=0.15", fc="white", ec="#009E73", lw=1.0), zorder=5)
    ax.text(2.95, 3.04, "C–N", fontsize=6.8, color="#006B4F", ha="right", va="center", weight="bold")
    ax.text(2.95, 2.92, "reductive", fontsize=6.8, color="#006B4F", ha="right", va="center", weight="bold")
    ax.text(2.95, 2.8, "amination", fontsize=6.8, color="#006B4F", ha="right", va="center", weight="bold")
    ax.text(5.6, 1.25, "b: Boc protection, then C–C Suzuki–Miyaura disconnection (to the two partners above)", fontsize=6.8,
            color="#006B4F", ha="right", va="center", weight="bold")
    ax.text(0.1, 1.05, "c  amide: HNMe$_2$ + ArCO$_2$H (HATU in R0), or pre-installed in a purchased aryl building block (R1, R2)",
            fontsize=7.2, ha="left", va="center", color="#006B4F", weight="bold")
    ax.text(0.1, 0.78, "Evidence class of the transformation for this substrate class", fontsize=7.5, weight="bold")
    x = 0.1
    for k in "ABCD":
        ax.add_patch(Rectangle((x, 0.42), 0.18, 0.18, fc=EV[k], ec="none"))
        ax.text(x + 0.25, 0.51, EVNAME[k], fontsize=7.3, va="center")
        x += 1.75
    ax.text(0.1, 0.15, "a: A (WO2016/099393 Ex. Ib); b: A/B (Ex. IV, Wei 2000); c: A (Ex. III). All at milligram to gram scale only.",
            fontsize=7.2, va="center")
    ax.text(7.1, 0.15, "Proposed — experimentally unvalidated", fontsize=7.8, ha="right", va="center", weight="bold", color="#D55E00",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#D55E00", lw=1.0))
    fig.savefig(os.path.join(FIG, "Fig1_architecture.png"), dpi=300)
    plt.close(fig)


FLAGABBR = {"Q3C1_solvent": "Cl1", "Q3C2_solvent": "Cl2", "Pd_catalyst": "Pd", "BTZ_reagent": "HOAt", "Prep_HPLC": "HPLC",
            "Long_reaction": "2 d", "Low_reported_yield": "16 %", "Lyophilisation_long_drying": "lyo"}


def fig2():
    routes = load("data/routes.json")
    res = load("results/results.json")
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 5.6))
    short = {
        "R0-amide": "dimethylamide\n(HATU)", "R0-suzuki": "Suzuki\ncoupling", "R0-boc": "Boc removal\n(TFA)",
        "R0-redam": "reductive\namination (DCE)", "R0-salt": "HCl salt\n(lyophilised)",
        "R1-suzuki": "Suzuki + Pd\ncontrol", "R1-boc": "Boc removal\n(HCl, Class 3)", "R1-redam": "reductive amination\n(other solvent)",
        "R1-salt": "HCl salt\ncrystallisation",
        "R2-Nfunc": "N-substituted\npiperidone", "R2-suzuki": "Suzuki\n(N-substituted)", "R2-salt": "HCl salt\ncrystallisation"}
    for ax, (rid, r) in zip(axes, routes["routes"].items()):
        ax.set_xlim(0, 10.4)
        ax.set_ylim(0, 2.0)
        ax.axis("off")
        ax.text(0.0, 1.85, rid, fontsize=10, weight="bold", va="center")
        d = res["routes"][rid]["default"]
        upst = "B" if rid != "R2" else "D"
        x = 0.7
        w, h = 1.38, 0.95
        # undisclosed upstream box
        ax.add_patch(FancyBboxPatch((x, 0.62), 1.15, h, boxstyle="round,pad=0.02", fc="white", ec=EV[upst], lw=1.2, ls="--"))
        ax.text(x + 0.575, 0.62 + h / 2, "undisclosed\nupstream\n(u = 2 steps)", ha="center", va="center", fontsize=6.8)
        x += 1.15
        prev_end = x
        for s in r["steps"]:
            x0 = x + 0.18
            ax.annotate("", xy=(x0, 0.62 + h / 2), xytext=(prev_end, 0.62 + h / 2), arrowprops=dict(arrowstyle="-|>", lw=0.9, color="#555"))
            ax.add_patch(FancyBboxPatch((x0, 0.62), w, h, boxstyle="round,pad=0.02", fc=EVTINT[s["cond_ev"]], ec=EV[s["cond_ev"]], lw=1.4))
            ax.text(x0 + w / 2, 0.62 + h / 2, short[s["id"]], ha="center", va="center", fontsize=7)
            fl = " ".join(FLAGABBR[f] for f in s["flags"])
            if fl:
                ax.text(x0 + w / 2, 0.38, fl, ha="center", va="center", fontsize=6.6, color="#8B1A1A", weight="bold")
            prev_end = x0 + w
            x = x0 + w
        ax.text(10.35, 1.05, "N = %d\nflags %d\nburden %d" % (d["steps_total"], d["flag_instances"], d["validation_burden"]["linear"]),
                ha="right", va="center", fontsize=7.2)
    # legend
    xl = 0.05
    for k in "ABCD":
        axes[2].add_patch(Rectangle((xl, 0.02), 0.2, 0.17, fc=EVTINT[k], ec=EV[k], lw=1.2, clip_on=False))
        axes[2].text(xl + 0.28, 0.105, "conditions: " + EVNAME[k], fontsize=6.8, va="center")
        xl += 2.55
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01, hspace=0.04)
    fig.savefig(os.path.join(FIG, "Fig2_routes.png"), dpi=300)
    plt.close(fig)


def fig3():
    res = load("results/results.json")
    risks = res["risks"]
    order = sorted(risks, key=lambda k: (-risks[k]["score"], k))
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.4), gridspec_kw={"width_ratios": [1, 1.15]})
    # (a) likelihood x impact grid
    cm = matplotlib.colormaps["YlOrRd"]
    for L in range(1, 6):
        for I in range(1, 6):
            a.add_patch(Rectangle((L - 0.5, I - 0.5), 1, 1, fc=cm((L * I) / 25 * 0.85 + 0.05), ec="white", lw=0.8))
    cells = {}
    for k in order:
        cells.setdefault((risks[k]["L"], risks[k]["I"]), []).append(k)
    for (L, I), ks in cells.items():
        for j, k in enumerate(ks):
            dx = (j % 2) * 0.42 - 0.21 if len(ks) > 1 else 0
            dy = (j // 2) * 0.3 - 0.1 * (len(ks) > 2)
            a.text(L + dx, I + 0.12 - dy * 1.0, k, ha="center", va="center", fontsize=7, weight="bold")
    a.set_xlim(0.5, 5.5)
    a.set_ylim(0.5, 5.5)
    a.set_xticks(range(1, 6))
    a.set_yticks(range(1, 6))
    a.set_xlabel("Likelihood (L, author's judgement)")
    a.set_ylabel("Impact (I, author's judgement)")
    a.set_aspect("equal")
    a.text(-0.02, 1.04, "a", transform=a.transAxes, fontsize=10, weight="bold")
    # (b) probability of staying in the top 3 / top 5 under +/-1 perturbation
    y = np.arange(len(order))[::-1]
    b.barh(y + 0.18, [risks[k]["p_top3"] for k in order], height=0.34, color="#D55E00", label="top 3")
    b.barh(y - 0.18, [risks[k]["p_top5"] for k in order], height=0.34, color="#56B4E9", label="top 5")
    b.set_yticks(y)
    b.set_yticklabels(["%s  (L×I = %d)" % (k, risks[k]["score"]) for k in order], fontsize=7)
    b.set_xlim(0, 1.0)
    b.set_xlabel("Share of draws ranking in the top 3 / top 5\nunder ±1 perturbation of every rating")
    b.legend(frameon=False, fontsize=7, loc="lower right")
    b.text(-0.02, 1.04, "b", transform=b.transAxes, fontsize=10, weight="bold")
    for ax in (a, b):
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "Fig3_risks.png"), dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    print("figures written to", FIG)
