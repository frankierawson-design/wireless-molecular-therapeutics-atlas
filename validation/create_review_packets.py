#!/usr/bin/env python3
"""Freeze, sample and create independent blinded literature-review packets.

Inputs are the immutable 24,904-record GitHub Actions harvest.
Works are selected before human decisions; labels in source data are never
copied into review decisions. No source author or DOI is revealed to reviewers.
"""
import argparse,csv,hashlib,json,pathlib,random,re,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"methods"))
from build_electrochemical_queue import collect

FIELDS=["blind_id","title","year","abstract","document_type_decision","remote_energy",
        "physical_modality","molecular_mechanism","experimental_outcome",
        "eligibility_tier","include_for_full_text","confidence","rationale",
        "source_full_text_checked","full_text_page_or_figure_evidence","reviewer_id"]
ALLOWED_TIERS={"T","P","E","D","R","U"}
def key_for(r):
    return (r.get("doi") or r.get("openalex_id") or 
            re.sub(r"[^a-z0-9]","",str(r.get("title") or "").lower())+":"+str(r.get("year") or "")).lower()
def blind_id(r,seed):
    return hashlib.sha256((seed+"\0"+key_for(r)).encode()).hexdigest()[:16]
def write_csv(path,rows,fieldnames):
    with pathlib.Path(path).open("w",newline="",encoding="utf-8-sig") as fh:
        w=csv.DictWriter(fh,fieldnames=fieldnames,extrasaction="ignore")
        w.writeheader();w.writerows(rows)
def sample(records,seed,hard_target=70,other_target=70):
    # Module's existing high-recall queue supplies the entire electrochemical
    # pilot. All remaining records form distinct sampling strata.
    bykey={key_for(r):r for r in records}
    que=collect(records)
    queue_keys={key_for(p) for p in que}
    # Queue items use normalized DOI/work-ID: enforce identical key semantics.
    qbydoi={str(q.get("doi") or "").lower() for q in que if q.get("doi")}
    qbyoa={str(q.get("openalex_work_id") or "").lower() for q in que if q.get("openalex_work_id")}
    fromqueue=lambda r: (key_for(r) in queue_keys or 
        (r.get("doi") and str(r.get("doi")).lower() in qbydoi) or
        (r.get("openalex_id") and str(r.get("openalex_id")).lower() in qbyoa))
    def difficult(r):
        text=(str(r.get("title") or "")+" "+str(r.get("abstract") or "")[:2200]).lower()
        has_electrical=bool(re.search(r"(electrochem|electroactive|wirefree|wireless|bipolar|bioelectronic|ion.pump|nanoantenna|conducting.polymer)",text))
        has_bio=bool(re.search(r"(therap|drug|neuro|cell|cancer|wound|pain|deliver|release|treat)",text))
        return has_electrical and has_bio
    leftovers=[r for r in records if not fromqueue(r)]
    hard=[r for r in leftovers if difficult(r)]
    hard_keys={key_for(r) for r in hard}
    other=[r for r in leftovers if key_for(r) not in hard_keys]
    rng=random.Random(seed)
    rng.shuffle(hard);rng.shuffle(other)
    selected={}
    for stratum,group in (("hard_negative",hard[:min(hard_target,len(hard))]),
                           ("other_negative",other[:min(other_target,len(other))])):
        for r in group:selected[key_for(r)]={"stratum":stratum,"record":r}
    # Using the *frozen queue* as the exhaustive pilot stratum; machine queue
    # labels have no reviewer authority and remain unblinded in the map only.
    for q in que:
        match=bykey.get(key_for(q))
        if match is None and q.get("doi"):
            match=next((r for r in records if str(r.get("doi") or "").lower()==q["doi"]),None)
        if match is None and q.get("openalex_work_id"):
            match=next((r for r in records if str(r.get("openalex_id") or "").lower()==q["openalex_work_id"]),None)
        if match:selected[key_for(match)]={"stratum":"electrochemical_queue_census","record":match}
    totals={"electrochemical_queue_census":len(que),"hard_negative":len(hard),"other_negative":len(other)}
    fractions={k:(sum(x["stratum"]==k for x in selected.values())/v if v else 0)
               for k,v in totals.items()}
    return list(selected.values()),totals,fractions,len(que)

def run(args):
    manifest=json.loads(pathlib.Path(args.freeze).read_text(encoding="utf8"))
    contents=pathlib.Path(args.input).read_bytes()
    sha=hashlib.sha256(contents).hexdigest()
    if sha!=manifest["source_candidates_sha256"]:
        raise SystemExit("Frozen source SHA-256 mismatch: stop and obtain approved baseline, do not silently replace it")
    corpus=json.loads(contents)["records"]
    if len(corpus)!=manifest["frozen_candidate_count"]:
        raise SystemExit("Frozen candidate count differs: stop")
    seed=manifest["sampling_seed"]
    selected,totals,fractions,qcount=sample(corpus,seed,args.hard,args.other)
    out=pathlib.Path(args.output);out.mkdir(parents=True,exist_ok=True)
    mapping=[];blind=[]
    for row in selected:
        r=row["record"];ident=blind_id(r,seed)
        meta={"blind_id":ident,"stratum":row["stratum"],"selection_probability":fractions[row["stratum"]],
              "doi":r.get("doi") or "","pmid":r.get("pmid") or "",
              "openalex_id":r.get("openalex_id") or "",
              "title":r.get("title") or "","year":r.get("year") or "",
              "authors_json":json.dumps(r.get("authors") or [],ensure_ascii=False),
              "source_databases":(";".join(r.get("source_databases") or [])),
              "source_queries":(";".join(r.get("source_queries") or [])),
              "source_work_type":r.get("openalex_work_type") or "",
              "source_publication_types":";".join(map(str,r.get("publication_types") or []))}
        mapping.append(meta)
        blind.append({"blind_id":ident,"title":r.get("title") or "",
                      "year":r.get("year") or "","abstract":re.sub(r"<[^>]*>"," ",r.get("abstract") or ""),
                      **{f:"" for f in FIELDS if f not in ("blind_id","title","year","abstract")}})
    if len({p["blind_id"] for p in blind})!=len(blind):
        raise SystemExit("Blind ID collision or unhandled multiple title/identifier versions")
    for reviewer in ("A","B"):
        shuffled=blind[:];random.Random(seed+":reviewer:"+reviewer).shuffle(shuffled)
        write_csv(out/f"reviewer_{reviewer}_BLANK.csv",shuffled,FIELDS)
    map_fields=["blind_id","stratum","selection_probability","doi","pmid","openalex_id","title",
                "year","authors_json","source_databases","source_queries","source_work_type","source_publication_types"]
    write_csv(out/"UNBLIND_mapping_DO_NOT_SHARE_WITH_REVIEWERS.csv",
              sorted(mapping,key=lambda x:x["blind_id"]),map_fields)
    details={"protocol_version":manifest["protocol_version"],"frozen_sha256":sha,
             "snapshot_source_run_id":manifest["source_github_run_id"],
             "electrochemical_queue_records":qcount,"selected_total":len(selected),
             "stratum_population_sizes":totals,
             "stratum_sample_sizes":{k:sum(x["stratum"]==k for x in selected) for k in totals},
             "sampling_fractions":fractions,"seed":seed,
             "independent_human_reviewers_completed":0,
             "reviewer_instructions":"Work independently. Keep decision columns blank until you personally review the title/abstract. Record U when source evidence insufficient. Never use source ranking or machine labels as review decisions.",
             "reviewer_blinding":"Title/year/abstract visible; DOI, author names, citation metrics, source query, journal, machine selection status withheld. Titles can inadvertently disclose authors.",
             "limitations":"The broad-corpus hard-negative stratum contains sampled omissions but cannot measure publications absent from the frozen harvest.",
             "stratum_selection":"Queue census plus independent random draws from two disjoint machine-negative strata"}
    (out/"sampling_report.json").write_text(json.dumps(details,indent=2),encoding="utf8")
    (out/"heldout_gold_reference_BLANK.csv").write_text(
        "doi,modality,external_discovery_source,reference_date,independent_eligibility_verified,adjudicator,eligible_tier,notes\n",
        encoding="utf8")
    (out/"adjudication_BLANK.csv").write_text(
        "blind_id,final_tier,final_remote_energy,final_modality,final_document_type,final_include,adjudicator,reason,original_paper_url,full_text_location,source_evidence,adjudication_date\n",
        encoding="utf8")
    print(json.dumps(details,indent=2))
    return details
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True);parser.add_argument("--freeze",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--hard",type=int,default=70);parser.add_argument("--other",type=int,default=70)
    run(parser.parse_args())
