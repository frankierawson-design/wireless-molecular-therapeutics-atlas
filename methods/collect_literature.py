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
                    if not a.get("orcid") and b.get("orcid"):
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
                    "publication_types":[v.get("name") or "" for v in (hit.get("pubTypeList") or {}).get("pubType") or []],
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
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="output")
    p.add_argument("--pages",type=int,default=3)
    p.add_argument("--epmc-page-size",type=int,default=250)
    p.add_argument("--openalex-page-size",type=int,default=100)
    p.add_argument("--source",choices=("both","epmc","openalex"),default="both")
    a=p.parse_args()
    folder=pathlib.Path(a.output);folder.mkdir(parents=True,exist_ok=True)
    records={};audit=[]
    for modality,qs in QUERIES.items():
        for phrase in qs:
            print("SEARCH",modality,phrase,flush=True)
            if a.source in ("both","epmc"): epmc_search(phrase,a.pages,a.epmc_page_size,records,audit)
            if a.source in ("both","openalex"):openalex_search(phrase,a.pages,a.openalex_page_size,records,audit)
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
    summary={"generated_utc":now,"search_strings":sum(map(len,QUERIES.values())),"candidate_records":len(arr),
             "query_page_events":len(audit),"errors":errors,"pages_at_end_of_result_set":complete,
             "bounded_by_page_limits":True,"rankings_permitted":False,"full_text_screened":0,
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
