#!/usr/bin/env python3
"""Scenario rank stability for the frozen, *not independently screened* Atlas.

Reports conditional stability under selected weightings and leave-one-paper-out.
Stable exploratory ranks do NOT validate bibliographic coverage or true impact.
"""
import argparse,collections,json,math,pathlib,statistics,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"methods"))
from build_provisional_rankings import score as provisional_score
SCENARIOS={
 "published_provisional":{"citation_impact":.35,"relevant_output":.25,
     "authorship_leadership":.20,"translational_indicators":.10,"sustained_activity":.10},
 "citation_emphasis":{"citation_impact":.55,"relevant_output":.15,
     "authorship_leadership":.10,"translational_indicators":.10,"sustained_activity":.10},
 "output_emphasis":{"citation_impact":.25,"relevant_output":.40,
     "authorship_leadership":.20,"translational_indicators":.10,"sustained_activity":.05},
 "no_translation_proxy":{"citation_impact":.40,"relevant_output":.30,
     "authorship_leadership":.20,"translational_indicators":.00,"sustained_activity":.10},
 "no_author_position_proxy":{"citation_impact":.45,"relevant_output":.35,
     "authorship_leadership":.00,"translational_indicators":.10,"sustained_activity":.10},
}
def weighted_score(row,weights):
    return sum(float(row["components"].get(k,0))*value for k,value in weights.items())
def score_ranks(rows,weights):
    scores={row["openalex_author_id"] or ("orcid:"+row["orcid"]):weighted_score(row,weights) for row in rows}
    result=sorted(rows,key=lambda row:(-scores[row["openalex_author_id"] or ("orcid:"+row["orcid"])],
                                     -row["publication_count"],row["name"].casefold()))
    return {row["openalex_author_id"] or ("orcid:"+row["orcid"]):i+1 for i,row in enumerate(result)}
def spearman(a,b):
    common=set(a)&set(b)
    if len(common)<2:return None
    n=len(common)
    means=sum(a[k] for k in common)/n,sum(b[k] for k in common)/n
    num=sum((a[k]-means[0])*(b[k]-means[1]) for k in common)
    den=math.sqrt(sum((a[k]-means[0])**2 for k in common)*sum((b[k]-means[1])**2 for k in common))
    return round(num/den,4) if den else None
def jaccard(a,b,k=10):
    a={x for x,r in a.items() if r<=k}
    b={x for x,r in b.items() if r<=k}
    return round(len(a&b)/len(a|b),4) if a|b else None
def loo_rank_change(row,rows):
    # Conditional on published candidate set, study removal cannot simulate missed works.
    papers=row.get("papers") or []
    if len(papers)<2:return None
    best=[]
    original=row["score"]
    for omit in range(len(papers)):
        score,_=provisional_score(papers[:omit]+papers[omit+1:])
        best.append(1+sum(float(other["score"])>score for other in rows if other is not row))
    return {"min":min(best),"max":max(best),"num_removals":len(best)}
def evaluate(data,leave_one_max=50):
    report={"source_methods_version":data.get("methods_version"),
      "validity_status":"EXPLORATORY_CONDITIONAL_STABILITY_ONLY",
      "warning":"No evidence screening, author verification or external field-normalization is performed here.",
      "scenarios":SCENARIOS,"modalities":{}}
    for category,rows in data["rankings"].items():
        if not rows:continue
        base=score_ranks(rows,SCENARIOS["published_provisional"])
        models={name:score_ranks(rows,weights) for name,weights in SCENARIOS.items()}
        comparisons={name:{"spearman_rho":spearman(base,ranks),
                     "top_10_jaccard":jaccard(base,ranks,min(10,len(rows))),
                     "n_researchers":len(rows)}
                for name,ranks in models.items()}
        row_reports=[]
        for i,row in enumerate(rows):
            ident=row["openalex_author_id"] or ("orcid:"+row["orcid"])
            ranks={name:vals[ident] for name,vals in models.items()}
            result={"name":row["name"],"openalex_author_id":row["openalex_author_id"],
                "orcid":row["orcid"],"institution":row["institution"],
                "publication_count":row["publication_count"],
                "baseline_rank":base[ident],
                "rank_by_scenario":ranks,"scenario_rank_min":min(ranks.values()),
                "scenario_rank_max":max(ranks.values()),
                "rank_span":max(ranks.values())-min(ranks.values())}
            if i<leave_one_max or category=="Electrochemical":
                result["leave_one_paper_out"]=loo_rank_change(row,rows)
            row_reports.append(result)
        report["modalities"][category]={"researchers":len(rows),"comparison":comparisons,
                                  "researcher_scenarios":row_reports,
                                  "rank_change_gt_10":sum(r["rank_span"]>10 for r in row_reports)}
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--rankings",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    data=json.loads(pathlib.Path(a.rankings).read_text(encoding="utf-8"))
    report=evaluate(data)
    out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    for k,v in report["modalities"].items():
        print(k,"n",v["researchers"],"scenario rank span >10",v["rank_change_gt_10"],
              "citation-heavy top10 Jaccard",v["comparison"]["citation_emphasis"]["top_10_jaccard"])
    print("VALIDITY:",report["validity_status"])
if __name__=="__main__":main()
