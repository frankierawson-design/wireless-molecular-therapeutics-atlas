#!/usr/bin/env python3
"""Trace known DOI sentinel publications against the candidate corpus.

Coverage audit, NOT a declaration of a complete literature review.
"""
import argparse, csv, json, pathlib
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
]
def normalize(value):
    s=str(value or "").strip().lower()
    for prefix in ("https://doi.org/","http://doi.org/","https://dx.doi.org/"):
        if s.startswith(prefix):s=s[len(prefix):]
    return s
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
                       "has_openalex_author_ids":oa_id_present})
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
