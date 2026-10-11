#!/usr/bin/env python3
"""Publish an explicitly unverified, high-recall electrical-treatment screening register.

This register is for paper discovery and missingness audits. It must not be
used as a denominator for a world ranking or as independently confirmed evidence.
"""
import argparse
import csv
import json
import pathlib
import re
from build_provisional_rankings import MODALITIES, classify

PATHWAYS=("TTFields","Electrochemotherapy","Electroporation",
          "Neuromodulation","Electrical Stimulation","Electrochemical")
TOPIC_CONTEXT=re.compile(
    r"\b(?:therap\w*|treat\w*|cancer|tumou?r|glioblastoma|disease|"
    r"neuron\w*|nerve|brain|epilepsy|Parkinson\w*|depression|"
    r"wound\w*|heal\w*|regenerat\w*|cell\w*|tissue|"
    r"pain|ablat\w*|rehabilitat\w*|electroporat\w*|delivery)\b",re.I)
REVIEW_HINT=re.compile(
    r"\b(?:systematic.review|literature.review|scoping.review|"
    r"meta.analysis|perspective|overview|review.article)\b",re.I)
EXCLUDE_TITLE=re.compile(
    r"\b(?:fuel.cell|hydrogen.evolution|water.splitting|"
    r"lithium.ion.battery|battery.anode)\b",re.I)
TITLE_FALLBACK={
    "TTFields":r"\b(?:tumou?r[ -]?treating[ -]?fields?|ttfields?|novottf|optune)\b",
    "Electrochemotherapy":r"\b(?:electrochemotherap\w*|electropermeabili[sz]ation)\b",
    "Electroporation":r"\b(?:electroporat\w*|high[ -]frequency[ -]irreversible|"
                     r"pulsed[ -]field[ -]ablation|nanosecond[ -]pulsed[ -]electric)\b",
    "Neuromodulation":r"\b(?:neuromodulat\w*|neurostimulat\w*|"
                       r"deep[ -]brain[ -]stimulation|vagus[ -]nerve|"
                       r"spinal[ -]cord[ -]stimulation|t[ -]?dcs|t[ -]?acs)\b",
    "Electrical Stimulation":r"\b(?:electrical[ -]stimulation|electric[ -]field[ -]stimulation|"
                             r"bioelectric[ -]stimulation|electric[ -]field[ -]guided)\b",
    "Electrochemical":r"\b(?:bipolar[ -]electrochem\w*|wirefree[ -]electrochem\w*|"
                      r"electrochemical[ -](?:release|drug[ -]delivery|therapy)|"
                      r"electroactive[ -]conducting[ -]polymer)\b",
}
def norm_doi(value):
    s=str(value or "").strip().lower()
    for prefix in ("https://doi.org/","http://doi.org/","https://dx.doi.org/"):
        if s.startswith(prefix):s=s[len(prefix):]
    return s
def stable_key(item):
    doi=norm_doi(item.get("doi"))
    return ("doi:"+doi) if doi else str(item.get("openalex_id") or
        "title:"+re.sub(r"[^a-z0-9]+","",str(item.get("title") or "").lower())+
        ":"+str(item.get("year") or ""))
def publication_pathways(item):
    title=item.get("title") or ""
    abstract=item.get("abstract") or ""
    queries=" ".join(item.get("source_queries") or [])
    if EXCLUDE_TITLE.search(title):return []
    output=[]
    for p in PATHWAYS:
        strong=re.search(TITLE_FALLBACK[p],title,re.I) or re.search(MODALITIES[p],title,re.I)
        # Query or abstract matches are only screening leads, never scored
        # inclusions. Requiring a relevant title reduces incidental citations.
        lead=TOPIC_CONTEXT.search(title) and (
            re.search(TITLE_FALLBACK[p],abstract,re.I) or
            re.search(TITLE_FALLBACK[p],queries,re.I))
        if strong or lead:
            output.append(p)
    return output
def collect(records):
    eligible,_=classify(records)
    scored={stable_key(r) for r in eligible}
    result=[]
    seen=set()
    for r in records:
        pathways=publication_pathways(r)
        if not pathways:continue
        key=stable_key(r)
        if key in seen:continue
        seen.add(key)
        doi=norm_doi(r.get("doi"))
        linked=r.get("openalex_id") or ""
        url="https://doi.org/"+doi if doi else linked if linked.startswith("https://openalex.org/") else ""
        title=r.get("title") or ""
        publication_type=str(r.get("openalex_work_type") or "")
        review=(publication_type.casefold()=="review" or bool(REVIEW_HINT.search(title)) or
                any("review" in str(x).casefold() for x in r.get("publication_types") or []))
        status=("review_or_background_candidate" if review else
                "machine_score_eligible_not_independently_screened" if key in scored else
                "awaiting_originality_mechanism_and_identity_review")
        result.append({
            "title":title,"year":r.get("year"),"doi":doi,"url":url,
            "openalex_work_id":linked,"pathways":pathways,"screening_status":status,
            "document_type_from_source":publication_type or "unspecified",
            "author_names":[a.get("name") or "" for a in r.get("authors") or []],
            "work_level_author_identifiers":sum(bool(a.get("openalex_author_id") or a.get("orcid"))
                                                for a in r.get("authors") or []),
            "openalex_citations":r.get("citations_openalex"),
            "source_databases":r.get("source_databases") or [],
            "source_queries":r.get("source_queries") or [],
            "abstract_available":bool(r.get("abstract")),
            "scientific_validation":"NOT_INDEPENDENTLY_SCREENED",
        })
    result.sort(key=lambda r:(-(int(r["year"]) if str(r["year"]).isdigit() else 0),
                              r["title"].casefold()))
    counts={p:sum(p in r["pathways"] for r in result) for p in PATHWAYS}
    return {"status":"UNVERIFIED_SCREENING_CANDIDATES_NOT_WORLD_CENSUS",
            "total_candidate_records":len(result),"counts_by_pathway":counts,
            "independent_full_text_screening_completed":0,
            "papers":result,
            "caveats":["Selection maximises literature discovery; many records are out-of-scope or irrelevant.",
                       "Machine eligible does not establish therapeutic efficacy or original-paper status.",
                       "Missing records and author IDs are not imputed, and no rankings are generated here.",
                       "All displayed authors and institutions require independent work-level verification."]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    source=json.loads(pathlib.Path(a.input).read_text(encoding="utf-8"))
    result=collect(source["records"])
    dest=pathlib.Path(a.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    fields=["year","title","doi","url","pathways","screening_status",
            "document_type_from_source","author_names","work_level_author_identifiers",
            "openalex_citations","source_databases","source_queries","scientific_validation"]
    with dest.with_suffix(".csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        for item in result["papers"]:
            w.writerow({k:"; ".join(map(str,item.get(k) or [])) if isinstance(item.get(k),list)
                        else item.get(k) for k in fields})
    print("Electrical treatment screening candidates:",result["total_candidate_records"])
    print("Pathway counts:",result["counts_by_pathway"])
if __name__=="__main__":
    main()
