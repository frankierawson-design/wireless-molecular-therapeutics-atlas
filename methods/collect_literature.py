#!/usr/bin/env python3
"""Reproducible *candidate* literature discovery. No automatic inclusion or rankings.

Public API sources: Europe PMC (includes PubMed); OpenAlex (optional API key).
Every search is bounded and logged, so results must never be called exhaustive.
Python 3.11+, standard library only.
"""
import argparse, csv, datetime, sys, json, os, pathlib, re, time, urllib.error, urllib.parse, urllib.request

QUERIES = {
 "electrochemical": [
  "wireless bipolar electrochemistry cell therapy",
  "bipolar electrochemistry cancer treatment",
  "wireless electrochemical drug delivery",
  "electrochemical drug release therapy",
  "wireless electroceutical nanoparticles",
  "bipolar electroactive conducting polymers cell stimulation",
  "wirefree electrochemical stimulation biological cells",
  "bipolar electrostimulation nerve cell differentiation",
  "wireless control nerve growth bipolar electrodes",
  "wireless bipolar electrode neuron growth",
  "wirefree electrochemistry drug release",
  "bipolar electrochemistry drug loading release",
  "electrochemical release conducting polymer therapy",
  "electrically controlled therapeutic molecule delivery",
  "electroresponsive conducting polymer drug delivery",
  "wireless organic electronic ion pump",
  "photo powered ion pump neurotransmitter delivery",
  "ultrasonically powered electrochemical drug release implant",
  "wirelessly powered electrochemical drug release",
  "wireless electrostimulation cancer nanoparticle",
  "bio nano antenna cancer cell electrical signalling",
  "electrical molecular quantum signalling apoptosis",
  "electric field transmembrane electron transport cells",
  "wireless electrochemistry cancer nanoparticle therapy",
  "electrochemical generation therapeutic nitric oxide",
  "electrochemical modulation cancer cell bioelectronics",
  "wireless bioelectronic membrane potential glioblastoma",
  "ferroelectric nanoparticle intracellular electric field cancer",
  "nanoscale bipolar electrodes biological activity",
  "contactless electrochemical therapeutic stimulation",
  "redox controlled drug release electroactive biomaterials",
 ],
 "ultrasound": [
  "sonodynamic therapy nanoparticles cancer",
  "ultrasound triggered drug delivery",
  "ultrasound piezoelectric nanomedicine",
  "focused ultrasound blood brain barrier drug delivery",
  "ultrasound controlled molecular therapy",
 ],
 "magnetic": [
  "magnetoelectric nanoparticles therapy",
  "magnetothermal therapy drug release",
  "magnetically triggered drug delivery",
  "magnetomechanical cell therapy",
  "magnetic field wireless neuromodulation nanoparticles",
 ],
 "optical": [
  "photopharmacology photoswitchable drugs",
  "near infrared triggered drug delivery",
  "light activated molecular therapy",
  "photocaged drug therapy",
  "photoelectrochemical cancer treatment",
 ],
 "radiofrequency": [
  "radiofrequency triggered drug delivery",
  "radiofrequency activated nanomedicine",
  "electromagnetic field activated therapy nanoparticles",
 ],
 "hybrid": [
  "wireless molecular therapeutics hybrid energy",
  "magnetoelectric ultrasound cancer therapy",
  "remote controlled nanomedicine therapy",
 ],
}
# DOI-level retrieval is applied to *all* documented electrochemical sentinels,
# not only a favoured researcher. A sentinel forces discovery, never ranking eligibility.
DOI_SENTINELS=(
 "10.1038/s41565-023-01496-y",
 "10.1002/advs.202516561",
 "10.1021/acsomega.1c03547",
 "10.1038/s41598-024-71236-2",
 "10.1021/acs.langmuir.6c00755",
 "10.1038/s43246-025-00750-1",
 "10.1038/s41528-019-0060-6",
 "10.1039/d5lc00708a",
 "10.1039/d3bm01946b",
 "10.1016/j.elecom.2024.107832",
 "10.1039/d4cc03996c",
 "10.1021/acs.analchem.4c04454",
 "10.1002/celc.202400506",
 "10.1016/j.apmt.2020.100804",
 "10.1016/j.apmt.2022.101481",
 "10.1016/j.elecom.2023.107626",
 "10.1016/j.coelec.2023.101297",
)
# These named bylines and ORCID links were checked against primary publisher or
# institutional records. Do not attribute identities solely from a surname match.
DOCUMENTED_DOI_ORCID={
 doi:"0000-0001-5079-3123" for doi in (
  "10.1021/acs.langmuir.6c00755",
  "10.1016/j.apmt.2020.100804",
  "10.1016/j.apmt.2022.101481",
  "10.1016/j.elecom.2023.107626",
  "10.1016/j.elecom.2024.107832",
  "10.1039/d4cc03996c",
  "10.1021/acs.analchem.4c04454",
  "10.1002/celc.202400506",
  "10.1016/j.coelec.2023.101297",
 )
}

UA="WirelessMolecularTherapeuticsAtlas/0.1 (bibliographic research; https://github.com/frankierawson-design/wireless-molecular-therapeutics-atlas)"
def fetch(url, params, tries=3):
    target=url+"?"+urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(target,headers={"User-Agent":UA,"Accept":"application/json"}), timeout=45) as f:
                return json.load(f)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError) as e:
            if i==tries-1: raise RuntimeError(str(e))
            time.sleep(min(12,2**(i+1)))
def doi_norm(s):
    return re.sub(r"^https?://(?:dx\.)?doi\.org/","",str(s or "").strip(),flags=re.I).casefold()
def text_norm(s):
    return re.sub(r"\W+"," ",str(s or "").casefold()).strip()
def matchkey(item):
    doi=doi_norm(item.get("doi"))
    if doi: return "doi:"+doi
    if item.get("pmid"):return "pmid:"+str(item["pmid"])
    return "title:"+text_norm(item.get("title"))[:180]+":"+str(item.get("year") or "")
def merge(out,record):
    key=matchkey(record)
    if key in out:
        old=out[key]
        old["source_databases"]=sorted(set(old["source_databases"]+record["source_databases"]))
        old["source_queries"]=sorted(set(old["source_queries"]+record["source_queries"]))
        for k in ("doi","pmid","openalex_id","title","year","abstract","citations_openalex","publication_types","openalex_work_type"):
            if old.get(k) is None or old.get(k) == "":
                if record.get(k) is not None and record.get(k) != "":
                    old[k]=record[k]
        # Crucial: Europe PMC often arrives first with initials/ORCIDs but no
        # OpenAlex author IDs. Prefer the exact-DOI matched OpenAlex authorship
        # array, which also records each author's institution on this paper.
        old_authors=old.get("authors") or []
        new_authors=record.get("authors") or []
        old_ids=sum(bool(a.get("openalex_author_id")) for a in old_authors)
        new_ids=sum(bool(a.get("openalex_author_id")) for a in new_authors)
        if new_ids > old_ids:
            if len(old_authors)==len(new_authors):
                for a,b in zip(new_authors,old_authors):
                    # Do not transfer an ORCID to an unrelated author if
                    # the two providers disagree on byline ordering.
                    tokens_a={x for x in re.findall(r"[a-z]{4,}",(a.get("name") or "").lower())}
                    tokens_b={x for x in re.findall(r"[a-z]{4,}",(b.get("name") or "").lower())}
                    if (tokens_a & tokens_b) and not a.get("orcid") and b.get("orcid"):
                        a["orcid"]=b["orcid"]
            old["authors"]=new_authors
            old["author_source"]="OpenAlex authorships (exact work/DOI)"
        elif not old_authors and new_authors:
            old["authors"]=new_authors
        return
    out[key]=record
def epmc_authors(hit):
    authorlist=hit.get("authorList") or {}
    if isinstance(authorlist,dict) and authorlist.get("author"):
        return [{"name":a.get("fullName") or a.get("lastName") or "", "orcid":a.get("authorId",{}).get("value") if isinstance(a.get("authorId"),dict) else ""} for a in authorlist.get("author",[])]
    return [{"name":v.strip()} for v in (hit.get("authorString") or "").split(",") if v.strip()]
def epmc_search(phrase, pages, perpage, output, audit):
    cursor="*"
    for page in range(pages):
        try:
            data=fetch("https://www.ebi.ac.uk/europepmc/webservices/rest/search", {
                "query":phrase,"format":"json","pageSize":perpage,"cursorMark":cursor,"resultType":"core"})
            hits=(data.get("resultList") or {}).get("result") or []
            for hit in hits:
                merge(output,{"title":hit.get("title") or "", "doi":doi_norm(hit.get("doi")),
                    "pmid":hit.get("pmid") or "", "openalex_id":"", "year":hit.get("pubYear"),
                    "abstract":re.sub("<[^>]*>"," ",hit.get("abstractText") or ""),
                    "publication_types":[(v.get("name") or "") if isinstance(v,dict) else str(v)
                         for v in ((hit.get("pubTypeList") or {}).get("pubType") or [])
                         if isinstance(v,(str,dict))],
                    "authors":epmc_authors(hit),"citations_openalex":None,
                    "source_databases":["Europe PMC"],"source_queries":[phrase],
                    "review_status":"UNSCREENED","identity_status":"UNVERIFIED"})
            next_cursor=data.get("nextCursorMark")
            audit.append({"source":"Europe PMC","query":phrase,"page":page+1,"retrieved":len(hits),
                "reported_total":data.get("hitCount"),"error":"","complete_for_query":bool(not hits or len(hits)<perpage or not next_cursor or next_cursor==cursor)})
            if not hits or len(hits)<perpage or not next_cursor or next_cursor==cursor:break
            cursor=next_cursor
            time.sleep(.15)
        except Exception as e:
            audit.append({"source":"Europe PMC","query":phrase,"page":page+1,"retrieved":0,"error":str(e),"complete_for_query":False})
            break
def openalex_abstract(positions):
    """Reconstruct a compact abstract from OpenAlex's inverted index."""
    if not isinstance(positions,dict): return ""
    terms=[]
    for word,locations in positions.items():
        for n in locations:
            if isinstance(n,int) and 0<=n<5000:terms.append((n,word))
    terms.sort()
    return " ".join(word for _,word in terms)

def openalex_search(phrase,pages,perpage,output,audit):
    cursor="*"
    for page in range(pages):
        try:
            params={"search":phrase,"per-page":perpage,"cursor":cursor}
            if os.getenv("OPENALEX_API_KEY"):params["api_key"]=os.environ["OPENALEX_API_KEY"]
            data=fetch("https://api.openalex.org/works",params)
            hits=data.get("results") or []
            for hit in hits:
                authors=[{"name":(a.get("author") or {}).get("display_name") or "",
                           "orcid":(a.get("author") or {}).get("orcid") or "",
                           "openalex_author_id":(a.get("author") or {}).get("id") or "",
                           "position":a.get("author_position") or "",
                           "institutions":[{"name":i.get("display_name") or "",
                                            "id":i.get("id") or ""}
                                            for i in a.get("institutions") or []
                                            if i.get("display_name")],
                           "raw_affiliations":a.get("raw_affiliation_strings") or []}
                         for a in hit.get("authorships") or []]
                merge(output,{"title":hit.get("title") or hit.get("display_name") or "",
                    "doi":doi_norm(hit.get("doi")),"pmid":(hit.get("ids") or {}).get("pmid") or "",
                    "openalex_id":hit.get("id") or "", "year":hit.get("publication_year"),
                    "abstract":openalex_abstract(hit.get("abstract_inverted_index")),
                    "openalex_work_type":hit.get("type") or "",
                    "authors":authors,"citations_openalex":hit.get("cited_by_count"),
                    "source_databases":["OpenAlex"],"source_queries":[phrase],
                    "review_status":"UNSCREENED","identity_status":"UNVERIFIED",
                    "author_source":"OpenAlex authorships (exact work/DOI)"})
            next_cursor=(data.get("meta") or {}).get("next_cursor")
            audit.append({"source":"OpenAlex","query":phrase,"page":page+1,"retrieved":len(hits),
                "reported_total":(data.get("meta") or {}).get("count"),"error":"",
                "complete_for_query":bool(not hits or len(hits)<perpage or not next_cursor or next_cursor==cursor)})
            if not hits or len(hits)<perpage or not next_cursor or next_cursor==cursor:break
            cursor=next_cursor
            time.sleep(.2)
        except Exception as e:
            audit.append({"source":"OpenAlex","query":phrase,"page":page+1,"retrieved":0,"error":str(e),"complete_for_query":False})
            break

def reconcile_documented_authorship(record):
    """Restore independently publisher-verified ORCID on exact DOI-and-byline match.
    
    Never fabricate an OpenAlex author ID. A surname-only or absent byline
    cannot be repaired. This provenance is not an independent full-text screen.
    """
    doi=doi_norm(record.get("doi"))
    orcid=DOCUMENTED_DOI_ORCID.get(doi)
    if not orcid:return False
    matches=[a for a in (record.get("authors") or []) if
             re.search(r"\\bforster\\b",str(a.get("name") or ""),re.I)
             and re.search(r"\\b(?:robert|r\\.?\\s*j\\.?)\\b",str(a.get("name") or ""),re.I)]
    if len(matches)!=1:return False
    author=matches[0]
    actual=str(author.get("orcid") or "")
    if actual and orcid not in actual.upper():
        # Conflicting author ORCID: do not override bibliographic metadata.
        record["documented_identity_conflict"]=True
        return False
    if not actual:author["orcid"]="https://orcid.org/"+orcid
    author["verified_orcid_from_publication"]=orcid
    record["author_identity_enrichment"]="Primary-publisher DOI and named-byline corroboration"
    return True

def openalex_doi_sentinels(output,audit):
    """Exact DOI lookups ensure that capped keyword rankings expose known misses."""
    for doi in DOI_SENTINELS:
        try:
            params={}
            if os.getenv("OPENALEX_API_KEY"):params["api_key"]=os.environ["OPENALEX_API_KEY"]
            hit=fetch("https://api.openalex.org/works/https://doi.org/"+doi,params,tries=2)
            authors=[{"name":(a.get("author") or {}).get("display_name") or "",
                      "orcid":(a.get("author") or {}).get("orcid") or "",
                      "openalex_author_id":(a.get("author") or {}).get("id") or "",
                      "position":a.get("author_position") or "",
                      "institutions":[{"name":i.get("display_name") or "","id":i.get("id") or ""}
                                      for i in a.get("institutions") or [] if i.get("display_name")],
                      "raw_affiliations":a.get("raw_affiliation_strings") or []}
                     for a in (hit.get("authorships") or [])]
            found=doi_norm(hit.get("doi"))
            if found!=doi:
                raise ValueError("API returned unexpected DOI "+found)
            rec={"title":hit.get("title") or hit.get("display_name") or "",
                 "doi":found,"pmid":(hit.get("ids") or {}).get("pmid") or "",
                 "openalex_id":hit.get("id") or "",
                 "year":hit.get("publication_year"),"abstract":openalex_abstract(hit.get("abstract_inverted_index")),
                 "openalex_work_type":hit.get("type") or "",
                 "authors":authors,"citations_openalex":hit.get("cited_by_count"),
                 "source_databases":["OpenAlex"],"source_queries":["exact-doi:"+doi],
                 "review_status":"UNSCREENED","identity_status":"UNVERIFIED",
                 "author_source":"OpenAlex authorships (exact work/DOI)"}
            merge(output,rec)
            row=output[matchkey(rec)]
            checked=reconcile_documented_authorship(row)
            audit.append({"source":"OpenAlex DOI lookup","query":doi,"page":1,
                          "retrieved":1,"reported_total":1,"error":"",
                          "complete_for_query":True,
                          "documented_byline_reconciled":checked})
        except Exception as e:
            # A sentinel failing lookup cannot become a synthetic paper.
            audit.append({"source":"OpenAlex DOI lookup","query":doi,"page":1,
                          "retrieved":0,"reported_total":0,"error":str(e),
                          "complete_for_query":False})
    # Earlier keyword records may have the exact DOI already but incomplete ORCID.
    for record in output.values():
        reconcile_documented_authorship(record)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="output")
    p.add_argument("--pages",type=int,default=3)
    p.add_argument("--epmc-page-size",type=int,default=250)
    p.add_argument("--openalex-page-size",type=int,default=100)
    p.add_argument("--source",choices=("both","epmc","openalex"),default="both")
    p.add_argument("--only-modalities",default="",help="Comma-separated modality names, defaults to all")
    p.add_argument("--baseline",default="",help="Existing candidates.json for incremental merge")
    p.add_argument("--baseline-audit",default="",help="Existing query_audit.json to preserve source provenance")
    p.add_argument("--doi-only",action="store_true",help="Only reconcile registered DOI sentinels against a substantial existing harvest")
    a=p.parse_args()
    folder=pathlib.Path(a.output);folder.mkdir(parents=True,exist_ok=True)
    records={};audit=[]
    if a.baseline:
        olddata=json.loads(pathlib.Path(a.baseline).read_text(encoding="utf-8"))
        for record in olddata.get("records") or []:
            merge(records,record)
        if a.baseline_audit:
            audit=json.loads(pathlib.Path(a.baseline_audit).read_text(encoding="utf-8"))
        print("Incremental base papers:",len(records),flush=True)
    selected={x.strip().casefold() for x in a.only_modalities.split(",") if x.strip()}
    invalid=selected-set(QUERIES)
    if invalid:p.error("Unknown modalities: "+", ".join(sorted(invalid)))
    selected_queries={} if a.doi_only else {k:qs for k,qs in QUERIES.items() if not selected or k in selected}
    if a.doi_only and not a.baseline:p.error("--doi-only requires --baseline")
    for modality,qs in selected_queries.items():
        for phrase in qs:
            print("SEARCH",modality,phrase,flush=True)
            if a.source in ("both","epmc"): epmc_search(phrase,a.pages,a.epmc_page_size,records,audit)
            if a.source in ("both","openalex"):openalex_search(phrase,a.pages,a.openalex_page_size,records,audit)
    openalex_doi_sentinels(records,audit)
    arr=sorted(records.values(),key=lambda r: int(r.get('year') or 0) if str(r.get('year') or '').isdigit() else 0,reverse=True)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (folder/"candidates.json").write_text(json.dumps({"generated_utc":now,"scope":"candidate discovery only; not screened or exhaustive","records":arr},ensure_ascii=False,indent=2),encoding="utf8")
    (folder/"query_audit.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding="utf8")
    with (folder/"candidates.csv").open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=["title","year","doi","pmid","openalex_id","source_databases","source_queries","citations_openalex","review_status","identity_status"])
        w.writeheader()
        for r in arr:
            w.writerow({k:"; ".join(map(str,r.get(k) or [])) if isinstance(r.get(k),list) else r.get(k) for k in w.fieldnames})
    errors=sum(bool(x.get("error")) for x in audit)
    complete=sum(bool(x.get("complete_for_query")) for x in audit)
    summary={"generated_utc":now,"search_strings":sum(map(len,QUERIES.values())),
             "search_strings_executed":sum(map(len,selected_queries.values())),
             "incremental_baseline":bool(a.baseline),"candidate_records":len(arr),
             "query_page_events":len(audit),"errors":errors,"pages_at_end_of_result_set":complete,
             "bounded_by_page_limits":True,"doi_only_reconciliation":bool(a.doi_only),"doi_sentinels_checked":len(DOI_SENTINELS),
             "rankings_permitted":False,"full_text_screened":0,
             "note":"A successful run does not establish exhaustive retrieval, author identity or eligible field publications."}
    (folder/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf8")
    # Export a dual-review-ready CSV; leave all eligibility decisions empty.
    import subprocess
    subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name("build_screening_sheet.py")),
                    "--input",str(folder/"candidates.json"),
                    "--output",str(folder/"manual_screening_sheet.csv")],check=True)
    print(json.dumps(summary,indent=2))
    if not arr:raise SystemExit("ERROR: no records retrieved: inspect query_audit.json")
if __name__=="__main__":main()
