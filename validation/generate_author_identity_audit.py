#!/usr/bin/env python3
"""Reproducibly sample author–paper links for *independent* identity verification.

The selected author bylines/IDs are unverified candidates. No automated decision
is substituted for publisher/ORCID corroboration, and rank is hidden from reviewer.
"""
import argparse,collections,csv,hashlib,json,pathlib,random,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"methods"))
from build_provisional_rankings import norm_aid,norm_orcid
from build_electrochemical_queue import collect

SEED=20261011
QUOTAS={"conflicting_orcid":40,"prominent_researcher":60,"electrochemical_therapy":60,
        "identifier_missing":50,"field_wide_random":60}
FIELDS=["audit_id","paper_doi_or_openalex","byline_author_name","candidate_openalex_author_id",
    "candidate_orcid","publisher_byline_url","orcid_crosscheck_url","institution_evidence",
    "classification_correct_wrong_person_split_ambiguous_unverifiable","independent_reviewer",
    "reconciled_identity","notes","review_date","source_evidence_url","publisher_byline_match_yes_no_uncertain"]
def doi_norm(s):
    s=str(s or "").strip().casefold()
    for p in ("https://doi.org/","http://doi.org/"):
        if s.startswith(p):s=s[len(p):]
    return s
def write_csv(path,fields,rows):
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)
def sampling(corpus,rankings,seed=SEED,quotas=QUOTAS):
    conflict=collections.defaultdict(set)
    for r in corpus:
        for a in (r.get("authors") or []):
            orcid=norm_orcid(a.get("orcid"));aid=norm_aid(a.get("openalex_author_id"))
            if orcid and aid:conflict[orcid].add(aid)
    conflicting={oid for oid,ids in conflict.items() if len(ids)>1}
    prominent={norm_aid(p.get("openalex_author_id"))
               for p in rankings["rankings"].get("Overall",[])[:50] if p.get("openalex_author_id")}
    queue=collect(corpus)
    electro_ids={q["openalex_work_id"] for q in queue if q.get("openalex_work_id")}
    electro_doi={doi_norm(q["doi"]) for q in queue if q.get("doi")}
    frames={x:[] for x in QUOTAS}
    seen=set()
    for r in corpus:
        doi=doi_norm(r.get("doi"))
        work=r.get("openalex_id") or ""
        if not work and not doi:continue
        in_queue=work in electro_ids or doi in electro_doi
        for i,a in enumerate(r.get("authors") or []):
            name=(a.get("name") or "").strip()
            if not name:continue
            oid=norm_orcid(a.get("orcid"));aid=norm_aid(a.get("openalex_author_id"))
            k=(doi or work,aid or oid or name.casefold())
            if k in seen:continue
            seen.add(k)
            if oid in conflicting:label="conflicting_orcid"
            elif aid in prominent:label="prominent_researcher"
            elif in_queue:label="electrochemical_therapy"
            elif not oid and not aid:label="identifier_missing"
            else:label="field_wide_random"
            institutions="; ".join(inst.get("name") or "" for inst in a.get("institutions") or [] if isinstance(inst,dict))
            link="https://doi.org/"+doi if doi else work
            rid="I"+hashlib.sha256((str(k)).encode("utf-8")).hexdigest()[:20]
            frames[label].append({
                "audit_id":rid,"paper_doi_or_openalex":doi or work,
                "byline_author_name":name,"candidate_openalex_author_id":aid,
                "candidate_orcid":oid,"publisher_byline_url":link,
                "orcid_crosscheck_url":"https://orcid.org/"+oid if oid else "",
                "institution_evidence":institutions,
                "_stratum":label,"_year":r.get("year"),"_work":work,
                "_author_position":a.get("position") or ("first" if i==0 else "unknown"),
            })
    rng=random.Random(seed)
    selected=[]
    for label,rows in frames.items():
        sorted_rows=sorted(rows,key=lambda v:v["audit_id"])
        draws=rng.sample(sorted_rows,min(quotas[label],len(sorted_rows)))
        for d in draws:
            d["_population"]=len(sorted_rows);d["_sample_size"]=len(draws)
            selected.append(d)
    rng.shuffle(selected)
    reviewer=[{k:r.get(k,"") for k in FIELDS} for r in selected]
    coordinator=[{**r,"sampling_probability":round(r["_sample_size"]/r["_population"],10),
         "sampling_weight":round(r["_population"]/r["_sample_size"],8)} for r in selected]
    manifest={"seed":seed,"quotas":quotas,"source_author_link_rows":len(seen),
        "frames":{k:len(v) for k,v in frames.items()},
        "sampled":{k:sum(r["_stratum"]==k for r in selected) for k in frames},
        "total_sample":len(selected),"orcid_conflicts_observed":len(conflicting),
        "status":"candidate byline links awaiting publisher and ORCID verification"}
    return reviewer,coordinator,manifest

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",required=True)
    p.add_argument("--rankings",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--seed",type=int,default=SEED)
    a=p.parse_args()
    corpus=json.loads(pathlib.Path(a.candidates).read_text(encoding="utf-8"))["records"]
    ranks=json.loads(pathlib.Path(a.rankings).read_text(encoding="utf-8"))
    reviewers,key,manifest=sampling(corpus,ranks,seed=a.seed)
    out=pathlib.Path(a.output);out.mkdir(exist_ok=True,parents=True)
    write_csv(out/"author_identity_audit_BLANK.csv",FIELDS,reviewers)
    coordinator_fields=FIELDS+["_stratum","_year","_work","_author_position","_population",
        "_sample_size","sampling_probability","sampling_weight"]
    write_csv(out/"author_identity_sampling_key.csv",coordinator_fields,key)
    (out/"author_identity_sampling_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("IDENTITY AUDIT",json.dumps(manifest))
    if len(reviewers)<100:raise SystemExit("Too few identity pairs to attempt cross-field validation")
if __name__=="__main__":main()
