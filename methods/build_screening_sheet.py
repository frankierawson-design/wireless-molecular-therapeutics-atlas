#!/usr/bin/env python3
"""Create blinded-review-ready title/abstract and full-text forms from candidate JSON.

DO NOT treat suggested modality as confirmed or inferred eligibility as final.
"""
import argparse, csv, json, pathlib, re
def suggest(text):
    t=text.casefold()
    pats={
      "Ultrasound":r"ultrasound|sonodynam|acoustic|piezoelectric|sonosensiti",
      "Magnetic":r"magnetotherm|magnetoelectric|magnetomechan|magnetic field",
      "Optical":r"photopharmac|photodynamic|photoswitch|photocag|near infrared|nir|photoactiv|light.activ",
      "Radiofrequency":r"radio.frequency|radiofrequency|rf.trigger|electromagnetic",
      "Electrochemical":r"bipolar electrochem|electrochemical|electron transfer|electro.pharmaceut",
    }
    return "|".join(k for k,p in pats.items() if re.search(p,t)) or "Undetermined"
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="output/candidates.json")
    ap.add_argument("--output",default="output/manual_screening_sheet.csv")
    a=ap.parse_args()
    rows=json.loads(pathlib.Path(a.input).read_text())["records"]
    out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    fieldnames=["record_number","title","year","doi","pmid","openalex_id","source_databases","source_queries",
                "modality_suggested_not_confirmed","abstract","author_names_unverified",
                "reviewer_1","reviewer_1_title_abstract_decision","reviewer_2","reviewer_2_title_abstract_decision",
                "consensus_title_abstract","full_text_access","full_text_inclusion",
                "exclusion_reason","stimulus_confirmed","transduction_confirmed",
                "therapeutic_endpoint_confirmed","study_type","notes","identity_verification_status"]
    with out.open("w",newline="",encoding="utf-8-sig") as fh:
        w=csv.DictWriter(fh,fieldnames=fieldnames);w.writeheader()
        for i,row in enumerate(rows,1):
            w.writerow({"record_number":i,"title":row.get("title"),"year":row.get("year"),
                 "doi":row.get("doi"),"pmid":row.get("pmid"),"openalex_id":row.get("openalex_id"),
                 "source_databases":"; ".join(row.get("source_databases") or []),
                 "source_queries":"; ".join(row.get("source_queries") or []),
                 "modality_suggested_not_confirmed":suggest((row.get("title") or "")+" "+(row.get("abstract") or "")),
                 "abstract":row.get("abstract") or "",
                 "author_names_unverified":"; ".join(a.get("name") or "" for a in row.get("authors") or []),
                 "identity_verification_status":"UNVERIFIED"})
    print("Created",out,"with",len(rows),"candidate records; decisions intentionally blank")
if __name__=="__main__": main()
