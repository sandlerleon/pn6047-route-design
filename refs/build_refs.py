# -*- coding: utf-8 -*-
"""Harvest the bibliographic records of every cited journal article from Crossref (nothing is typed by hand for these) and write
refs/refs_cache.json and refs/ref_keys.json. Patents, regulatory guidelines and web pages are listed by hand in MANUAL.

    python build_refs.py
"""
import html
import json
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DOIS = {
    "conibear2020": "10.1124/jpet.119.258640", "wei2000": "10.1021/jm000229p", "qian2010": "10.1002/chem.201002147",
    "zivec2010": "10.1021/op1000989", "schneider1987": "10.1021/jm00386a009", "niu2023": "10.1016/j.ejmech.2023.115172",
    "abdelmagid1996": "10.1021/jo960057x", "roughley2011": "10.1021/jm200187y", "dugger2005": "10.1021/op050021j",
    "carey2006": "10.1039/b602413k", "brown2016": "10.1021/acs.jmedchem.5b01409", "magano2011": "10.1021/cr100346g",
    "dunetz2016": "10.1021/op500305s", "wehrstedt2005": "10.1016/j.jhazmat.2005.05.044", "jimenez2011": "10.1021/op200097d",
    "prat2016": "10.1039/c5gc01008j", "sheldon2017": "10.1039/c6gc02157c", "gaich2010": "10.1021/jo1006812",
    "hendrickson1977": "10.1021/ja00458a035", "garrett2004": "10.1002/adsc.200404071", "galaffu2007": "10.1021/op7000172",
    "federsel2009": "10.1021/ar800257v", "blakemore2018": "10.1038/s41557-018-0021-z", "bastin2000": "10.1021/op000018u",
    "yu2008": "10.1007/s11095-007-9511-1", "alfonsi2008": "10.1039/b711717e", "vitaku2014": "10.1021/jm501100b",
    "kempf1998": "10.1021/jm970636+", "isidro2009": "10.1021/cr800323s", "baumann2015": "10.3762/bjoc.11.134",
}
MANUAL = {
    "wo2016": "PharmNovo AB (inventors: von Mentzer B, Starke I, Brandt P). Diarylmethylidene piperidine derivatives and their use as delta opioid receptor agonists. "
              "Patent application WO 2016/099393 A1; published 23 June 2016. https://patents.google.com/patent/WO2016099393A1/en",
    "wo2022": "PharmNovo AB (inventors: von Mentzer B, Starke I, Nilsson HG). Polymorphs of a hydrochloride salt of PN6047. "
              "Patent application WO 2022/013153 A1; published 20 January 2022. https://patents.google.com/patent/WO2022013153A1/en",
    "cordis": "European Commission. PN6047-DOBRA: PN6047 - a breakthrough treatment of neuropathic pain. CORDIS project 101188409. "
              "https://cordis.europa.eu/project/id/101188409. Accessed 6 Oct 2026",
    "ich_q11": "ICH. Q11: Development and manufacture of drug substances (chemical entities and biotechnological/biological entities). 2012. "
               "https://database.ich.org/sites/default/files/Q11_Guideline.pdf",
    "ich_q3a": "ICH. Q3A(R2): Impurities in new drug substances. 2006. https://database.ich.org/sites/default/files/Q3A%28R2%29%20Guideline.pdf",
    "ich_q3c": "ICH. Q3C(R8): Impurities: guideline for residual solvents. 2021. "
               "https://database.ich.org/sites/default/files/ICH_Q3C-R8_Guideline_Step4_2021_0422_1.pdf",
    "ich_q3d": "ICH. Q3D(R2): Guideline for elemental impurities. 2022. https://database.ich.org/sites/default/files/Q3D-R2_Guideline_Step4_2022_0308.pdf",
    "ich_m7": "ICH. M7(R2): Assessment and control of DNA reactive (mutagenic) impurities in pharmaceuticals to limit potential carcinogenic risk. 2023. "
              "https://database.ich.org/sites/default/files/ICH_M7%28R2%29_Guideline_Step4_2023_0216_0.pdf",
    "ich_q9": "ICH. Q9(R1): Quality risk management. 2022. https://database.ich.org/sites/default/files/ICH_Q9%28R1%29_Guideline_Step4_2022_1219.pdf",
}


def fetch(doi):
    req = urllib.request.Request("https://api.crossref.org/works/" + doi, headers={"User-Agent": "refbuild (mailto:sandler.leon@gmail.com)"})
    return json.load(urllib.request.urlopen(req, timeout=60))["message"]


def initials(given):
    parts = re.split(r"[\s\-.]+", given.strip())
    return "".join(p[0] for p in parts if p)


def fmt(m, doi):
    au = m.get("author", [])
    names = ["%s %s" % (a.get("family", ""), initials(a.get("given", ""))) for a in au if a.get("family")]
    names = names if len(names) <= 6 else names[:6] + ["et al"]
    title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m["title"][0]))).strip().rstrip(".")
    j = (m.get("short-container-title") or m.get("container-title") or [""])[0]
    j = html.unescape(j).replace(".", "").replace("  ", " ").strip()
    year = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
    vol, page = m.get("volume"), m.get("page")
    tail = "%s %s" % (j, year)
    if vol:
        tail = "%s. %s;%s" % (j, year, vol) + (":%s" % page.replace("-", "–") if page else "")
    else:
        tail = "%s. %s" % (j, year)
    return "%s. %s. %s. https://doi.org/%s" % (", ".join(names), title, tail, doi)


def main():
    cache = {}
    for k, d in DOIS.items():
        m = fetch(d)
        cache[k] = {"doi": d, "entry": fmt(m, d), "title": m["title"][0], "year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0]}
        print(k, "->", cache[k]["entry"][:140])
    for k, v in MANUAL.items():
        cache[k] = {"doi": None, "entry": v}
    json.dump(cache, open(os.path.join(HERE, "refs_cache.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump(sorted(cache), open(os.path.join(HERE, "ref_keys.json"), "w", encoding="utf-8"), indent=1)
    print(len(cache), "entries")


if __name__ == "__main__":
    main()
