#!/usr/bin/env python3
"""Publisher-reference DOI reconciliation without inventing missing researcher credit."""
import argparse,json,pathlib,re
from electropharmaceutics_focus import norm_doi, screen
from build_provisional_rankings import norm_orcid
def compare(corpus,manifest):
    indexed={norm_doi(r.get("doi")):r for r in corpus if r.get("doi")}
    rows=[]
    included,_=screen(corpus)
    scored={norm_doi(p.get("doi")) for p in included}
    expected=norm_orcid(manifest["orcid"])
    last_name=manifest["researcher"].split()[-1].casefold()
    for work in manifest["works"]:
        doi=norm_doi(work["doi"])
        found=indexed.get(doi)
        authors=found.get("authors",[]) if found else []
        names=[a for a in authors if last_name in str(a.get("name") or "").casefold()]
        confirmed=any(norm_orcid(a.get("orcid"))==expected for a in names)
        source_name=bool(names)
        if not found:identity="publication_not_harvested"
        elif confirmed:identity="work_level_orcid_matches"
        elif source_name:identity="matching_byline_only_identity_not_confirmed"
        else:identity="author_not_matched_in_index_metadata"
        rows.append({
          "doi":doi,"year":work["year"],"title":work["title"],
          "publisher_source":work["source"],
          "reference_role":work["anticipated_review_class"],
          "retrieved":bool(found),
          "author_identity_status":identity,
          "machine_eligible_publication":doi in scored,
          "in_ranking_only_if_identity_verified":bool(doi in scored and confirmed),
          "indexed_title":found.get("title") if found else None,
          "indexed_document_type":found.get("openalex_work_type") if found else None,
          "status":"NOT_INDEPENDENTLY_FULL_TEXT_REVIEWED"
        })
    return {
      "status":"BIBLIOGRAPHY_SAMPLE_NOT_EXHAUSTIVE",
      "researcher":manifest["researcher"],
      "orcid":expected,
      "reference_source":manifest.get("source_explanation"),
      "total_reference_works":len(rows),
      "found_in_candidate_corpus":sum(r["retrieved"] for r in rows),
      "machine_eligible":sum(r["machine_eligible_publication"] for r in rows),
      "full_text_screened_independently":0,
      "reference_works":rows,
      "limitations":["Publisher-source reference sample, not a full ORCID/Scopus/Google Scholar/Nottingham bibliography.",
       "Work-level bylines, title duplicates and ORCID mappings require adjudication before scholar credit.",
       "A found original study may be excluded legitimately as an enabling platform; a missing DOI is a retrieval problem.",
       "Machine eligibility does not validate claims or determine the researcher's standing."]
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--reference",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    records=json.loads(pathlib.Path(a.input).read_text(encoding="utf-8"))["records"]
    ref=json.loads(pathlib.Path(a.reference).read_text(encoding="utf-8"))
    result=compare(records,ref)
    dest=pathlib.Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Publisher identified:",result["total_reference_works"],
          "harvested:",result["found_in_candidate_corpus"],
          "machine eligible:",result["machine_eligible"])
if __name__=="__main__":main()
