#!/usr/bin/env python3
"""Independent, reproducible red-flag audit of provisional Atlas rankings.

NOT an independent scientific review. Counts metadata limitations instead of
implicitly treating absent metadata as proof of peer-review or researcher identity.
"""
import argparse,collections,csv,datetime,hashlib,json,pathlib,re
from build_provisional_rankings import normalized_work_title
NON_ORIGINAL={"dissertation","conference-paper","conference-abstract","review",
    "book","book-chapter","preprint","editorial","erratum","report","peer-review",
    "paratext","retraction"}
def norm(s):
    return re.sub(r"[^a-z0-9]+","",str(s or "").lower())
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",required=True)
    p.add_argument("--ranking",required=True)
    p.add_argument("--search-summary",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    corpus=json.loads(pathlib.Path(a.candidates).read_text(encoding="utf8"))["records"]
    ranking=json.loads(pathlib.Path(a.ranking).read_text(encoding="utf8"))
    summary=json.loads(pathlib.Path(a.search_summary).read_text(encoding="utf8"))
    by_openalex={x.get("openalex_id"):x for x in corpus if x.get("openalex_id")}
    works={}
    identity_dupes=0
    duplicate_evidence=[]
    for group,authors in ranking["rankings"].items():
        for author in authors:
            seen=collections.defaultdict(list)
            for paper in author.get("papers") or []:
                wid=paper.get("url") or paper.get("doi") or ""
                works[wid]=by_openalex.get(wid) or {}
                seen[normalized_work_title(paper.get("title"))].append(paper)
            for title,items in seen.items():
                if title and len(items)>1:
                    identity_dupes+=1
                    if len(duplicate_evidence)<25:
                        duplicate_evidence.append({"category":group,"academic":author.get("name"),
                            "title":items[0].get("title"),"occurrences":len(items),
                            "work_ids":";".join(x.get("url","") for x in items)})
    types=collections.Counter(str(w.get("openalex_work_type") or "unspecified").casefold() for w in works.values())
    journal_metadata=types["article"]
    unknown_metadata=types["unspecified"]
    nonoriginal={kind:n for kind,n in types.items() if kind in NON_ORIGINAL}
    scored_missing_doi=sum(not w.get("doi") and not w.get("pmid") for w in works.values())
    ranked_rows=ranking["rankings"].get("Overall") or []
    authors_without_institution=sum((x.get("institution") or "Not available")=="Not available" for x in ranked_rows)
    doi_groups=collections.defaultdict(list)
    for r in corpus:
        title=normalized_work_title(r.get("title"))
        if title:
            doi_groups[(title,str(r.get("year") or ""))].append(r)
    repeated=sum(len(v)>1 for v in doi_groups.values())
    excess=sum(len(v)-1 for v in doi_groups.values() if len(v)>1)
    scores=ranking["summary"]
    findings=[
        {"severity":"critical","check":"independent eligibility screening",
         "observed":summary.get("full_text_screened",0),"required":"independent full-text review",
         "effect":"No published global ranking is validated"},
        {"severity":"high","check":"publication-type metadata missing among scored works",
         "observed":unknown_metadata,"required":"verify original journal source",
         "effect":"Journal status and research type not established for those works"},
        {"severity":"high","check":"ambiguous ORCID/OpenAlex links",
         "observed":scores.get("ambiguous_orcid_to_openalex_mappings",0),
         "required":"researcher-level disambiguation","effect":"Possible split or merged publication histories"},
        {"severity":"high","check":"record retrieval errors",
         "observed":summary.get("errors",0),"required":"resolve or account for source API errors",
         "effect":"Coverage cannot be considered exhaustive"},
        {"severity":"medium","check":"repeated title+year records in full harvest",
         "observed":repeated,"required":"manual DOI and version reconciliation",
         "effect":"Potential preprint, repository, and journal duplicates"},
        {"severity":"critical" if nonoriginal else "pass",
         "check":"known nonoriginal document types in scored works",
         "observed":nonoriginal,"required":"0",
         "effect":"Theses, conference papers and reviews must never count as original articles"},
        {"severity":"critical" if scored_missing_doi else "pass",
         "check":"scored works without DOI or PMID",
         "observed":scored_missing_doi,"required":"0",
         "effect":"Cannot establish original publication provenance"},
        {"severity":"critical" if identity_dupes else "pass",
         "check":"exact duplicate paper titles within author score rows",
         "observed":identity_dupes,"required":"0",
         "effect":"Duplicate works can inflate scores"},
        {"severity":"medium","check":"ranked scholars without dated institution evidence",
         "observed":authors_without_institution,"required":"manual affiliation verification",
         "effect":"Institutional representation may be incomplete"},
    ]
    report={"audit_generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status":"NOT_VALIDATED_WORLD_RANKING",
        "scope":"automated evidence audit; no independent full-text or byline verification",
        "candidate_records":len(corpus),"machine_screened_papers":scores.get("machine_screened_papers",0),
        "electrochemical_papers":scores.get("paper_modalities",{}).get("Electrochemical",0),
        "overall_scored_researchers":len(ranked_rows),
        "unique_scored_work_records":len(works),
        "scored_work_metadata":{"explicit_article":journal_metadata,
            "unspecified_type":unknown_metadata,
            "explicit_nonoriginal":nonoriginal,
            "identifier_missing":scored_missing_doi},
        "candidate_title_year_duplicate_groups":repeated,
        "candidate_title_year_extra_rows":excess,
        "duplicate_score_evidence_groups":identity_dupes,
        "full_text_screened":summary.get("full_text_screened",0),
        "search_query_errors":summary.get("errors",0),
        "orcid_mapping_conflicts":scores.get("ambiguous_orcid_to_openalex_mappings",0),
        "ranked_researchers_without_affiliation":authors_without_institution,
        "scoring_script_sha256":hashlib.sha256((pathlib.Path(__file__).with_name("build_provisional_rankings.py")).read_bytes()).hexdigest(),
        "findings":findings,
        "duplicate_evidence_examples":duplicate_evidence,
        "interpretation":"Positions are exploratory within a biased machine-selected corpus and cannot substantiate international standing."
    }
    out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf8")
    with out.with_suffix(".csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=["severity","check","observed","required","effect"])
        writer.writeheader()
        for row in findings:
            writer.writerow({**row,"observed":json.dumps(row["observed"]) if isinstance(row["observed"],dict) else row["observed"]})
    print("Ranking quality findings:",json.dumps(report["scored_work_metadata"]))
    print("Candidate duplicates:",repeated,"source errors:",report["search_query_errors"])
    if nonoriginal or scored_missing_doi or identity_dupes:
        raise SystemExit("Ranking QA failed: nonoriginal or duplicate works remain in scored results")
if __name__=="__main__":main()
