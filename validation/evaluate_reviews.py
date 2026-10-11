#!/usr/bin/env python3
"""Evaluate independent dual screening only after reviews and adjudication exist.

Blank reviewer templates generate a "NOT_STARTED" readiness report and NO
accuracy estimates. Machine labels are read only after reviewers lock decisions.
"""
import argparse,collections,csv,datetime,json,math,pathlib,random,statistics,sys
from urllib.parse import urlparse

VALID={"include","exclude","uncertain"}
MODALITIES=("Electrochemical","Ultrasound","Magnetic","Optical","Radiofrequency","Hybrid")
KNOWN_SENTINELS={"10.1038/s41565-023-01496-y","10.1002/advs.202516561",
 "10.1021/acsomega.1c03547","10.1038/s41598-024-71236-2",
 "10.1021/acs.langmuir.6c00755","10.1038/s43246-025-00750-1",
 "10.1038/s41528-019-0060-6","10.1039/d5lc00708a","10.1039/d3bm01946b"}
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

def review_section(a,b,adjud,key):
    key_by_id={x["record_id"]:x for x in key}
    if len(key_by_id)!=len(key):raise ValueError("Duplicate record IDs in adjudicator key")
    rev={}
    for n,rows in (("A",a),("B",b)):
        if len({x["record_id"] for x in rows})!=len(rows):raise ValueError("Duplicate review record")
        if {x["record_id"] for x in rows}!={x["record_id"] for x in key}:raise ValueError("Review IDs do not match key")
        rev[n]={x["record_id"]:x for x in rows}
    adj={x["record_id"]:x for x in adjud}
    results=[]
    pending=[]
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
        if not ca or not cb or ca==cb:
            pending.append({"record_id":rid,"reason":"two distinct reviewer codes required"});continue
        all_agreement_A.append(da);all_agreement_B.append(db)
        if da==db and da!="uncertain":
            final=da
            provenance="independent_reviewer_agreement"
        else:
            row=adj.get(rid,{})
            final=(row.get("final_eligibility_include_exclude_uncertain") or "").strip().casefold()
            if final not in VALID or not (row.get("adjudicator_code") or "").strip() or not (row.get("evidence_source_url") or "").strip():
                pending.append({"record_id":rid,"reason":"third-party adjudication and source link required"});continue
            provenance="third_party_adjudication"
        if final=="uncertain":
            pending.append({"record_id":rid,"reason":"unresolved after adjudication"});continue
        if (item.get("machine_eligible_electrochemical") or "").casefold() not in {"include","exclude"}:
            raise ValueError("Missing machine label for "+rid)
        results.append({"record_id":rid,"stratum":item["frame_stratum"],"truth":final,
                        "machine":item["machine_eligible_electrochemical"].casefold(),
                        "weight":float(item["inverse_probability_weight"]),
                        "truth_source":provenance})
    agreement=kappa(all_agreement_A,all_agreement_B)
    complete=(len(pending)==0 and len(results)==len(key) and len(all_agreement_A)==len(key))
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

def reference_section(rows,corpus):
    references=[x for x in rows if (x.get("doi") or x.get("pmid") or "").strip()]
    dataset_dois={normalize_doi(x.get("doi")) for x in corpus if x.get("doi")}
    dataset_pmids={str(x.get("pmid") or "").strip() for x in corpus if x.get("pmid")}
    result={"reference_rows_submitted":len(references),"modalities":{},"status":"NOT_VALIDATED"}
    for m in MODALITIES:
        matches=[x for x in references if (x.get("modality") or "")==m]
        eligible=[]
        invalid=0
        for x in matches:
            d=normalize_doi(x.get("doi"));p=(x.get("pmid") or "").strip()
            if d in KNOWN_SENTINELS:invalid+=1;continue
            if (x.get("independent_eligibility_include_exclude_uncertain") or "").lower()!="include":continue
            if (x.get("source_before_atlas_lookup") or "").lower() not in {"yes","true","1"}:
                invalid+=1;continue
            if (x.get("reviewer_confirmed_original_yes_no") or "").lower()!="yes":
                invalid+=1;continue
            if not x.get("verification_url") or not x.get("independent_discovery_method"):
                invalid+=1;continue
            eligible.append(x)
        found=sum(normalize_doi(x.get("doi")) in dataset_dois or str(x.get("pmid") or "").strip() in dataset_pmids for x in eligible)
        result["modalities"][m]={"total_reference_rows":len(matches),"independent_verified_eligible":len(eligible),
            "known_sentinels_or_ineligible":invalid,"retrieved":found,
            "recall":round(found/len(eligible),4) if eligible else None,
            "wilson_95pct_ci":wilson(found,len(eligible)),
            "minimum_30_met":len(eligible)>=30,
            "recall_point_ge_0_95":found/len(eligible)>=.95 if eligible else False}
    if all(v["minimum_30_met"] for v in result["modalities"].values()) and not any(v["known_sentinels_or_ineligible"] for v in result["modalities"].values()):
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
       "not_yet_validated":checked<100 or codes["ambiguous"]+codes["unverifiable"]>0}

def main():
    parser=argparse.ArgumentParser()
    for k in ("reviewer-a","reviewer-b","adjudicator-key","adjudications","reference-set",
              "author-audit","candidates","output"):parser.add_argument("--"+k,required=True)
    a=parser.parse_args()
    source=json.loads(pathlib.Path(a.candidates).read_text(encoding="utf-8"))["records"]
    review=review_section(read_csv(a.reviewer_a),read_csv(a.reviewer_b),
                          read_csv(a.adjudications),read_csv(a.adjudicator_key))
    ref=reference_section(read_csv(a.reference_set),source)
    authors=author_section(read_csv(a.author_audit))
    result={"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status":"VALIDATION_RESULTS_AVAILABLE" if review["validation_ready"] else "NOT_STARTED_OR_INCOMPLETE",
        "review":review,"reference_recall":ref,"author_identity":authors,
        "limitations":["The same publications were not independently full-text reviewed by this software.",
          "Blinded reviewer decisions and independent publisher verification must be supplied by real reviewers.",
          "Stratified bootstrap intervals estimate sampling variation conditional on the constructed sampling frame, not missed literature outside that frame.",
          "A complete pilot does not constitute a validated international ranking."]}
    if result["status"]=="VALIDATION_RESULTS_AVAILABLE" and (ref["status"]!="EVALUATED_WITH_INDEPENDENT_REFERENCE_DATA" or authors["not_yet_validated"]):
        result["status"]="PILOT_ONLY_NOT_WORLD_RANKING_VALIDATED"
    out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("Screening",review["paired_review_decisions"],"/",review["expected_records"],
          "adjudicated",review["adjudicated"],"pending",review["unresolved"])
    print("Reference set",ref["status"],"Author audit verified:",authors["verified_n"])
    print("STATUS:",result["status"])
if __name__=="__main__":main()
