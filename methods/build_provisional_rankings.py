#!/usr/bin/env python3
"""Generate explicitly provisional author rankings from a bounded literature harvest.

Only OpenAlex-author-ID-backed, citation-bearing machine-screened publications score.
No claim of exhaustive searching, full-text review or identity reconciliation.
"""
import argparse, collections, csv, json, math, pathlib, re, statistics
from datetime import datetime, timezone

MODALITIES={
 "Ultrasound":r"\b(?:ultrasound|sonodynamic|sonosensiti[sz]\w*|sonoporat\w*|sonochem\w*|acoustic.?(?:trigger|activat|stimulation|drug)|focused.ultrasound)\b",
 "Magnetic":r"\b(?:magnetothermal|magnetoelectric|magnetomechanical|magnetically.trigger\w*|magnetic.hyperthermia|magnetic.field|magnetic.actuat\w*|magnetic.stimulation|magnetically.control\w*)\b",
 "Optical":r"\b(?:photodynamic|photothermal|photopharmacolog\w*|photoactivat\w*|photoswitch\w*|photocag\w*|light.trigger\w*|light.activated|near.infrared.(?:activat|trigger|respons)|NIR.(?:activat|trigger|respons))\b",
 "Radiofrequency":r"\b(?:radiofrequency|radio.frequency|RF.trigger\w*|RF.activat\w*|microwave.trigger\w*)\b",
 "Electrochemical":r"\b(?:wireless.bipolar|bipolar.electrochem\w*|electrochemical.drug|electrochemical.nitric.oxide|electroceutical\w*|electro.pharmaceut\w*|wireless.electrical|electrical.stimulation|electric.field|electrochemical.therapy|electron.transfer.therapy|electrochemical.release|electrochemical.generation|electric.pulse\w*)\b"
}
THERAPY=r"\b(?:therap\w*|treat\w*|drug\w*|deliver\w*|release|cancer|tumou?r\w*|glioblastoma|melanoma|neuron\w*|nerve|neurostimulat\w*|regenerat\w*|heal\w*|apoptos\w*|ablat\w*|immunotherap\w*|pain|wound|disease|cell.death|chemotherap\w*|blood.brain.barrier|brain.stimulation|cell.modulat\w*)\b"
REVIEW=r"\b(?:review|overview|bibliometric|meta.analysis|perspective|scientometric|recent.advances|current.progress|state.of.the.art|prospects|research.progress|roadmap|survey|abstract \d+)\b"
DIAGNOSTIC=r"\b(?:biosens\w*|diagnos\w*|detect\w*|monitor\w*|sensor|aptasens\w*)\b"
TRANSLATION=r"\b(?:in.vivo|animal|mice|mouse|xenograft|patient|clinical|porcine|human.trial|wound.closure|tumo\w*.regression)\b"
REVIEW_ABSTRACT=r"\b(?:this review|in this review|here we review|review of current|the current review|we summariz|this perspective)\b"
SCORING_WEIGHTS={"citation_impact":0.35,"relevant_output":0.25,"authorship_leadership":0.20,"translational_indicators":0.10,"sustained_activity":0.10}
def matches(pattern,text):return bool(re.search(pattern,text or "",re.I))
def classify(records):
    included=[]; excluded=collections.Counter()
    for r in records:
        try: year=int(r.get("year") or 0)
        except (ValueError,TypeError):year=0
        title=r.get("title") or ""
        if not 2000<=year<=2026:excluded["publication_year_out_of_scope"]+=1;continue
        if not r.get("openalex_id") or not isinstance(r.get("citations_openalex"),int):
            excluded["no_linked_openalex_work_or_citation"]+=1;continue
        if matches(REVIEW,title) or matches(REVIEW_ABSTRACT,r.get("abstract") or ""):
            excluded["possible_review_or_nonoriginal"]+=1;continue
        mods=[m for m,p in MODALITIES.items() if matches(p,title)]
        if not mods:excluded["no_explicit_remote_energy_in_title"]+=1;continue
        if not matches(THERAPY,title):excluded["no_therapeutic_endpoint_in_title"]+=1;continue
        if matches(DIAGNOSTIC,title) and not matches(r"\b(?:release|drug.delivery|therap\w*|treat\w*|neurostimulat\w*|wound.healing|cancer.therap\w*)\b",title):
            excluded["diagnostics_only"]+=1;continue
        if "Radiofrequency" in mods and matches(r"\b(?:atrial.fibrillation|cardiac|catheter|arrhythmia)\b",title) and not matches(r"\b(?:drug|nanoparticle|delivery|molecular)\b",title):
            mods.remove("Radiofrequency")
        if not mods:excluded["nonmolecular_radiofrequency"]+=1;continue
        if len(mods)>=2: mods.append("Hybrid")
        if not any(a.get("openalex_author_id") for a in (r.get("authors") or [])):
            excluded["author_identifier_missing"]+=1;continue
        r2=dict(r);r2["year"]=year;r2["modalities"]=mods
        included.append(r2)
    return included,excluded

def cohort_percentile(citations,year,modality,cohorts):
    values=cohorts.get((year,modality),[])
    if len(values)<10:
        values=[c for (y,m),arr in cohorts.items() if m==modality and abs(y-year)<=1 for c in arr]
    if not values:return 50.0
    less=sum(v<citations for v in values)
    same=sum(v==citations for v in values)
    return round(100*(less+.5*same)/len(values),2)

def score(papers):
    n=len(papers)
    citation=statistics.mean(sorted((p["citation_percentile"] for p in papers),reverse=True)[:min(10,n)])
    output=min(100,100*math.log1p(n)/math.log1p(60))
    lead=sum(p["authorship"] in ("first","last") for p in papers)
    leadership=min(100,100*math.log1p(lead)/math.log1p(35))
    trans=100*sum(matches(TRANSLATION,p["title"]) for p in papers)/n
    activity=100*min(1,len({p["year"] for p in papers})/9)
    components={"citation_impact":round(citation,2),"relevant_output":round(output,2),
                "authorship_leadership":round(leadership,2),"translational_indicators":round(trans,2),
                "sustained_activity":round(activity,2)}
    total=sum(components[k]*SCORING_WEIGHTS[k] for k in SCORING_WEIGHTS)
    return round(total,2),components

def make_ranks(included):
    cohorts=collections.defaultdict(list)
    for r in included:
        for mod in r["modalities"]:cohorts[(r["year"],mod)].append(r["citations_openalex"])
    authors=collections.defaultdict(lambda:{"name":"","orcid":"","papers":{}})
    for r in included:
        mods=r["modalities"]
        percentile=round(sum(cohort_percentile(r["citations_openalex"],r["year"],m,cohorts) for m in mods)/len(mods),2)
        a_list=[a for a in r.get("authors",[]) if a.get("openalex_author_id")]
        for i,a in enumerate(a_list):
            aid=a["openalex_author_id"]
            person=authors[aid]
            person["name"]=a.get("name") or person["name"]
            person["orcid"]=a.get("orcid") or person["orcid"]
            position=a.get("position") or ("first" if i==0 else "last" if i==len(a_list)-1 else "middle")
            evidence={"title":r["title"],"doi":r.get("doi"),"url":r.get("openalex_id"),"year":r["year"],
                      "citations":r["citations_openalex"],"citation_percentile":percentile,
                      "modalities":mods,"authorship":position}
            key=r.get("doi") or r.get("openalex_id")
            person["papers"][key]=evidence
    ranks={}
    for group in ["Overall",*MODALITIES,"Hybrid"]:
        rows=[]
        minimum=3 if group=="Overall" else 2
        for aid,a in authors.items():
            papers=[p for p in a["papers"].values() if group=="Overall" or group in p["modalities"]]
            if len(papers)<minimum:continue
            total,parts=score(papers)
            papers.sort(key=lambda p:(p["citations"],p["year"]),reverse=True)
            rows.append({"name":a["name"],"openalex_author_id":aid,"orcid":a["orcid"],
                         "score":total,"publication_count":len(papers),
                         "indexed_citations":sum(p["citations"] for p in papers),
                         "first_last_papers":sum(p["authorship"] in ("first","last") for p in papers),
                         "components":parts,"papers":papers})
        rows.sort(key=lambda a:(-a["score"],-a["publication_count"],a["name"].casefold(),a["openalex_author_id"]))
        for i,a in enumerate(rows,1):a["rank"]=i
        ranks[group]=rows
    return ranks,len(authors)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--csv",required=True)
    opts=ap.parse_args()
    raw=json.loads(pathlib.Path(opts.input).read_text(encoding="utf-8"))
    input_records=raw["records"]
    included,excluded=classify(input_records)
    ranked,author_count=make_ranks(included)
    stats={"candidate_records":len(input_records),"machine_screened_papers":len(included),
           "openalex_author_id_candidates":author_count,
           "ranked_researchers":{k:len(v) for k,v in ranked.items()},
           "paper_modalities":dict(collections.Counter(m for r in included for m in r["modalities"])),
           "exclusions":dict(excluded)}
    result={"generated_utc":datetime.now(timezone.utc).isoformat(),
            "ranking_label":"Provisional automated literature-index ranking (NOT verified world standing)",
            "methods_version":"2026.10-provisional-1",
            "summary":stats,"weights":SCORING_WEIGHTS,
            "minimum_relevant_papers":{"Overall":3,"each_modality":2},
            "limitations":[
                "Automated title/abstract inclusion is not a human full-text systematic review.",
                "Search queries and per-query pagination are bounded and may omit major researchers.",
                "Only works with OpenAlex citation counts AND linked OpenAlex author IDs score; Europe PMC-only and unresolved identities are excluded from numerical positions.",
                "Citations are ranked within the harvested year/modality cohort, not global field-normalized citations.",
                "Clinical translation is a title-keyword proxy, not validated clinical impact.",
                "Scored positions are relative to this particular retrieved and machine-screened dataset, not an exhaustive world ranking."
            ],"rankings":ranked}
    out=pathlib.Path(opts.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    csvpath=pathlib.Path(opts.csv);csvpath.parent.mkdir(parents=True,exist_ok=True)
    with csvpath.open("w",newline="",encoding="utf-8-sig") as f:
        fields=["category","rank","researcher","openalex_author_id","orcid","score","machine_matched_papers","indexed_citations","first_last_papers",*SCORING_WEIGHTS]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for category,rows in ranked.items():
            for r in rows:
                w.writerow({"category":category,"rank":r["rank"],"researcher":r["name"],
                            "openalex_author_id":r["openalex_author_id"],"orcid":r["orcid"],
                            "score":r["score"],"machine_matched_papers":r["publication_count"],
                            "indexed_citations":r["indexed_citations"],"first_last_papers":r["first_last_papers"],
                            **r["components"]})
    print(json.dumps(stats,indent=2))
    if not ranked["Overall"]:raise SystemExit("No ranking rows. Check corpus and screening logic.")
if __name__=="__main__":main()
