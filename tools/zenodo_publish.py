# -*- coding: utf-8 -*-
"""Publish the two Zenodo records reserved by zenodo_reserve.py:

  software     the tagged GitHub release as a zip (MIT)
  preprint     the manuscript (docx and pdf) (CC BY 4.0)

The DOIs were reserved first so that they could be written into the manuscript. The token is read from ZENODO_TOKEN and never written to disk.

    python zenodo_publish.py software|preprint [--version=1.0.0] [--ms=1] [--dry]
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

TOKEN = os.environ.get("ZENODO_TOKEN")
if not TOKEN:
    raise SystemExit("ZENODO_TOKEN is not set in the environment")
API = "https://zenodo.org/api"
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
STATE = os.path.join("C:" + os.sep, "YouTube", "_pn6047_zenodo_state.json")
VERSION = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--version=")), "1.0.0")
MS = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--ms=")), "1")
TAG = "v" + VERSION
DRY = "--dry" in sys.argv
GITHUB = "https://github.com/sandlerleon/pn6047-route-design"
CREATORS = [{"name": "Sandler, Leon", "affiliation": "Independent Researcher", "orcid": "0009-0007-4584-808X"}]
TITLE_PAPER = "An Evidence-Graded Framework for Pharmaceutical Route Selection and Process-Risk Prioritization: A PN6047 Case Study"
TITLE_CODE = "PN6047 route-design screening: evidence-graded route inventories, flags, risk register, model code and manuscript"
KEYWORDS = ["PN6047", "pharmaceutical process development", "synthetic route design", "drug substance manufacturing", "evidence grading",
            "process risk assessment", "sensitivity analysis", "delta opioid receptor agonist", "ICH Q11", "Suzuki-Miyaura coupling", "reductive amination"]

ABOUT = """<p><strong>A literature- and document-based screening study. No synthesis was performed; no yield, impurity level, cost or timeline is
predicted.</strong> Prepared for submission to the <em>Journal of Pharmaceutical Innovation</em> (Springer). The operations of the only publicly
exemplified route to the drug substance of PN6047 (patent documents WO 2016/099393 and WO 2022/013153) are inventoried, each transformation and its
conditions are graded A-D by the strength of public evidence, documented regulatory and hazard attributes are flagged, two process-oriented variants
are screened, and a risk register is tested for the sensitivity of its prioritisation to the author-assigned ratings. The contribution is the reusable framework; PN6047 is the case study.</p>
<p><strong>Not claimed:</strong> that any proposed route works; any freedom-to-operate conclusion; any economic prediction. The author has no affiliation with
the patent applicant.</p>"""
DESC_CODE = ABOUT + """<p>Contents: route, flag, precedent and risk inventories (<code>data/</code>), the screening model and its tests (<code>code/</code>),
figure scripts, the reference-harvest script (Crossref), the manuscript builder and the manuscript. Manuscript preprint:
<a href="https://doi.org/{PP}">{PP}</a>.</p>"""
DESC_PAPER = ABOUT + """<p>Code, data and analysis: <a href="%s">%s</a>, archived at <a href="https://doi.org/{SW}">{SW}</a>.</p>""" % (GITHUB, GITHUB)


NOTES = {"1.1.0": "Reframed as an evidence-graded framework with PN6047 as the case study (new title and abstract); adds the four framework requirements and three stated propositions "
                  "(Section 2.7), a break-even analysis between documented flags and validation burden, a reversal analysis and a test of three rating distributions (Section 3.6), the "
                  "reusable nine-step workflow (Section 4.6), and a statement that the journal precedents were assessed from record and abstract. 'Monte Carlo' language replaced by "
                  "sensitivity of risk prioritisation to rating uncertainty. Numbers of the original analysis are unchanged."}
NEWVER = "<p><strong>Version %s.</strong> " + NOTES.get(VERSION, "Revised.") + "</p>"
NOTES_MS = {"3": "Language edit (Rubriq) merged selectively into the manuscript: American spelling, number formatting and comma edits only; no change to results, numbers or claims. A copy without line numbers is included for ChemRxiv."}


def clear_inherited(d):
    """A new-version draft starts with the files of the previous version; remove them so that only this version's files remain."""
    for fid in d.get("inherited_files", []):
        try:
            req("DELETE", "%s/deposit/depositions/%s/files/%s" % (API, d["id"], fid))
        except SystemExit:
            pass


def req(method, url, data=None, headers=None, raw=None):
    h = {"Authorization": "Bearer " + TOKEN}
    if headers:
        h.update(headers)
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    if data is not None and raw is None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=600) as resp:
            t = resp.read()
            return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        raise SystemExit("%s %s -> %s\n%s" % (method, url, e.code, e.read().decode()[:800]))


def upload(bucket, path, name):
    with open(path, "rb") as fh:
        req("PUT", "%s/%s" % (bucket, urllib.parse.quote(name)), raw=fh.read(), headers={"Content-Type": "application/octet-stream"})
    print("   uploaded %-62s %9.1f kB" % (name, os.path.getsize(path) / 1024.0))


def finish(did, meta):
    req("PUT", "%s/deposit/depositions/%s" % (API, did), data={"metadata": meta})
    print("   metadata written")
    if DRY:
        print("   DRY RUN - draft %s left unpublished" % did)
        return
    pub = req("POST", "%s/deposit/depositions/%s/actions/publish" % (API, did))
    rec = req("GET", "%s/records/%s" % (API, pub["id"]))
    print("   PUBLISHED  DOI %s  concept %s" % (rec.get("doi"), rec.get("conceptdoi")))


def software():
    st = json.load(open(STATE))
    d = st["software_" + VERSION] if "software_" + VERSION in st else st["software"]
    tmp = os.path.join(os.environ.get("TEMP", "."), "pn6047-route-design-%s.zip" % VERSION)
    subprocess.check_call(["git", "-C", REPO, "archive", "--format=zip", "--prefix=pn6047-route-design-%s/" % VERSION, "-o", tmp, TAG])
    print("=== software draft %s (reserved DOI %s)" % (d["id"], d["doi"]))
    clear_inherited(d)
    upload(d["bucket"], tmp, os.path.basename(tmp))
    meta = {"title": TITLE_CODE, "upload_type": "software", "description": (NEWVER % VERSION if VERSION != "1.0.0" else "") + DESC_CODE.replace("{PP}", st.get("publication_v" + MS, st["publication"])["doi"]),
            "creators": CREATORS, "keywords": KEYWORDS, "access_right": "open", "license": "mit-license", "version": VERSION, "language": "eng",
            "prereserve_doi": {"doi": d["doi"]},
            "related_identifiers": [{"identifier": GITHUB + "/tree/" + TAG, "relation": "isSupplementTo", "scheme": "url"},
                                    {"identifier": st.get("publication_v" + MS, st["publication"])["doi"], "relation": "isSupplementTo", "scheme": "doi"}]}
    finish(d["id"], meta)


def preprint():
    st = json.load(open(STATE))
    d = st["publication_v" + MS] if "publication_v" + MS in st else st["publication"]
    print("=== preprint draft %s (reserved DOI %s)" % (d["id"], d["doi"]))
    clear_inherited(d)
    for name in ("PN6047_Route_Design_v%s.docx" % MS, "PN6047_Route_Design_v%s.pdf" % MS, "PN6047_Route_Design_v%s_ChemRxiv.docx" % MS):
        upload(d["bucket"], os.path.join(REPO, "manuscript", name), name)
    meta = {"title": TITLE_PAPER, "upload_type": "publication", "publication_type": "preprint",
            "description": ("<p><strong>Version v%s.</strong> %s</p>" % (MS, NOTES_MS.get(MS, NOTES.get(VERSION, "Revised."))) if MS != "1" else "") + DESC_PAPER.replace("{SW}", st.get("software_" + VERSION, st["software"])["doi"]), "creators": CREATORS, "keywords": KEYWORDS, "access_right": "open",
            "license": "cc-by-4.0", "version": MS, "language": "eng", "prereserve_doi": {"doi": d["doi"]},
            "related_identifiers": [{"identifier": st.get("software_" + VERSION, st["software"])["doi"], "relation": "isSupplementedBy", "scheme": "doi"},
                                    {"identifier": GITHUB, "relation": "isSupplementedBy", "scheme": "url"}]}
    finish(d["id"], meta)


if __name__ == "__main__":
    what = [a for a in sys.argv[1:] if not a.startswith("--")]
    if what == ["software"]:
        software()
    elif what == ["preprint"]:
        preprint()
    else:
        raise SystemExit("usage: zenodo_publish.py software|preprint [--version=] [--ms=] [--dry]")
