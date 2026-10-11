#!/usr/bin/env python3
"""Trace known DOI sentinel publications against the candidate corpus.

Coverage audit, NOT a declaration of a complete literature review.
"""
import argparse, csv, json, pathlib, re
from build_provisional_rankings import classify

SEEDS=[
  {"doi":"10.1038/s41565-023-01496-y","topic":"Wireless Au nanoantenna, apoptosis","expected":"therapeutic"},
  {"doi":"10.1002/advs.202516561","topic":"Wireless carbon nanotube porin, GBM","expected":"therapeutic"},
  {"doi":"10.1021/acsomega.1c03547","topic":"Bipolar nanoelectrode cell impedance","expected":"enabling-not-necessarily-eligible"},
  {"doi":"10.1038/s41598-024-71236-2","topic":"Wireless BPE growth of cellular microwires","expected":"enabling"},
  {"doi":"10.1021/acs.langmuir.6c00755","topic":"Wirefree PEDOT dye release","expected":"molecular-delivery-platform"},
  {"doi":"10.1038/s43246-025-00750-1","topic":"Wireless BPE drug loading into conducting hydrogel","expected":"molecular-delivery-platform"},
  {"doi":"10.1038/s41528-019-0060-6","topic":"Photovoltaic wireless electronic ion pump","expected":"molecular-delivery-platform"},
  {"doi":"10.1039/d5lc00708a","topic":"Remote-controlled electrochemical drug pump","expected":"molecular-delivery-platform"},
  {"doi":"10.1039/d3bm01946b","topic":"Wireless nerve growth BPE (review, exclude ranking)","expected":"review-not-ranked"},
  {"doi":"10.1016/j.apmt.2020.100804","topic":"Forster / DCU: Wireless bipolar conducting-polymer cell stimulation","expected":"original-therapeutic-candidate","expected_author":"Robert J. Forster","expected_orcid":"0000-0001-5079-3123"},
  {"doi":"10.1016/j.apmt.2022.101481","topic":"Forster / DCU: Wireless polymer templates for neuronal differentiation","expected":"original-therapeutic-candidate","expected_author":"Robert J. Forster","expected_orcid":"0000-0001-5079-3123"},
  {"doi":"10.1016/j.elecom.2023.107626","topic":"Forster / DCU: BDNF wirefree electrochemical release and neurite outgrowth","expected":"original-therapeutic-candidate","expected_author":"Robert J. Forster","expected_orcid":"0000-0001-5079-3123"},
  {"doi":"10.1021/acs.langmuir.6c00755","topic":"Forster / DCU: Wirefree drug release along PEDOT film","expected":"molecular-delivery-platform","expected_author":"Robert J. Forster","expected_orcid":"0000-0001-5079-3123"},
  {"doi":"10.1016/j.elecom.2024.107832","topic":"Forster / DCU: Wirefree electrochemistry for detection and treatment of disease","expected":"review-not-ranked","expected_author":"Robert J. Forster","expected_orcid":"0000-0001-5079-3123"},
  {"doi":"10.1039/d4cc03996c","topic":"Forster / DCU: Regio-selective wireless electropolymerisation","expected":"enabling-not-automatically-ranked","expected_author":"Robert J. Forster","expected_orcid":"0000-0001-5079-3123"},
  {"doi":"10.1021/acs.analchem.4c04454","topic":"Forster / DCU: Wirefree PEDOT field distribution","expected":"enabling-not-automatically-ranked","expected_author":"Robert J. Forster","expected_orcid":"0000-0001-5079-3123"},
  {"doi":"10.1002/celc.202400506","topic":"Forster / DCU: Bipolar polymer deposition and modelling","expected":"enabling-not-automatically-ranked","expected_author":"Robert J. Forster","expected_orcid":"0000-0001-5079-3123"},
]
def normalize(value):
    s=str(value or "").strip().lower()
    for prefix in ("https://doi.org/","http://doi.org/","https://dx.doi.org/"):
        if s.startswith(prefix):s=s[len(prefix):]
    return s

def author_identity_status(doc, seed):
    """Only an exact work-level ORCID is positive identity evidence."""
    if not seed.get("expected_author"):
        return "not_applicable"
    if doc is None:
        return "not_harvested"
    target=seed.get("expected_orcid","").upper()
    authors=doc.get("authors") or []
    if target and any(target in str(a.get("orcid") or "").upper() and
                      "forster" in str(a.get("name") or "").casefold()
                      for a in authors):
        return "orcid_verified_in_work_metadata"
    if any("forster" in str(a.get("name") or "").casefold() and
           re.search(r"\b(?:robert|r\.?\s*j\.?)\b",str(a.get("name") or ""),re.I)
           for a in authors):
        return "name_only_identity_not_verified"
    return "expected_author_absent_from_work_metadata"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--output",required=True)
    opts=ap.parse_args()
    corpus=json.loads(pathlib.Path(opts.input).read_text(encoding="utf8"))
    records=corpus["records"]
    lookup={normalize(r.get("doi")):r for r in records if r.get("doi")}
    report=[]
    for seed in SEEDS:
        doi=seed["doi"]
        doc=lookup.get(doi)
        if doc is not None:
            admitted,exclusions=classify([doc])
            status="machine_included" if admitted else "not_machine_included"
            explanation="machine matched" if admitted else ", ".join(exclusions)
            authors=doc.get("authors") or []
            oa_id_present=any(a.get("openalex_author_id") for a in authors)
        else:
            status="not_harvested"
            explanation="This DOI was not found by any bounded query; it may still be a valid study"
            oa_id_present=False
        report.append({"doi":doi,"topic":seed["topic"],"expected_role":seed["expected"],
                       "retrieved":bool(doc),"machine_status":status,
                       "reason":explanation,"title":doc.get("title","") if doc else "",
                       "openalex_work_id":doc.get("openalex_id","") if doc else "",
                       "has_openalex_author_ids":oa_id_present,
                       "expected_author":seed.get("expected_author",""),
                       "expected_orcid":seed.get("expected_orcid",""),
                       "author_identity_status":author_identity_status(doc,seed),
                       "publisher_orcid_conflict_corrected":bool(doc and doc.get("publisher_orcid_conflict_corrected")),
                       "publisher_correction_source":doc.get("publisher_orcid_correction_source","") if doc else "",
                       "original_source_orcid":next((a.get("openalex_original_orcid") for a in (doc.get("authors") or [])
                           if a.get("openalex_original_orcid")), "") if doc else ""})
    path=pathlib.Path(opts.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({"purpose":"Non-exhaustive DOI sentinel coverage audit",
         "records":report,"total_sentinels":len(SEEDS),
         "retrieved":sum(int(x["retrieved"]) for x in report),
         "included":sum(x["machine_status"]=="machine_included" for x in report)},
         indent=2,ensure_ascii=False),encoding="utf8")
    with path.with_suffix(".csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(report[0]));w.writeheader();w.writerows(report)
    print("DOI sentinel coverage",sum(int(x["retrieved"]) for x in report),"/",len(SEEDS))
    for r in report:print(r["doi"],r["machine_status"],r["reason"])
if __name__=="__main__":main()
