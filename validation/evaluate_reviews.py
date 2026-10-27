#!/usr/bin/env python3
"""Evaluate independent dual screening only after reviews and adjudication exist.

Blank reviewer templates generate a "NOT_STARTED" readiness report and NO
accuracy estimates. Machine labels are read only after reviewers lock decisions.
"""
import argparse,collections,csv,datetime,hashlib,json,math,pathlib,random,statistics,sys
from urllib.parse import urlparse

VALID={"include","exclude","uncertain"}
from scopes import SCOPES, KNOWN_SENTINELS
MODALITIES=SCOPES["legacy_wireless"]

def valid_date(value):
    try:
        datetime.date.fromisoformat(value or "")
        return True
    except (ValueError, TypeError):
        return False

def full_text_verified(row, decision):
    return (row.get("full_text_verified_yes_no") == "yes"
            and bool(row.get("evidence_source_url"))
            and bool(row.get("supporting_text_or_page"))
            and row.get("article_type_verified_yes_no_uncertain") == "yes"
            and row.get("doi_pmid_verified_yes_no_uncertain") == "yes"
            and (decision != "include" or row.get("highest_evidence_tier_T0_T1_T2_T3_uncertain") in {"T2", "T3"}))

def read_csv(path):
    with pathlib.Path(path).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))
def normalize_doi(v):
    s=(v or "").strip().casefold()
    for p in ("https://doi.org/","http://doi.org/","https://dx.doi.org/"):
        if s.startswith(p):s=s[len(p):]
    return s
def wilson(hit,total,z=1.96):
    if total<=0:return None
    p=hit/total;denom=1+z*z/total
    center=(p+z*z/(2*total))/denom
    half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denom
    return [round(max(0,center-half),4),round(min(1,center+half),4)]
def kappa(a,b):
    categories=sorted(set(a+b))
    n=len(a)
    if not n:return None
    obs=sum(x==y for x,y in zip(a,b))/n
    ca=collections.Counter(a);cb=collections.Counter(b)
    exp=sum(ca[x]/n*cb[x]/n for x in categories)
    return {"observed_agreement":round(obs,4),"cohens_kappa":round((obs-exp)/(1-exp),4) if exp<1 else None,
            "n":n}
def bootstrap_confusion(rows,reps=800,seed=20261011):
    groups=collections.defaultdict(list)
    for x in rows:groups[x["stratum"]].append(x)
    if not groups:return {}
    rng=random.Random(seed)
    scores={"recall":[],"precision":[],"specificity":[]}
    for _ in range(reps):
        sample=[]
        for members in groups.values():
            sample.extend(rng.choice(members) for _ in range(len(members)))
        counts=weighted_confusion(sample)
        calculated=rates(counts)
        for key in scores:
            if calculated.get(key) is not None:scores[key].append(calculated[key])
    results={}
    for key,values in scores.items():
        if not values:results[key]=None;continue
        values.sort()
        results[key]=[round(values[int(.025*(len(values)-1))],4),
                      round(values[int(.975*(len(values)-1))],4)]
    return results
def weighted_confusion(rows):
    a=collections.Counter()
    for x in rows:
        truth=x["truth"]=="include";pred=x["machine"]=="include"
        cat=("TP" if truth else "FP") if pred else ("FN" if truth else "TN")
        a[cat]+=x["weight"]
    return {k:round(a[k],6) for k in ("TP","FP","FN","TN")}
def rates(c):
    tp,fp,fn,tn=[c[k] for k in ("TP","FP","FN","TN")]
    return {"recall":round(tp/(tp+fn),4) if tp+fn else None,
            "precision":round(tp/(tp+fp),4) if tp+fp else None,
            "specificity":round(tn/(tn+fp),4) if tn+fp else None,
            "false_negative_rate":round(fn/(tp+fn),4) if tp+fn else None,
            "false_positive_rate":round(fp/(tn+fp),4) if tn+fp else None}

def review_section(a,b,adjud,key,scope="legacy_wireless"):
    if scope != "legacy_wireless" and any(x.get("validation_scope") != scope for x in key):
        raise ValueError("Key scope does not match requested validation scope")
    key_by_id={x["record_id"]:x for x in key}
    if len(key_by_id)!=len(key):raise ValueError("Duplicate record IDs in adjudicator key")
    rev={}
    for n,rows in (("A",a),("B",b)):
        if len({x["record_id"] for x in rows})!=len(rows):raise ValueError("Duplicate review record")
        if {x["record_id"] for x in rows}!={x["record_id"] for x in key}:raise ValueError("Review IDs do not match key")
        rev[n]={x["record_id"]:x for x in rows}
    if len({x["record_id"] for x in adjud}) != len(adjud):
        raise ValueError("Duplicate adjudication record")
    if any(x["record_id"] not in key_by_id for x in adjud):
        raise ValueError("Unknown adjudication record")
    adj={x["record_id"]:x for x in adjud}
    results=[]
    pending=[]
    codes_a={x.get("reviewer_code", "").strip() for x in a} - {""}
    codes_b={x.get("reviewer_code", "").strip() for x in b} - {""}
    overlapping_reviewers=bool(codes_a & codes_b)
    all_agreement_A=[];all_agreement_B=[]
    for rid,item in key_by_id.items():
        ra=rev["A"][rid];rb=rev["B"][rid]
        da=(ra.get("initial_eligibility_include_exclude_uncertain") or "").strip().casefold()
        db=(rb.get("initial_eligibility_include_exclude_uncertain") or "").strip().casefold()
        if not da or not db:
            pending.append({"record_id":rid,"reason":"reviewer decision missing"})
            continue
        if da not in VALID or db not in VALID:raise ValueError("Bad reviewer label for "+rid)
        ca=(ra.get("reviewer_code") or "").strip()
        cb=(rb.get("reviewer_code") or "").strip()
        if not ca or not cb or ca==cb or overlapping_reviewers:
            pending.append({"record_id":rid,"reason":"two distinct reviewer codes required"});continue
        if any(not valid_date(r.get("review_date_yyyy_mm_dd")) or not r.get("reason_code") for r in (ra, rb)):
            pending.append({"record_id":rid,"reason":"dated independent decisions and reasons required"});continue
        all_agreement_A.append(da);all_agreement_B.append(db)
        if da==db and da!="uncertain":
            if not all(full_text_verified(r, da) for r in (ra, rb)):
                pending.append({"record_id":rid,"reason":"both reviewers need full-text verification and evidence"});continue
            final=da
            provenance="independent_reviewer_agreement"
        else:
            row=adj.get(rid,{})
            final=(row.get("final_eligibility_include_exclude_uncertain") or "").strip().casefold()
            if final not in VALID or not (row.get("adjudicator_code") or "").strip() or not (row.get("evidence_source_url") or "").strip():
                pending.append({"record_id":rid,"reason":"third-party adjudication and source link required"});continue
            if (row.get("adjudicator_code") in codes_a | codes_b
                    or not valid_date(row.get("adjudication_date_yyyy_mm_dd"))
                    or not valid_date(row.get("reviewer_A_locked_date"))
                    or not valid_date(row.get("reviewer_B_locked_date"))
                    or row.get("adjudication_date_yyyy_mm_dd", "") < max(row.get("reviewer_A_locked_date", ""), row.get("reviewer_B_locked_date", ""))
                    or row.get("article_type_verified_yes_no_uncertain") != "yes"
                    or row.get("doi_pmid_verified_yes_no_uncertain") != "yes"
                    or not row.get("full_text_page_or_quotation")
                    or (final == "include" and row.get("final_evidence_tier_T0_T1_T2_T3_uncertain") not in {"T2", "T3"})
                    or (final == "exclude" and not row.get("exclusion_reason"))):
                pending.append({"record_id":rid,"reason":"independent full-text adjudication after reviewer locks required"});continue
            provenance="third_party_adjudication"
        if final=="uncertain":
            pending.append({"record_id":rid,"reason":"unresolved after adjudication"});continue
        label_field = "machine_eligible_electrochemical" if scope == "legacy_wireless" else "machine_eligible"
        if scope != "legacy_wireless" and item.get("validation_scope") != scope:
            raise ValueError("Key scope does not match requested validation scope")
        if (item.get(label_field) or "").casefold() not in {"include","exclude"}:
            raise ValueError("Missing machine label for "+rid)
        results.append({"record_id":rid,"stratum":item["frame_stratum"],"truth":final,
                        "machine":item[label_field].casefold(),
                        "weight":float(item["inverse_probability_weight"]),
                        "truth_source":provenance})
    agreement=kappa(all_agreement_A,all_agreement_B)
    complete=(bool(key) and len(pending)==0 and len(results)==len(key) and len(all_agreement_A)==len(key))
    report={"expected_records":len(key),"paired_review_decisions":len(all_agreement_A),
        "independently_resolved":sum(x["truth_source"]=="independent_reviewer_agreement" for x in results),
        "adjudicated":sum(x["truth_source"]=="third_party_adjudication" for x in results),
        "unresolved":len(pending),"pending_examples":pending[:30],
        "inter_review_agreement":agreement,"validation_ready":complete}
    if complete:
        c=weighted_confusion(results)
        report["weighted_confusion"]=c
        report["weighted_rates"]=rates(c)
        report["stratum_results"]={stratum:{"sample_size":len([x for x in results if x["stratum"]==stratum]),
                  "confusion":weighted_confusion([x for x in results if x["stratum"]==stratum])}
            for stratum in sorted({x["stratum"] for x in results})}
        report["stratified_bootstrap_95pct_intervals"]=bootstrap_confusion(results)
        report["threshold_check"]={
            "recall_point_ge_0_95":report["weighted_rates"]["recall"] is not None and report["weighted_rates"]["recall"]>=.95,
            "precision_point_ge_0_90":report["weighted_rates"]["precision"] is not None and report["weighted_rates"]["precision"]>=.90,
        }
    return report

def reference_section(rows,corpus,scope="legacy_wireless"):
    references=[x for x in rows if (x.get("doi") or x.get("pmid") or "").strip()]
    dataset_dois={normalize_doi(x.get("doi")) for x in corpus if x.get("doi")}
    dataset_pmids={str(x.get("pmid") or "").strip() for x in corpus if x.get("pmid")}
    result={"reference_rows_submitted":len(references),"modalities":{},"status":"NOT_VALIDATED"}
    unknown=[x for x in references if x.get("modality") not in SCOPES[scope]]
    result["unknown_modality_rows"]=len(unknown)
    result["validation_scope"]=scope
    for m in SCOPES[scope]:
        matches=[x for x in references if (x.get("modality") or "")==m]
        eligible=[]
        invalid=0
        seen_dois=set();seen_pmids=set()
        for x in matches:
            d=normalize_doi(x.get("doi"));p=(x.get("pmid") or "").strip()
            if d in KNOWN_SENTINELS or (d and d in seen_dois) or (p and p in seen_pmids):invalid+=1;continue
            if d:seen_dois.add(d)
            if p:seen_pmids.add(p)
            if (x.get("independent_eligibility_include_exclude_uncertain") or "").lower()!="include":continue
            if (x.get("source_before_atlas_lookup") or "").lower() not in {"yes","true","1"}:
                invalid+=1;continue
            if (x.get("reviewer_confirmed_original_yes_no") or "").lower()!="yes":
                invalid+=1;continue
            if (not x.get("verification_url") or not x.get("independent_discovery_method")
                    or not x.get("reviewer_id") or not valid_date(x.get("review_date"))
                    or not x.get("full_text_page_or_quotation")
                    or x.get("evidence_tier_T0_T1_T2_T3") not in {"T2", "T3"}):
                invalid+=1;continue
            eligible.append(x)
        found=sum(normalize_doi(x.get("doi")) in dataset_dois or str(x.get("pmid") or "").strip() in dataset_pmids for x in eligible)
        result["modalities"][m]={"total_reference_rows":len(matches),"independent_verified_eligible":len(eligible),
            "known_sentinels_or_ineligible":invalid,"retrieved":found,
            "recall":round(found/len(eligible),4) if eligible else None,
            "wilson_95pct_ci":wilson(found,len(eligible)),
            "minimum_30_met":len(eligible)>=30,
            "recall_point_ge_0_95":found/len(eligible)>=.95 if eligible else False}
    if not unknown and all(v["minimum_30_met"] for v in result["modalities"].values()) and not any(v["known_sentinels_or_ineligible"] for v in result["modalities"].values()):
        result["status"]="EVALUATED_WITH_INDEPENDENT_REFERENCE_DATA"
    return result

def author_section(rows):
    valid=[x for x in rows if (x.get("classification_correct_wrong_person_split_ambiguous_unverifiable") or "").strip()]
    codes=collections.Counter(x["classification_correct_wrong_person_split_ambiguous_unverifiable"].strip().lower() for x in valid)
    if any(k not in {"correct","wrong_person","split","ambiguous","unverifiable"} for k in codes):
        raise ValueError("Unknown author audit label")
    checked=codes["correct"]+codes["wrong_person"]+codes["split"]
    return {"submitted":len(valid),"verified_n":checked,"codes":dict(codes),
       "accuracy":round(codes["correct"]/checked,4) if checked else None,
       "wilson_95pct_ci":wilson(codes["correct"],checked),
       "unresolved":codes["ambiguous"]+codes["unverifiable"],
       "not_yet_validated":checked<100 or codes["ambiguous"]+codes["unverifiable"]>0
           or (codes["correct"]/checked < .99 if checked else True)
           or any(not x.get("publisher_byline_url") or not x.get("independent_reviewer")
                  or not x.get("orcid_crosscheck_url") or not x.get("institution_evidence") for x in valid)}

def evaluation_status(review, reference, authors):
    if not review["validation_ready"]:
        return "NOT_STARTED_OR_INCOMPLETE"
    if (not all(review.get("threshold_check", {}).get(k, False) for k in
                ("recall_point_ge_0_95", "precision_point_ge_0_90"))
            or reference["status"] != "EVALUATED_WITH_INDEPENDENT_REFERENCE_DATA"
            or not all(x["recall_point_ge_0_95"] for x in reference["modalities"].values())
            or authors["not_yet_validated"]):
        return "PILOT_THRESHOLDS_NOT_MET"
    return "PILOT_THRESHOLDS_MET_SIGNOFF_PENDING"

def main():
    parser=argparse.ArgumentParser()
    for k in ("reviewer-a","reviewer-b","adjudicator-key","adjudications","reference-set",
              "author-audit","candidates","output"):parser.add_argument("--"+k,required=True)
    parser.add_argument("--packet-manifest", required=True)
    parser.add_argument("--scope", choices=tuple(SCOPES), default="legacy_wireless")
    a=parser.parse_args()
    manifest=json.loads(pathlib.Path(a.packet_manifest).read_text())
    if manifest.get("validation_scope", "legacy_wireless") != a.scope:
        raise ValueError("Packet manifest scope mismatch")
    if hashlib.sha256(pathlib.Path(a.candidates).read_bytes()).hexdigest() != manifest.get("frozen_source_sha256"):
        raise ValueError("Frozen source checksum mismatch")
    key_path=pathlib.Path(a.adjudicator_key)
    if hashlib.sha256(key_path.read_bytes()).hexdigest() != manifest.get("files_sha256", {}).get(key_path.name):
        raise ValueError("Adjudicator key checksum mismatch")
    source=json.loads(pathlib.Path(a.candidates).read_text(encoding="utf-8"))["records"]
    review=review_section(read_csv(a.reviewer_a),read_csv(a.reviewer_b),
                          read_csv(a.adjudications),read_csv(a.adjudicator_key),a.scope)
    ref=reference_section(read_csv(a.reference_set),source,a.scope)
    authors=author_section(read_csv(a.author_audit))
    result={"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "validation_scope":a.scope,
        "status":evaluation_status(review,ref,authors),
        "scientific_release_permitted":False,
        "review":review,"reference_recall":ref,"author_identity":authors,
        "remaining_release_gates":["search saturation and source coverage", "ranked-cohort identity reconciliation",
            "external normalization and rank uncertainty", "independent scientific sign-off"],
        "limitations":["Software checks supplied evidence fields; it cannot certify reviewer independence or truth.",
            "Full-text reviews and independent reference selection require real reviewers.",
            "Intervals are conditional on the sampled frame; missing literature is not bounded by this pilot.",
            "Passing pilot thresholds never authorizes validated international rankings."]}
    out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("Screening",review["paired_review_decisions"],"/",review["expected_records"],
          "adjudicated",review["adjudicated"],"pending",review["unresolved"])
    print("Reference set",ref["status"],"Author audit verified:",authors["verified_n"])
    print("STATUS:",result["status"])
if __name__=="__main__":main()

