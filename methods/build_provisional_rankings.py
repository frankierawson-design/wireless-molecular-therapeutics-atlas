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
 "Optical":r"\b(?:photodynamic|photothermal|photopharmacolog\w*|photoactivat\w*|photoswitch\w*|photocag\w*|light.trigger\w*|light.activated|photovoltaic.{0,55}ion.pump\w*|near.infrared.(?:activat|trigger|respons)|NIR.(?:activat|trigger|respons))\b",
 "Radiofrequency":r"\b(?:radiofrequency|radio.frequency|RF.trigger\w*|RF.activat\w*|microwave.trigger\w*)\b",
 "TTFields":r"\b(?:tumou?r[ -]?treating[ -]?fields?|ttfields?|alternating[ -]electric[ -]fields?.{0,70}(?:cancer|tumou?r|glioblastoma)|novottf|optune)\b",
 "Electrochemotherapy":r"\b(?:electrochemotherap\w*|electropermeabili[sz]ation.{0,55}(?:bleomycin|cisplatin|tumou?r|cancer)|electrochemotherapeutic)\b",
 "Electroporation":r"\b(?:irreversible[ -]electroporat\w*|reversible[ -]electroporat\w*|high[ -]frequency[ -]irreversible[ -]electroporat\w*|h[ -]?fire|pulsed[ -]field.{0,45}ablat\w*|nanosecond[ -]pulsed[ -]electric[ -]fields?|electroporation[ -]gene[ -]transfer|electrotransfer|electroporation.{0,35}(?:therap\w*|ablat\w*|drug|cancer|tumou?r))\b",
 "Neuromodulation":r"\b(?:deep[ -]brain[ -]stimulation|vagus[ -]nerve[ -]stimulation|spinal[ -]cord[ -]stimulation|transcranial[ -](?:direct[ -]current|alternating[ -]current|electrical)[ -]stimulation|t[ -]?dcs|t[ -]?acs|peripheral[ -]nerve[ -]stimulation|transcutaneous[ -]electrical[ -]nerve[ -]stimulation|electrical[ -]direct[ -]current[ -]therap\w*|electrical[ -]neuromodulat\w*|neurostimulat\w*|nerve[ -]stimulation)\b",
 "Electrical Stimulation":r"\b(?:(?:electrical|electric[ -]field|bioelectric)[ -]stimulation.{0,90}(?:wound\w*|cell\w*|tissue\w*|bone|regenerat\w*|muscle\w*|heal\w*|rehabilitat\w*|cancer)|(?:wound\w*|cell\w*|tissue\w*|bone|regenerat\w*|muscle\w*|heal\w*|rehabilitat\w*)[a-z -]{0,90}(?:electrical|electric[ -]field)[ -]stimulation|electrical[ -]muscle[ -]stimulation|electric[ -]field[ -]guided[ -]cell[ -]migration)\b",
 "Electrochemical":r"\b(?:wireless.bipolar|bipolar.electrochem\w*|bipolar.electrod\w*|bipolar.electroactive|bipolar.electrostimul\w*|wireless.cell.stimulation|wirefree.electrochem\w*|wire.free.electrochem\w*|electrochemical.drug|electrochemical.pump|electrochemical.nitric.oxide|electroceutical\w*|electro.pharmaceut\w*|wireless.electrical|wireless.bioelectronic|bioelectronic.modulation|electrochemical.therapy|electron.transfer.therapy|electrochemical.release|electrochemical.generation|organic.electronic.ion.pump\w*|iontronic.click.to.release|electrically.controlled.drug|electrochemically.controlled.release|wirefree.{0,50}(?:drug|release|pedot|polymer|electrode)|(?:electroactive|conducting.polymer).{0,60}(?:drug.delivery|drug.release|neurostimulation|nerve.regeneration|cell.stimulation))\b"
}
THERAPY=r"\b(?:therap\w*|treat\w*|drug\w*|deliver\w*|release|cancer|tumou?r\w*|glioblastoma|melanoma|neuron\w*|nerve|neurostimulat\w*|regenerat\w*|heal\w*|apoptos\w*|ablat\w*|immunotherap\w*|pain|wound|disease|cell.death|chemotherap\w*|blood.brain.barrier|brain.stimulation|parkinson\w*|epilepsy|depression|atrial.fibrillation|electrochemotherap\w*|electroporat\w*|ablat\w*|neuromodulat\w*|cell.modulat\w*|cell.stimulation|cell.differentiation|neuron\w*.stimulation|neurite\w*|neural.differentiation)\b"
REVIEW=r"\b(?:review|overview|bibliometric|meta.analysis|perspective|scientometric|recent.advances|current.progress|state.of.the.art|prospects|research.progress|roadmap|survey|abstract \d+)\b"
DIAGNOSTIC=r"\b(?:biosens\w*|diagnos\w*|detect\w*|monitor\w*|sensor|aptasens\w*)\b"
TRANSLATION=r"\b(?:in.vivo|animal|mice|mouse|xenograft|patient|clinical|porcine|human.trial|wound.closure|tumo\w*.regression)\b"
REVIEW_ABSTRACT=r"\b(?:this review|in this review|here we review|review of current|the current review|we summariz|this perspective)\b"

# Additional *strong* abstract evidence is used only when a paper's title
# contains a matching electrical/electroactive device or delivery term.
ELECTRO_ABSTRACT=r"\b(?:bipolar.electrochem\w*|wirefree.electrochem\w*|wire.less.electrochemical|organic.electronic.ion.pump\w*|wirelessly.controlled.electrochem\w*|wirefree.{0,55}(?:bipolar|drug.release|conducting.polymer)|photovoltaic.{0,90}ion.pump|electrochemically.driven.delivery|redox.controlled.release|electron.transfer.mediated.cell)\b"
ELECTRO_PLATFORM_TITLE=r"\b(?:wirefree|wire.less|wirelessly|wireless|remote|ion.pump|iontronic|electroactive|conducting.polymer|pedot|electrochemical|electroresponsive|bioelectronic|nanoparticle|molecular|drug.delivery|drug.release|photovoltaic)\b"
ELECTRO_DELIVERY=r"\b(?:drug.release|drug.delivery|on.demand.drug|molecular.delivery|biomolecular.delivery|(?:release.{0,35}(?:drug|molecule))|(?:delivery.{0,25}drug)|neurotransmitter|acetylcholine|ion.pump\w*|iontronic|release.of.molecules|pharmacologically.active)\b"
ELECTRO_REMOTE=r"\b(?:wireless|wirefree|wire.free|unwired|remote\w*|contactless|battery.free|near.field.communication|NFC|photovoltaic|photo.powered|light.driven|electromagnetic|ultrasonic|acoustic|inductively.powered|externally.generated.electric.field)\b"
ELECTRO_BIO=r"\b(?:cancer|glioblastoma|neuron|nerve|wound|cell|biological|apoptos|tumou?r|therapy|disease|nerve.growth|antitumou?r)\b"

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
        if re.match(r"^10\.(?:1101/|26434/chemrxiv|2139/ssrn|48550/arxiv|20944/preprints|21203/rs)",str(r.get("doi") or ""),re.I):
            excluded["preprint_not_in_primary_ranking"]+=1;continue
        if re.match(r"^10\.(?:17615/|25148/etd|3929/)",str(r.get("doi") or ""),re.I):
            excluded["repository_record_requires_original_article"]+=1;continue
        # Some indexed supplement entries have their own DOIs but are
        # meeting abstracts, not independent peer-reviewed full articles.
        conference_abstract_dois={"10.1093/neuonc/noaf185.039"}
        if str(r.get("doi") or "").casefold() in conference_abstract_dois:
            excluded["conference_abstract_not_full_paper"]+=1;continue
        # Document-type guard. A dissertation, book, meeting abstract or
        # standalone review is not a peer-reviewed original research article,
        # even when title keywords and OpenAlex citations look promising.
        work_type=str(r.get("openalex_work_type") or "").strip().casefold()
        nonoriginal_types={"dissertation","conference-paper","conference-abstract",
                           "review","book","book-chapter","preprint","editorial",
                           "erratum","report","peer-review","paratext","retraction"}
        if work_type in nonoriginal_types:
            excluded["nonoriginal_openalex_work_type_"+work_type]+=1;continue
        # A record lacking BOTH a DOI and PMID cannot currently substantiate
        # peer-reviewed original-paper status; retain it for manual review.
        if not r.get("doi") and not r.get("pmid"):
            excluded["unverified_work_without_doi_or_pmid"]+=1;continue
        pubtypes="; ".join(str(x) for x in (r.get("publication_types") or []))
        curated_review_dois={"10.1039/d3bm01946b", "10.1016/j.elecom.2024.107832", "10.1016/j.coelec.2023.101297"}
        # Data-in-Brief supporting datasets must not be double-counted as
        # separate original biological interventions.
        if matches(r"^data on\b", title) or matches(r"\b(?:data article|data descriptor)\b",pubtypes):
            excluded["supporting_data_article"]+=1;continue
        if (matches(REVIEW,title)
            or matches(REVIEW_ABSTRACT,r.get("abstract") or "")
            or matches(r"\b(?:review|meta.analysis|editorial|perspective)\b",pubtypes)
            or str(r.get("doi") or "").casefold() in curated_review_dois):
            excluded["possible_review_or_nonoriginal"]+=1;continue
        abstract=r.get("abstract") or ""
        mods=[m for m,p in MODALITIES.items() if matches(p,title)]
        # Abstract-based recall only for titles that already identify a plausible
        # electroactive platform: broad unrelated review background is not enough.
        if "Electrochemical" not in mods and matches(ELECTRO_PLATFORM_TITLE,title) and matches(ELECTRO_ABSTRACT,abstract):
            if matches(ELECTRO_REMOTE,title+" "+abstract) and (matches(ELECTRO_DELIVERY,title+" "+abstract) or matches(ELECTRO_BIO,title)):
                mods.append("Electrochemical")
        if not mods:excluded["no_explicit_remote_energy_in_title"]+=1;continue
        # For molecular delivery platforms the mechanism can be in the abstract
        # even when the title lacks a disease or drug keyword.
        therapy_title=matches(THERAPY,title)
        platform_electro=("Electrochemical" in mods and
                         matches(ELECTRO_PLATFORM_TITLE,title) and
                         matches(ELECTRO_DELIVERY,title+" "+abstract) and
                         matches(ELECTRO_REMOTE,title+" "+abstract))
        # These established clinical treatment classes can use wired devices.
        clinical_electrical=bool(set(mods)&{"TTFields","Electrochemotherapy","Electroporation","Neuromodulation","Electrical Stimulation"})
        if not therapy_title and not platform_electro and not clinical_electrical:
            excluded["no_therapeutic_endpoint_in_title"]+=1;continue
        # A wired electrochemical delivery device is not, by itself, a
        # wireless molecular-therapeutic system. Bipolar electrochemistry
        # inherently offers wireless polarisation when remotely driven.
        if "Electrochemical" in mods and not (
            matches(ELECTRO_REMOTE,title+" "+abstract)
            or matches(r"\b(?:bipolar.electrochem\w*|wireless.bipolar|unwired.bipolar)\b",title+" "+abstract)
        ):
            mods.remove("Electrochemical")
        if not mods:
            excluded["no_remote_electrochemical_actuation"]+=1;continue
        if matches(DIAGNOSTIC,title) and not matches(r"\b(?:release|drug.delivery|therap\w*|treat\w*|neurostimulat\w*|wound.healing|cancer.therap\w*)\b",title):
            excluded["diagnostics_only"]+=1;continue
        if "Radiofrequency" in mods and matches(r"\b(?:atrial.fibrillation|cardiac|catheter|arrhythmia)\b",title) and not matches(r"\b(?:drug|nanoparticle|delivery|molecular)\b",title):
            mods.remove("Radiofrequency")
        if not mods:excluded["nonmolecular_radiofrequency"]+=1;continue
        # Multiple electric-treatment labels do not imply distinct energy modalities.
        energy_family={"Ultrasound":"acoustic","Magnetic":"magnetic",
                       "Optical":"optical","Radiofrequency":"radiofrequency",
                       "Electrochemical":"electrical","TTFields":"electrical",
                       "Electrochemotherapy":"electrical","Electroporation":"electrical",
                       "Neuromodulation":"electrical","Electrical Stimulation":"electrical"}
        if len({energy_family[m] for m in mods if m in energy_family})>=2:
            mods.append("Hybrid")
        if not any(a.get("openalex_author_id") or norm_orcid(a.get("orcid")) for a in (r.get("authors") or [])):
            excluded["author_identifier_missing"]+=1;continue
        r2=dict(r);r2["year"]=year;r2["modalities"]=mods
        if matches(r"\b(?:apoptos\w*|cancer.cell.death|wound.heal\w*|tumou?r.regress\w*|neur\w*.regenerat\w*|cell.stimulation|clinical.treat\w*|cancer.therap\w*)\b",title):
            tier="therapeutic_biological_candidate"
        elif matches(ELECTRO_DELIVERY,title+" "+abstract):
            tier="molecular_delivery_platform_candidate"
        else:
            tier="therapeutic_mechanism_candidate"
        r2["evidence_tier"]=tier
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

def norm_orcid(value):
    m=re.search(r"\b\d{4}-\d{4}-\d{4}-[\dX]{4}\b",str(value or ""),re.I)
    return m.group(0).upper() if m else ""

def norm_aid(value):
    m=re.search(r"(?:openalex\.org/)?(A\d+)\b",str(value or ""),re.I)
    return "https://openalex.org/"+m.group(1).upper() if m else ""

def identity_map(records):
    # ORCID-only bylines can be linked to a unique OpenAlex identity when
    # another record supplies both stable identifiers. Never merge by names.
    seen=collections.defaultdict(set)
    for r in records:
        for a in (r.get("authors") or []):
            orcid=norm_orcid(a.get("orcid"))
            aid=norm_aid(a.get("openalex_author_id"))
            if orcid and aid:seen[orcid].add(aid)
    return {k:next(iter(v)) for k,v in seen.items() if len(v)==1}, sum(len(v)>1 for v in seen.values())

def author_key(a,links):
    aid=norm_aid(a.get("openalex_author_id"))
    orcid=norm_orcid(a.get("orcid"))
    # A paper-level publisher-corroborated ORCID is a stronger identity
    # key than a fragmented OpenAlex author ID *for this specific paper*.
    # This does not merge generic name matches or unverified ORCID collisions.
    if orcid and norm_orcid(a.get("verified_orcid_from_publication"))==orcid:
        return "https://orcid.org/"+orcid
    if aid:return aid
    if orcid:return links.get(orcid) or "https://orcid.org/"+orcid
    return ""

def rank_institution(a):
    # This is a dated affiliation on the cited paper, NOT guaranteed current.
    return [{"name":i.get("name",""),"id":i.get("id","")}
            for i in (a.get("institutions") or [])
            if isinstance(i,dict) and i.get("name")]

def institution_lookup(all_records,links):
    # Use metadata from *all* harvested works, even where the paper is not
    # eligible for scoring, so affiliated names are not truncated by filters.
    observed=collections.defaultdict(list)
    for r in all_records:
        try: year=int(r.get("year") or 0)
        except (ValueError,TypeError):year=0
        for a in (r.get("authors") or []):
            key=author_key(a,links)
            if not key:continue
            for inst in rank_institution(a):
                observed[key].append((year,inst["name"],inst["id"],r.get("openalex_id") or "",r.get("doi") or ""))
    out={}
    for key,values in observed.items():
        byname={}
        for year,name,iid,work,doi in values:
            ident=iid or name.casefold()
            state=byname.setdefault(ident,{"name":name,"id":iid,"last_year":year,"count":0,"work":work,"doi":doi})
            state["count"]+=1
            if year>=state["last_year"]:
                state.update({"name":name,"id":iid,"last_year":year,"work":work,"doi":doi})
        # Most recent documented affiliation, with repeated entries as tie-break.
        out[key]=sorted(byname.values(),key=lambda z:(-z["last_year"],-z["count"],z["name"].casefold()))
    return out

def normalized_work_title(title):
    """Conservative exact-normalized title, for duplicate manifestations per author."""
    return re.sub(r"[^a-z0-9]+","",str(title or "").casefold())

def evidence_priority(paper):
    """Prefer publisher article to undated record, then stronger citation evidence."""
    paper_type=(paper.get("openalex_work_type") or "").casefold()
    doi=str(paper.get("doi") or "").casefold()
    journal_doi=bool(doi and not re.match(
        r"^10\.(?:17615/|25148/etd|3929/|48550/|2139/ssrn|1101/|21203/rs)",doi))
    return (
        int(paper_type=="article"),
        int(journal_doi),
        int(bool(doi)),
        int(paper.get("citations") or 0),
        int(paper.get("year") or 0),
    )

def make_ranks(included, all_records):
    links,conflicts=identity_map(all_records)
    institution_by_author=institution_lookup(all_records,links)
    cohorts=collections.defaultdict(list)
    for r in included:
        for mod in r["modalities"]:cohorts[(r["year"],mod)].append(r["citations_openalex"])
    authors=collections.defaultdict(lambda:{"name":"","orcid":"","papers":{},"identity_sources":set(),"duplicates_suppressed":0})
    for r in included:
        mods=r["modalities"]
        percentile=round(sum(cohort_percentile(r["citations_openalex"],r["year"],m,cohorts) for m in mods)/len(mods),2)
        a_list=r.get("authors") or []
        for i,a in enumerate(a_list):
            key=author_key(a,links)
            if not key:continue
            person=authors[key]
            name=a.get("name") or ""
            # A complete institutional author name is more informative than initials.
            if len(name)>len(person["name"]):person["name"]=name
            person["orcid"]=norm_orcid(a.get("orcid")) or person["orcid"]
            person["identity_sources"].add("Publisher-corroborated work ORCID" if a.get("verified_orcid_from_publication") else "OpenAlex" if norm_aid(a.get("openalex_author_id")) else "ORCID")
            position=a.get("position") or ("first" if i==0 else "last" if i==len(a_list)-1 else "middle")
            evidence={"title":r["title"],"doi":r.get("doi"),"url":r.get("openalex_id"),"year":r["year"],
                      "citations":r["citations_openalex"],"citation_percentile":percentile,
                      "modalities":mods,"authorship":position,"evidence_tier":r.get("evidence_tier","unclassified"),
                      "institutions":rank_institution(a),
                      "openalex_work_type":r.get("openalex_work_type") or "",
                      "document_type_status":"metadata_article" if str(r.get("openalex_work_type") or "").casefold()=="article" else "not_confirmed"}
            k=normalized_work_title(r.get("title")) or r.get("doi") or r.get("openalex_id")
            # Same author + same normalized title is one research work, even
            # when a repository copy has another DOI or publication year.
            # The source links remain in the corpus for screening.
            old=person["papers"].get(k)
            if old:
                person["duplicates_suppressed"]+=1
                if evidence_priority(evidence)>evidence_priority(old):
                    person["papers"][k]=evidence
            else:
                person["papers"][k]=evidence
    ranks={}
    for group in ["Overall",*MODALITIES,"Hybrid"]:
        rows=[]
        minimum=3 if group=="Overall" else 2
        for aid,a in authors.items():
            papers=[p for p in a["papers"].values() if group=="Overall" or group in p["modalities"]]
            if len(papers)<minimum:continue
            total,parts=score(papers)
            papers.sort(key=lambda p:(p["citations"],p["year"]),reverse=True)
            insts=institution_by_author.get(aid,[])
            current=insts[0] if insts else None
            rows.append({"name":a["name"],"openalex_author_id":aid if aid.startswith("https://openalex.org/") else "",
                         "orcid":a["orcid"], "identity_method":", ".join(sorted(a["identity_sources"])),
                         "institution":current["name"] if current else "Not available",
                         "institution_year":current["last_year"] if current else None,
                         "institution_source_work":current["work"] if current else "",
                         "institution_record_source":"OpenAlex work-level affiliation" if current else "Not verified",
                         "institutions":insts[:5],
                         "score":total,"publication_count":len(papers),
                         "indexed_citations":sum(p["citations"] for p in papers),
                         "first_last_papers":sum(p["authorship"] in ("first","last") for p in papers),
                         "components":parts,"papers":papers,
                         "duplicates_suppressed":a["duplicates_suppressed"],
                         "document_types_confirmed":sum(p.get("document_type_status")=="metadata_article" for p in papers)})
        rows.sort(key=lambda a:(-a["score"],-a["publication_count"],a["name"].casefold(),a["openalex_author_id"]))
        for i,a in enumerate(rows,1):a["rank"]=i if len(rows)>=10 else None
        ranks[group]=rows
    return ranks,len(authors),conflicts

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--csv",required=True)
    opts=ap.parse_args()
    raw=json.loads(pathlib.Path(opts.input).read_text(encoding="utf-8"))
    input_records=raw["records"]
    included,excluded=classify(input_records)
    ranked,author_count,conflicts=make_ranks(included,input_records)
    stats={"candidate_records":len(input_records),"machine_screened_papers":len(included),
           "identifier_matched_author_candidates":author_count,
           "ambiguous_orcid_to_openalex_mappings":conflicts,
           "ranked_researchers":{k:len(v) for k,v in ranked.items()},
           "paper_modalities":dict(collections.Counter(m for r in included for m in r["modalities"])),
           "evidence_tiers":dict(collections.Counter(r.get("evidence_tier","unclassified") for r in included)),
           "exclusions":dict(excluded)}
    result={"generated_utc":datetime.now(timezone.utc).isoformat(),
            "ranking_label":"Provisional automated literature-index ranking (NOT verified world standing)",
            "methods_version":"2026.10-provisional-1",
            "summary":stats,"weights":SCORING_WEIGHTS,
            "minimum_relevant_papers":{"Overall":3,"each_modality":2},
            "limitations":[
                "Automated title/abstract inclusion is not a human full-text systematic review.",
                "Search queries and per-query pagination are bounded and may omit major researchers.",
                "Works with OpenAlex citation counts plus OpenAlex author IDs or ORCID-anchored bylines; identity-uncertain names remain excluded.",
                "Institutions represent the most recent affiliation documented on harvested OpenAlex work records; they are not verified current employers.",
                "Preprints, dissertations, books and conference materials are excluded by OpenAlex document type when available; works without DOI or PMID require review.",
                "Original-publication status cannot be verified for many older records lacking source document-type metadata.",
                "Exact-title duplicates are collapsed within each author; potentially different studies with the same title require adjudication.",
                "Institutional repository deposits and DOI-marked preprints are excluded pending original journal source confirmation.",
                "Citations are ranked within the harvested year/modality cohort, not global field-normalized citations.",
                "Clinical translation is a title-keyword proxy, not validated clinical impact.",
                "Scored positions are relative to this particular retrieved and machine-screened dataset, not an exhaustive world ranking.",
                "Clinical electric-field and neurostimulation pathways must not be equated with electrochemical redox or double counted as hybrid solely because of overlapping terminology.",
                "A category with fewer than 10 scorable researchers is not assigned ordinal positions."
            ],"rankings":ranked}
    out=pathlib.Path(opts.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    csvpath=pathlib.Path(opts.csv);csvpath.parent.mkdir(parents=True,exist_ok=True)
    with csvpath.open("w",newline="",encoding="utf-8-sig") as f:
        fields=["category","rank","researcher","openalex_author_id","orcid","institution","institution_year","institution_source_work","identity_method","document_types_confirmed","duplicates_suppressed","score","machine_matched_papers","indexed_citations","first_last_papers",*SCORING_WEIGHTS]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for category,rows in ranked.items():
            for r in rows:
                w.writerow({"category":category,"rank":r["rank"],"researcher":r["name"],
                            "openalex_author_id":r["openalex_author_id"],"orcid":r["orcid"],
                            "institution":r["institution"],"institution_year":r["institution_year"],
                            "institution_source_work":r["institution_source_work"],"identity_method":r["identity_method"],
                            "document_types_confirmed":r["document_types_confirmed"],
                            "duplicates_suppressed":r["duplicates_suppressed"],
                            "score":r["score"],"machine_matched_papers":r["publication_count"],
                            "indexed_citations":r["indexed_citations"],"first_last_papers":r["first_last_papers"],
                            **r["components"]})
    print(json.dumps(stats,indent=2))
    if not ranked["Overall"]:raise SystemExit("No ranking rows. Check corpus and screening logic.")
if __name__=="__main__":main()
