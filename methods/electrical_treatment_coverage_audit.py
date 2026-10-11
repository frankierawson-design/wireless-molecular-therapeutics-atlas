#!/usr/bin/env python3
"""Prospective coverage sentinels for *all* core electrical-therapy classes.

The DOI references are source-verified examples, NOT a claim of bibliographic
completeness or of independently screened treatment efficacy.
"""
import argparse, collections, csv, json, pathlib
from build_provisional_rankings import classify, MODALITIES

SENTINELS=[
 {"doi":"10.1001/jama.2017.18718","pathway":"TTFields","label":"EF-14 glioblastoma survival, 2017"},
 {"doi":"10.1001/jama.2015.16669","pathway":"TTFields","label":"EF-14 initial randomised report, 2015"},
 {"doi":"10.1016/j.ejcsup.2006.08.002","pathway":"Electrochemotherapy","label":"ESOPE cutaneous metastases prospective clinical report"},
 {"doi":"10.1007/s00270-010-9964-1","pathway":"Electroporation","label":"Irreversible electroporation of renal cell carcinoma"},
 {"doi":"10.1056/nejmoa2307291","pathway":"Electroporation","label":"ADVENT pulsed field cardiac ablation trial"},
 {"doi":"10.1056/nejmoa060281","pathway":"Neuromodulation","label":"Randomised deep-brain stimulation for Parkinson disease"},
 {"doi":"10.1056/nejmoa1612999","pathway":"Neuromodulation","label":"Transcranial direct-current stimulation trial"},
 {"doi":"10.1177/19322968211035128","pathway":"Electrical Stimulation","label":"Electrical stimulation for diabetic wound healing"},
 {"doi":"10.1016/j.apmr.2009.12.026","pathway":"Electrical Stimulation","label":"Pressure ulcer electrical-stimulation trial"},
 {"doi":"10.1016/j.apmt.2020.100804","pathway":"Electrochemical","label":"Bipolar electroactive polymers for wireless cell stimulation"},
 {"doi":"10.1016/j.elecom.2023.107626","pathway":"Electrochemical","label":"BDNF release by wireless bipolar electrochemistry"},
]
PATHWAYS=["TTFields","Electrochemotherapy","Electroporation","Neuromodulation",
          "Electrical Stimulation","Electrochemical"]

def norm(doi):
    value=str(doi or "").casefold().strip()
    for prefix in ("https://doi.org/","http://doi.org/","https://dx.doi.org/"):
        if value.startswith(prefix):value=value[len(prefix):]
    return value

def audit(records, query_audit=None):
    lookup={norm(r.get("doi")):r for r in records if r.get("doi")}
    eligible,_=classify(records)
    scored={norm(r.get("doi")):r for r in eligible if r.get("doi")}
    report=[]
    for seed in SENTINELS:
        doi=seed["doi"]
        paper=lookup.get(doi)
        selected=scored.get(doi)
        classified_as=selected.get("modalities",[]) if selected else []
        included=seed["pathway"] in classified_as
        reason=""
        if paper and not included:
            _, exclusions=classify([paper])
            reason=", ".join(exclusions.keys()) if exclusions else "not_classified_in_target_pathway"
        if not paper:reason="not_retrieved"
        report.append({
            "pathway":seed["pathway"],"doi":doi,"label":seed["label"],
            "retrieved":bool(paper),"classified_in_target_pathway":included,
            "actual_machine_pathways":"; ".join(classified_as),
            "exclusion_or_mismatch":reason,
            "publisher_type":paper.get("openalex_work_type","") if paper else "",
            "source_work":paper.get("openalex_id","") if paper else "",
            "source_queries":"; ".join(paper.get("source_queries",[])) if paper else "",
        })
    group=[]
    events=query_audit or []
    for path in PATHWAYS:
        sentinels=[p for p in report if p["pathway"]==path]
        matched=[r for r in eligible if path in r["modalities"]]
        # Counts are sample/corpus-relative. Search terms may overlap pathways.
        prefix_queries={
            "TTFields":("tumor treating","tumour treating","ttfields","alternating electric","optune"),
            "Electrochemotherapy":("electrochemotherapy","electropermeabilization","esOPE"),
            "Electroporation":("irreversible electroporation","reversible electroporation",
                              "high frequency irreversible","pulsed field ablation",
                              "nanosecond pulsed","electroporation"),
            "Neuromodulation":("deep brain","vagus nerve","spinal cord","transcranial",
                               "peripheral nerve","transcutaneous"),
            "Electrical Stimulation":("electrical stimulation","electric field guided",
                                       "electric field stimulation","electrical muscle"),
            "Electrochemical":("bipolar","electrochemical","wirefree","wireless"),
        }[path]
        query_events=[e for e in events if any(
          str(e.get("query","")).casefold().startswith(p.casefold()) for p in prefix_queries)]
        group.append({
            "pathway":path,
            "known_doi_sentinels":len(sentinels),
            "sentinels_retrieved":sum(int(p["retrieved"]) for p in sentinels),
            "sentinels_machine_included":sum(int(p["classified_in_target_pathway"]) for p in sentinels),
            "machine_matched_papers":len(matched),
            "query_events":len(query_events),
            "query_errors":sum(bool(e.get("error")) for e in query_events),
            "independently_full_text_screened":0,
            "completeness_confirmed":False,
        })
    return {"scope":"Broader electrical therapy discovery, not a validated worldwide census",
            "validation_status":"MACHINE_SCREENED_NOT_INDEPENDENTLY_VALIDATED",
            "pathways":group,"sentinels":report,
            "search_errors":sum(bool(e.get("error")) for e in events),
            "critical_caveats":[
                "Retrieval may miss publications and the DOI sentinels do not measure recall.",
                "Clinical trials and cellular mechanisms are distinct evidence tiers.",
                "Institutional and author ID validation, full text adjudication and independent screening remain pending.",
                "No category-specific paper or author counts establish scientific ranking validity.",
                "Cross-modality overall rankings are not externally field normalized.",
            ]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--query-audit",default="")
    a=p.parse_args()
    dataset=json.loads(pathlib.Path(a.input).read_text(encoding="utf-8"))
    if a.query_audit:
        events=json.loads(pathlib.Path(a.query_audit).read_text(encoding="utf-8"))
    else:
        events=[]
    result=audit(dataset["records"],events)
    dest=pathlib.Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    with dest.with_suffix(".csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(result["sentinels"][0]))
        w.writeheader();w.writerows(result["sentinels"])
    for row in result["pathways"]:
        print(row["pathway"],row["machine_matched_papers"],"scored papers;",
              row["sentinels_retrieved"],"/",row["known_doi_sentinels"],"DOIs retrieved;",
              row["sentinels_machine_included"],"classified")
if __name__=="__main__":
    main()
