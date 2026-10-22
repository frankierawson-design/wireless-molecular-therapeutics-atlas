#!/usr/bin/env python3
"""Bounded diagnostic re-run; never mutates the frozen corpus or public rankings."""
import argparse
import datetime
import json
import pathlib
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'methods'))
from collect_literature import epmc_search, openalex_search

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--audit',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--limit',type=int,default=3)
    p.add_argument('--pages',type=int,default=6)
    a=p.parse_args()
    if not 1<=a.limit<=5 or not 1<=a.pages<=10:p.error('limit 1–5, pages 1–10')
    report=json.loads(pathlib.Path(a.audit).read_text())
    families={'electropharmaceutics','electrochemotherapy','electrochemical'}
    rows=[r for r in report['queries'] if r['source'] in {'OpenAlex','Europe PMC'}
          and r['status']!='end_observed' and families.intersection(r['query_families'])]
    rows.sort(key=lambda r:(r['status']!='error','electropharmaceutics' not in r['query_families'],r['query'],r['source']))
    selected=rows[:a.limit];records={};events=[]
    for row in selected:
        started=datetime.datetime.now(datetime.timezone.utc).isoformat()
        before=len(events)
        search=openalex_search if row['source']=='OpenAlex' else epmc_search
        search(row['query'],a.pages,100,records,events)
        for event in events[before:]:event['attempt_started_utc']=started
    out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
    (out/'query_audit.json').write_text(json.dumps(events,indent=2)+'\n')
    (out/'candidate_delta.json').write_text(json.dumps({'records':list(records.values()),'status':'UNSCREENED_DIAGNOSTIC_DELTA'},indent=2)+'\n')
    result={'selected_queries':selected,'new_candidate_records':len(records),
            'error_events':sum(bool(e.get('error')) for e in events),
            'queries_with_end_observed':sum(any(e['source']==r['source'] and e['query']==r['query'] and e.get('complete_for_query') for e in events) for r in selected),
            'scientific_release_permitted':False,
            'note':'Separate bounded retry, no DOI injection, no frozen corpus replacement, no independent recall estimate.'}
    (out/'retry_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
