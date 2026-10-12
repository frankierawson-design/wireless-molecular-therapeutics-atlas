#!/usr/bin/env python3
"""Prospective, conservative electro-mediated pharmaceutics screen.

Electrical treatment alone is NOT pharmaceutical mediation. Results are
machine candidates, not independently reviewed therapeutic effectiveness.
"""
import argparse
import collections
import csv
import json
import pathlib
import re
import build_provisional_rankings as rank

FIELD="Electro-Mediated Pharmaceutics"
ELECTRIC=re.compile(r"\b(?:electrochem\w*|electrotherap\w*|electrochemotherap\w*|"
 r"electroporat\w*|electric(?:al)?[ -](?:fields?|stimulat\w*|actuat\w*)|"
 r"alternating[ -]current|a\.?c\.?[ -]field|"
 r"bioelectronic\w*|bipolar[ -]electrod\w*|bipolar[ -]electro\w*|"
 r"redox[ -](?:switch\w*|control\w*|responsive)|"
 r"organic[ -]electronic[ -]ion[ -]pump|"
 r"electrically[ -](?:controlled|triggered|responsive|activated)|"
 r"electroresponsive|electroactive|conducting[ -]polymer|"
 r"electric[ -]field[ -]responsive|iontronic|wirefree[ -]electro\w*)\b",re.I)
PHARM=re.compile(r"\b(?:drug\w*|pharmacolog\w*|pharmaceut\w*|chemotherap\w*|"
 r"bleomycin|cisplatin|vincristine|temozolomide|doxorubicin|"
 r"therapeutic[ -](?:molecule\w*|agent\w*|compound\w*)|"
 r"neurotransmitter\w*|acetylcholine|brain[ -]derived[ -]neurotrophic[ -]factor|"
 r"growth[ -]factor\w*|cytochrome|"
 r"nanomedicin\w*|bio[- ]nanoantenna\w*|"
 r"drug[ -]resistan\w*|medicinal[ -]molecule\w*|"
 r"drug[ -](?:deliver\w*|releas\w*|uptake)|"
 r"molecular[ -](?:therap\w*|actuat\w*|releas\w*|deliver\w*)|"
 r"porphyrin\w*|redox[ -]mediator\w*)\b",re.I)
INTERVENTION=re.compile(r"\b(?:deliv\w*|releas\w*|activat\w*|actuat\w*|"
 r"uptake|internalis\w*|internaliz\w*|"
 r"endosom\w*|sensitivity|sensiti[sz]\w*|"
 r"resistan\w*|cell[ -]death|apoptos\w*|"
 r"tumou?r[ -]response|"
 r"cell[ -]viability|electrochemotherap\w*|"
 r"cell[ -]apoptos\w*|cell[ -]signall\w*|"
 r"neuromodulat\w*|redox[ -]state|bioavailabil\w*|"
 r"therap\w*|cytotoxi\w*|controlled)\b",re.I)
JUST_ELECTRICAL=re.compile(r"\b(?:tumou?r[ -]treating[ -]fields?|ttfields?|"
 r"deep[ -]brain[ -]stimulation|vagus[ -]nerve[ -]stimulation|"
 r"spinal[ -]cord[ -]stimulation|electrical[ -]muscle[ -]stimulation|"
 r"pulsed[ -]field[ -]ablation|irreversible[ -]electroporat\w*|"
 r"wound[ -]healing)\b",re.I)
DIAGNOSTIC=re.compile(r"\b(?:sensing|sensor\w*|diagnos\w*|"
 r"impedimetric|electroanalyt\w*|characteri[sz]ation|monitor\w*)\b",re.I)
CLINICAL_DRUG=re.compile(r"\b(?:electrochemotherap\w*|"
 r"bleomycin|cisplatin|drug[ -]uptake|drug[ -]deliver\w*|"
 r"drug[ -]resistan\w*|nanomedicin\w*|bio[- ]nanoantenna\w*|"
 r"cytochrome)\b",re.I)
ELECTRO_MOLECULAR=re.compile(r"\b(?:electrical[ -]molecular|"
 r"electrochemically[ -]controlled|electrochemically[ -]triggered|"
 r"redox[ -]controlled|electric[ -]field[ -]induced)\b",re.I)
NONORIGINAL={"dissertation","conference-paper","conference-abstract","review",
 "book","book-chapter","preprint","editorial","erratum","report","peer-review",
 "paratext","retraction"}
REFERENCE_REVIEW={"10.1039/d3bm01946b","10.1016/j.elecom.2024.107832",
                  "10.1016/j.coelec.2023.101297"}

def norm_doi(value):
    return re.sub(r"^https?://(?:dx\.)?doi\.org/","",str(value or "").strip().casefold())
def tidy(s):
    return str(s or "").replace("–","-").replace("—","-").replace("−","-").replace("‑","-").replace("\u00a0"," ")

def candidate_role(paper):
    """Return one of direct_candidate, enabling_context, out_of_scope."""
    title=tidy(paper.get("title"))
    abstract=tidy(paper.get("abstract"))
    combined=title+" "+abstract
    if not (ELECTRIC.search(title) or
            (ELECTRIC.search(abstract) and PHARM.search(title)) or
            (ELECTRO_MOLECULAR.search(title) and PHARM.search(abstract))):
        return "out_of_scope"
    # Co-treatment, TTFields + TMZ, electrical ablation and standalone
    # neurostimulation do not automatically establish electro-*mediated* drug
    # action. Require explicit electrical effect on the medicinal component.
    if JUST_ELECTRICAL.search(title) and not (
        CLINICAL_DRUG.search(title) and
        (ELECTRO_MOLECULAR.search(combined) or
         re.search(r"\b(?:electrochemotherap\w*|electroporat\w*|"
                   r"drug[ -](?:sensiti[sz]\w*|deliver\w*|uptake|releas\w*))\b",title,re.I))):
        return "out_of_scope"
    if DIAGNOSTIC.search(title) and not (
        CLINICAL_DRUG.search(title) and INTERVENTION.search(title)):
        return "enabling_context" if PHARM.search(combined) else "out_of_scope"
    # An electrical event must demonstrably mediate an effect on medicinal
    # cargo/biomolecules; title context alone is insufficient to score.
    if PHARM.search(combined) and INTERVENTION.search(combined) and (
        PHARM.search(title) or ELECTRO_MOLECULAR.search(title) or
        re.search(r"\b(?:drug[ -]release|ion[ -]pump|"
                  r"electrochemotherap\w*)\b",title,re.I)
    ):
        return "direct_candidate"
    if ELECTRIC.search(combined) and (PHARM.search(combined) or
        re.search(r"\b(?:electron[ -]transport|cell\w*|"
                  r"nanoelectrod\w*|tissue)\b",title,re.I)):
        return "enabling_context"
    return "out_of_scope"

def original_metadata(paper):
    try:year=int(paper.get("year") or 0)
    except (TypeError,ValueError):return False
    if not 2000<=year<=2026:return False
    if not paper.get("openalex_id"):return False
    if not isinstance(paper.get("citations_openalex"),int):return False
    doi=norm_doi(paper.get("doi"))
    if not doi and not paper.get("pmid"):return False
    if doi in REFERENCE_REVIEW:return False
    if re.match(r"^10\.(?:1101/|26434/chemrxiv|2139/ssrn|48550/arxiv|20944/preprints|21203/rs|17615/|25148/etd|3929/)",doi):return False
    typ=str(paper.get("openalex_work_type") or "").casefold()
    if typ in NONORIGINAL:return False
    if rank.matches(rank.REVIEW,paper.get("title") or "") or rank.matches(rank.REVIEW_ABSTRACT,paper.get("abstract") or ""):return False
    pt="; ".join(map(str,paper.get("publication_types") or []))
    if rank.matches(r"\b(?:review|meta.analysis|editorial|perspective|data descriptor)\b",pt):return False
    if rank.matches(r"^data on\b",paper.get("title") or ""):return False
    return any(rank.norm_aid(a.get("openalex_author_id")) or
        rank.norm_orcid(a.get("orcid")) for a in paper.get("authors") or [])

def screen(records):
    included=[]
    register=[]
    for p in records:
        role=candidate_role(p)
        if role=="out_of_scope":continue
        scored=role=="direct_candidate" and original_metadata(p)
        entry={"doi":norm_doi(p.get("doi")),"title":p.get("title") or "",
            "year":p.get("year"),"role":role,
            "scored_machine_candidate":scored,
            "reviewed_full_text":False,
            "authors":[a.get("name") or "" for a in p.get("authors") or []],
            "source_work":p.get("openalex_id") or "",
            "document_type":p.get("openalex_work_type") or "",
            "reason":("original-metadata+screen pass; human verification pending"
                 if scored else "supporting/mechanistic context or metadata review required")}
        register.append(entry)
        if scored:
            row=dict(p)
            row["year"]=int(row["year"])
            row["modalities"]=[FIELD]
            row["evidence_tier"]="electrically_mediated_pharmaceutical_effect_candidate"
            included.append(row)
    return included,register

def build(records):
    eligible,register=screen(records)
    # Scoped runner; avoid modifying the legacy broader ranking pipeline.
    if FIELD not in rank.MODALITIES:
        rank.MODALITIES[FIELD]=r"\b__electropharm_only_do_not_match__\b"
    ranks,n,ambiguous=rank.make_ranks(eligible,records)
    rows=ranks.get(FIELD,[])
    return {"ranking_label":"Provisional electro-mediated pharmaceutics comparison — NOT a validated world ranking",
        "scope":FIELD,"scientific_validation":"NOT_INDEPENDENTLY_SCREENED",
        "generated_utc":rank.datetime.now(rank.timezone.utc).isoformat(),
        "summary":{"candidate_records":len(records),
                   "machine_screened_papers":len(eligible),
                   "enabling_or_mechanistic_context":sum(r["role"]=="enabling_context" for r in register),
                   "ranked_researchers":{FIELD:len(rows),"Overall":len(rows)},
                   "paper_modalities":{FIELD:len(eligible)},
                   "ambiguous_orcid_to_openalex_mappings":ambiguous,
                   "field_relevance_audited":False},
        "rankings":{FIELD:rows,"Overall":rows},
        "weights":rank.SCORING_WEIGHTS,
        "machine_candidate_publications":register,
        "limitations":["Drug, bioactive molecule or molecular therapeutic action must be electrically mediated, not simply co-administered alongside electric-field treatment.",
            "Electric-field treatment, standalone TTFields, ablation, DBS, wound stimulation and unmodified neuromodulation do not qualify automatically.",
            "Diagnostic and enabling redox/transport studies are recorded separately from therapeutic pharmaceutical evidence.",
            "Only DOI/PMID and OpenAlex citation-backed original-article candidates are scored; full text and author identities require independent verification.",
            "Title and abstract screening has not been independently validated for recall/precision, author completeness or clinical impact.",
            "This is a bounded source-relative exploratory index, NOT a comprehensive worldwide scientist ranking."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--csv",required=True)
    p.add_argument("--register",required=True)
    args=p.parse_args()
    source=json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
    result=build(source["records"])
    out=pathlib.Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({k:v for k,v in result.items() if k!="machine_candidate_publications"},
                              ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    reg=pathlib.Path(args.register);reg.parent.mkdir(parents=True,exist_ok=True)
    reg.write_text(json.dumps({"scope":FIELD,"screening_status":"NOT_INDEPENDENTLY_SCREENED",
                              "publications":result["machine_candidate_publications"]},
                            ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    with pathlib.Path(args.csv).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["rank","researcher","institution","score","matched_publications","orcid"])
        w.writeheader()
        for r in result["rankings"][FIELD]:
            w.writerow({"rank":r["rank"],"researcher":r["name"],"institution":r["institution"],
                        "score":r["score"],"matched_publications":r["publication_count"],
                        "orcid":r["orcid"]})
    print("Focused pharmaceutical therapeutic papers:",result["summary"]["machine_screened_papers"])
    print("Focused academic rows:",result["summary"]["ranked_researchers"][FIELD])
if __name__=="__main__":main()
