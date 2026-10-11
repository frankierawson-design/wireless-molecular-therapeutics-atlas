#!/usr/bin/env python3
"""Build a high-recall ELECTROCHEMICAL SCREENING QUEUE without inventing ranks.

Inclusion in this *queue* is not confirmation of primary therapeutic efficacy.
DOI/work-level citation metadata can be absent. Each candidate preserves the
paper source, machine classification and known missing data.
"""
import argparse,csv,json,pathlib,re
from build_provisional_rankings import classify

ELECTRICAL=re.compile(
    r"\b(?:bipolar.electrochem\w*|bipolar.electrod\w*|"
    r"electrochem\w*|wirefree|wire.free|organic.electronic.ion.pump\w*|"
    r"electroceutical\w*|wireless.bioelectronic|iontronic|electroactive|"
    r"electrorespons\w*|conducting.polymer|pedot|bioelectronic|"
    r"electrical.stimulation|electric.field|nanoantenna\w*)\b",re.I)
REMOTE=re.compile(
    r"\b(?:wireless|wirefree|wire.free|unwired|remote\w*|contactless|"
    r"inductive\w*|photovoltaic\w*|ultrasound|ultrasonic|"
    r"near.field.communication|nfc|magnetic.field|externally.applied|"
    r"light.powered|acoustic)\b",re.I)
THERAPY=re.compile(
    r"\b(?:therap\w*|treat\w*|drug\w*|release|deliver\w*|"
    r"neuron\w*|nerve|regenerat\w*|tissue|glioblastoma|"
    r"apoptos\w*|wound|cell\w*|cancer|tumou?r\w*|"
    r"biomolecul\w*|neurotransmitter|acetylcholine|pain)\b",re.I)
POTENTIALLY_DIAGNOSTIC=re.compile(
    r"\b(?:biosens\w*|diagnos\w*|detection|detector|sensor|monitoring|"
    r"electrochemiluminescen\w*|immunoassay|aptasensor)\b",re.I)
PRIMARY_THERAPY=re.compile(
    r"\b(?:therapy|therapeutic|treatment|tumou?r|cancer|wound.heal\w*|"
    r"drug.release|drug.deliver\w*|cell.stimulation|"
    r"nerve.regenerat\w*|cancer.cell.death)\b",re.I)
FALSE_POSITIVE=re.compile(
    r"\b(?:fuel.cell|water.splitting|hydrogen.evolution.catalyst|"
    r"battery.anode|zinc.air.batter\w*|"
    r"electrochemical.water.treatment|electrochemical.reactor|"
    r"catalytic.water.splitting|energy.storage.device)\b",re.I)
REVIEWS=re.compile(r"\b(?:review|perspective|bibliometric|scientometric|overview|meta.analysis)\b",re.I)
def normalize_doi(doi):
    s=str(doi or "").lower().strip()
    for x in ("https://doi.org/","http://doi.org/","https://dx.doi.org/"):
        if s.startswith(x):s=s[len(x):]
    return s

def collect(raw):
    out=[]
    for r in raw:
        title=r.get("title") or ""
        abstract=r.get("abstract") or ""
        combined=title+" "+abstract
        if not ELECTRICAL.search(title):continue
        if not REMOTE.search(combined):continue
        if not THERAPY.search(combined):continue
        if FALSE_POSITIVE.search(title):continue
        if POTENTIALLY_DIAGNOSTIC.search(title) and not PRIMARY_THERAPY.search(title):
            continue
        primary=re.compile(r"\b(?:review|perspective|bibliometric|meta.analysis)\b",re.I)
        is_review=bool(primary.search(title) or
                       any(REVIEWS.search(str(p)) for p in (r.get("publication_types") or [])) or
                       normalize_doi(r.get("doi")) in {"10.1039/d3bm01946b","10.1016/j.elecom.2024.107832"})
        # Every included record has at least a topical title and a reference.
        original,exclusions=classify([r])
        status=("review/background_reference" if is_review else
                "citation_eligible_machine_candidate" if original and "Electrochemical" in original[0]["modalities"]
                else "awaiting_full_text_and_identity_review")
        doi=normalize_doi(r.get("doi"))
        oa=r.get("openalex_id") or ""
        link="https://doi.org/"+doi if doi else oa
        out.append({"title":title,"year":r.get("year"),"doi":doi,
                    "pmid":r.get("pmid") or "","openalex_work_id":oa,
                    "url":link,"screening_status":status,
                    "has_openalex_citations":isinstance(r.get("citations_openalex"),int),
                    "openalex_citations":r.get("citations_openalex"),
                    "author_names":[a.get("name","") for a in r.get("authors") or []],
                    "author_ids_available":sum(bool(a.get("openalex_author_id") or a.get("orcid")) for a in r.get("authors") or []),
                    "source_databases":r.get("source_databases") or [],
                    "abstract_excerpt":abstract[:380],
                    "exclusion_reason_from_ranking":", ".join(exclusions) if exclusions else "",
                    "researcher_positions_not_assigned":True})
    out.sort(key=lambda x:(-int(x["year"] or 0) if str(x["year"] or "").isdigit() else 0,x["title"].casefold()))
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    raw=json.loads(pathlib.Path(a.input).read_text(encoding="utf-8"))["records"]
    papers=collect(raw)
    statuses={k:sum(p["screening_status"]==k for p in papers) for k in sorted({p["screening_status"] for p in papers})}
    result={"source_type":"Machine-discovered electrochemical bibliography, not validated eligible studies",
            "total_candidate_papers":len(papers),"status_counts":statuses,"papers":papers,
            "limitations":["Titles and partial abstracts may misclassify papers.",
                           "No publication in this directory is automatically attributed to a ranked author when its identifiers are absent.",
                           "Reviews and enabling platforms may be included for literature discovery but do not imply demonstrated therapeutic efficacy.",
                           "Only independently verified original research should enter a definitive international scientist ranking."]}
    dest=pathlib.Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    fieldnames=["title","year","doi","pmid","url","screening_status","has_openalex_citations","openalex_citations","author_names","source_databases","exclusion_reason_from_ranking"]
    with dest.with_suffix(".csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames);w.writeheader()
        for p in papers:w.writerow({k:"; ".join(p[k]) if isinstance(p[k],list) else p.get(k) for k in fieldnames})
    print("Electrochemical literature screening queue:",len(papers),statuses)
    if len(papers)<25:raise SystemExit("Too few candidate records; check search/heuristic inputs.")
if __name__=="__main__":main()
