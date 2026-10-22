#!/usr/bin/env python3
"""Create frozen, reproducible, blinded two-reviewer screening packets.

Use validation/PROTOCOL_v1.md. Never expose the unblinded key to reviewers
until each reviewer file is independently signed and returned.
"""
import argparse,csv,hashlib,json,pathlib,random,sys
from collections import Counter
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"methods"))
from build_electrochemical_queue import collect,ELECTRICAL,REMOTE,THERAPY
from build_provisional_rankings import classify
from scopes import SCOPES
from electropharmaceutics_focus import screen as focused_screen, candidate_role
from build_electrical_treatment_queue import collect as broad_collect

REFERENCE_SHA256="ee79f92617423900368049f5d1e2bbd0c097da8eb424f8a2eef7276e92f2bd59"
SEED=20261011
BLIND_FIELDS=[
    "record_id","title","publication_year","abstract_for_review",
    "article_type_original_review_preprint_thesis_conference_unknown",
    "remote_actuation_yes_no_uncertain","physical_energy_modality",
    "electrochemical_transduction_yes_no_uncertain","molecular_or_cellular_mechanism_yes_no_uncertain",
    "highest_evidence_tier_T0_T1_T2_T3_uncertain",
    "initial_eligibility_include_exclude_uncertain","reason_code",
    "supporting_text_or_page","reviewer_code","confidence_high_medium_low",
    "review_date_yyyy_mm_dd", "full_text_verified_yes_no", "evidence_source_url",
    "article_type_verified_yes_no_uncertain", "doi_pmid_verified_yes_no_uncertain"]
KEY_FIELDS=[
    "record_id","frame_stratum","stratum_population","stratum_sample_size",
    "sampling_probability","inverse_probability_weight","title","year","doi","pmid",
    "openalex_work_id","publication_types","openalex_work_type",
    "machine_eligible_electrochemical","machine_queue_status",
    "source_databases","original_author_byline","full_abstract","source_queries", "validation_scope", "machine_eligible"]

def normal_doi(x):
    t=str(x or "").casefold().strip()
    for p in ("https://doi.org/","http://doi.org/","https://dx.doi.org/"):
        if t.startswith(p):t=t[len(p):]
    return t
def record_id(r):
    # Stable opaque id: no author, rank or classifier output in ID.
    key=normal_doi(r.get("doi")) or str(r.get("openalex_id") or "") or ("pmid:"+str(r["pmid"]) if r.get("pmid") else "") or (str(r.get("year"))+":"+str(r.get("title")))
    return "E"+hashlib.sha256(key.encode("utf-8")).hexdigest()[:18]
def write_csv(path,fields,rows):
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader();w.writerows(rows)
def make_packets(records,n_negative=70,seed=SEED,scope="legacy_wireless"):
    if scope not in SCOPES:raise ValueError("Unknown validation scope")
    if scope == "electropharmaceutics":
        focused, _ = focused_screen(records)
        focused_ids={record_id(r) for r in focused}
        # Preserve distinct source records, including DOI-less duplicates, for
        # reviewer reconciliation instead of merging them by title alone.
        queue=[dict(r, _record_id=record_id(r)) for r in records if candidate_role(r)!="out_of_scope"]
    elif scope == "electrical_therapies":
        queue=broad_collect(records)["papers"]
    else:
        queue=collect(records)
    identified={}
    doi_to_id={}
    title_year_to_id={}
    for r in records:
        rid=record_id(r)
        if rid not in identified:identified[rid]=r
        doi=normal_doi(r.get("doi"))
        if doi:doi_to_id.setdefault(doi,rid)
        titleyear=(str(r.get("year") or ""),str(r.get("title") or "").strip().casefold())
        title_year_to_id.setdefault(titleyear,rid)
    # Queue exports can lack their originating OpenAlex ID when DOI is absent.
    # Reconcile by exact DOI, or only exact (title, year); never drop such rows.
    qindex={}
    unmatched=[]
    for q in queue:
        doi=normal_doi(q.get("doi"))
        key=(str(q.get("year") or ""),str(q.get("title") or "").strip().casefold())
        rid=q.get("_record_id") or (doi_to_id.get(doi) if doi else None) or title_year_to_id.get(key)
        if not rid:unmatched.append(q);continue
        if rid in qindex and qindex[rid].get("title")!=q.get("title"):
            raise ValueError("Two different queue papers mapped to one record ID")
        qindex[rid]=q
    if unmatched:
        raise ValueError("Unable to reconcile "+str(len(unmatched))+" electrochemical queue items with corpus")
    if len(qindex)!=len(queue):
        raise ValueError("Duplicate queue identities: "+str(len(queue))+" queue rows versus "+str(len(qindex))+" distinct works")
    frames={"electro_queue_census":[],"title_electrical_excluded":[],"remote_therapy_non_electrical":[],"background_random":[]}
    for rid,r in identified.items():
        title=r.get("title") or "";abstract=r.get("abstract") or ""
        if rid in qindex:frames["electro_queue_census"].append((rid,r));continue
        if ELECTRICAL.search(title):frames["title_electrical_excluded"].append((rid,r));continue
        if REMOTE.search(title+" "+abstract) and THERAPY.search(title+" "+abstract):
            frames["remote_therapy_non_electrical"].append((rid,r));continue
        frames["background_random"].append((rid,r))
    rng=random.Random(seed)
    selected=[]
    sample_sizes={}
    for stratum,items in frames.items():
        sorted_items=sorted(items,key=lambda x:x[0])
        picked=sorted_items if stratum=="electro_queue_census" else rng.sample(sorted_items,min(len(sorted_items),n_negative))
        sample_sizes[stratum]=len(picked)
        for rid,r in picked:selected.append((rid,r,stratum,len(items),len(picked)))
    assert len({item[0] for item in selected})==len(selected)
    rng.shuffle(selected)
    blinded=[]
    key=[]
    for rid,r,stratum,population,size in selected:
        q=qindex.get(rid,{})
        eligible,exc=classify([r])
        status=bool(eligible and "Electrochemical" in eligible[0].get("modalities",[]))
        if scope == "electropharmaceutics":status=rid in focused_ids
        elif scope == "electrical_therapies":
            status=bool(eligible and set(eligible[0].get("modalities",[])) & set(SCOPES[scope]))
        blinded.append({
            "record_id":rid,"title":r.get("title") or "",
            "publication_year":r.get("year") or "",
            "abstract_for_review":(r.get("abstract") or "")[:8000]})
        key.append({
            "record_id":rid,"frame_stratum":stratum,"validation_scope":scope, "machine_eligible":"include" if status else "exclude",
            "stratum_population":population,"stratum_sample_size":size,
            "sampling_probability":round(size/population,12) if population else 0,
            "inverse_probability_weight":round(population/size,10) if size else 0,
            "title":r.get("title") or "","year":r.get("year") or "",
            "doi":normal_doi(r.get("doi")),"pmid":r.get("pmid") or "",
            "openalex_work_id":r.get("openalex_id") or "",
            "publication_types":"; ".join(str(x) for x in r.get("publication_types") or []),
            "openalex_work_type":r.get("openalex_work_type") or "",
            "machine_eligible_electrochemical":"include" if status else "exclude",
            "machine_queue_status":q.get("screening_status","outside_queue"),
            "source_databases":"; ".join(r.get("source_databases") or []),
            "original_author_byline":"; ".join(str(a.get("name") or "") for a in (r.get("authors") or [])),
            "full_abstract":r.get("abstract") or "",
            "source_queries":"; ".join(r.get("source_queries") or []),
        })
    return frames,blinded,key,sample_sizes

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--expected-sha256",default=REFERENCE_SHA256)
    p.add_argument("--negative-per-stratum",type=int,default=70)
    p.add_argument("--seed",type=int,default=SEED)
    p.add_argument("--scope", choices=tuple(SCOPES), default="legacy_wireless")
    a=p.parse_args()
    if a.negative_per_stratum<1:p.error("negative-per-stratum must be positive")
    source=pathlib.Path(a.candidates)
    actual=hashlib.sha256(source.read_bytes()).hexdigest()
    if a.expected_sha256 and actual!=a.expected_sha256:
        raise SystemExit("FROZEN CORPUS HASH MISMATCH: expected "+a.expected_sha256+" actual "+actual)
    records=json.loads(source.read_text(encoding="utf-8"))["records"]
    frames,blinded,key,sizes=make_packets(records,a.negative_per_stratum,a.seed,a.scope)
    out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
    reviewer_files=[]
    for i,code in enumerate(("A","B")):
        rows=list(blinded)
        random.Random(a.seed+1001+i).shuffle(rows)
        file=out/("reviewer_"+code+"_blinded.csv")
        write_csv(file,BLIND_FIELDS,rows)
        reviewer_files.append(file)
    write_csv(out/"adjudicator_key_DO_NOT_SHARE_WITH_REVIEWERS.csv",KEY_FIELDS,key)
    write_csv(out/"adjudication_BLANK.csv",[
        "record_id","adjudicator_code","reviewer_A_locked_date","reviewer_B_locked_date",
        "final_eligibility_include_exclude_uncertain","final_evidence_tier_T0_T1_T2_T3_uncertain",
        "article_type_verified_yes_no_uncertain","doi_pmid_verified_yes_no_uncertain",
        "energy_modality_verified","evidence_source_url","full_text_page_or_quotation",
        "exclusion_reason","adjudication_date_yyyy_mm_dd","notes"
    ],[{"record_id":x["record_id"]} for x in key])
    with (out/"independent_reference_set_BLANK.csv").open("w",newline="",encoding="utf-8-sig") as f:
        cols=["reference_id","modality","doi","pmid","title",
              "independent_discovery_method","source_before_atlas_lookup","reviewer_confirmed_original_yes_no",
              "remote_actuation_yes_no","evidence_tier_T0_T1_T2_T3",
              "independent_eligibility_include_exclude_uncertain","verification_url","reviewer_id","review_date","full_text_page_or_quotation"]
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for modality in SCOPES[a.scope]:
            w.writerow({"modality":modality})
    with (out/"author_identity_audit_BLANK.csv").open("w",newline="",encoding="utf-8-sig") as f:
        fields=["audit_id","paper_doi_or_openalex","byline_author_name","candidate_openalex_author_id",
                "candidate_orcid","publisher_byline_url","orcid_crosscheck_url","institution_evidence",
                "classification_correct_wrong_person_split_ambiguous_unverifiable","independent_reviewer",
                "reconciled_identity","notes"]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    manifest={"protocol_version":"v1.1-amendment", "validation_scope":a.scope,"frozen_source_sha256":actual,
              "sampling_seed":a.seed,"negative_per_stratum":a.negative_per_stratum,
              "source_record_count":len(records),
              "frame_populations":{k:len(v) for k,v in frames.items()},
              "sample_sizes":sizes,"total_sample":len(blinded),
              "files_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob("*.csv")},
              "reviewers_blinded_to":["machine_eligible_electrochemical","machine_queue_status",
                   "source_queries","doi","author bylines","ranking positions"],
              "source_status":"not screened; no author or full-text validation implied"}
    (out/"packet_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))
    if not blinded:raise SystemExit("No screening candidates generated")
if __name__=="__main__":main()

