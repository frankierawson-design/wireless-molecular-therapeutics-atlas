#!/usr/bin/env python3
"""Audit frozen artifacts without inferring independent recall or eligibility."""
import argparse
import collections
import csv
import hashlib
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'methods'))
from collect_literature import QUERIES
from electrical_treatment_coverage_audit import SENTINELS
from scopes import normalize_doi


def query_report(events):
    groups = collections.defaultdict(list)
    for event in events:
        groups[(event['source'], event['query'])].append(event)
    rows = []
    for (source, query), history in sorted(groups.items()):
        # Merged logs have no run ID. Page resets delimit inferred attempts;
        # never sum repeat pages as unique coverage or erase historic errors.
        latest = []
        previous = 0
        for event in history:
            page = int(event.get('page') or 1)
            if page <= previous:
                latest = []
            latest.append(event)
            previous = page
        terminal = any(x.get('complete_for_query') is True for x in latest)
        errors = sum(bool(x.get('error')) for x in latest)
        families = [family for family, queries in QUERIES.items() if query in queries]
        rows.append({'source': source, 'query': query, 'query_families': families,
                     'historical_error_events': sum(bool(x.get('error')) for x in history),
                     'latest_attempt_error_events': errors,
                     'latest_attempt_last_page': previous,
                     'latest_attempt_end_of_results_observed': terminal,
                     'status': 'error' if errors else 'end_observed' if terminal else 'bounded_or_unresolved',
                     'reported_total': latest[-1].get('reported_total'),
                     'latest_error': next((x['error'] for x in reversed(latest) if x.get('error')), '')})
    return rows


def reconcile(records, register, classification):
    by_doi = {normalize_doi(r.get('doi')): r for r in records if r.get('doi')}
    reg = {normalize_doi(r.get('doi')): r for r in register}
    classified = {normalize_doi(r['doi']): r for r in classification}
    rows = []
    for sentinel in SENTINELS:
        if sentinel['pathway'] == 'Electrochemical':
            continue  # issue #11's nine clinical landmarks; other controls remain in source audit
        doi = normalize_doi(sentinel['doi'])
        paper = by_doi.get(doi, {})
        queries = paper.get('source_queries') or []
        ordinary = [q for q in queries if not q.startswith('exact-doi:')]
        c = classified.get(doi, {})
        entry = reg.get(doi, {})
        rows.append({'doi': doi, 'expected_pathway': sentinel['pathway'], 'label': sentinel['label'],
                     'retrieved': bool(paper), 'source_databases': paper.get('source_databases', []),
                     'ordinary_query_recorded': bool(ordinary), 'ordinary_queries': ordinary,
                     'exact_doi_lookup_recorded': any(q.startswith('exact-doi:') for q in queries),
                     'retrieval_route': 'ordinary_query_recorded' if ordinary else 'exact_doi_only' if paper else 'missing',
                     'in_register': bool(entry), 'register_pathways': entry.get('pathways', []),
                     'classified_in_target_pathway': c.get('classified_in_target_pathway', False),
                     'exclusion_or_mismatch': c.get('exclusion_or_mismatch', 'classification not supplied'),
                     'independent_full_text_verified': False})
    return rows


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--artifact-dir', required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('--artifact-id', required=True)
    p.add_argument('--output', required=True)
    a=p.parse_args()
    src=pathlib.Path(a.artifact_dir);out=pathlib.Path(a.output);out.mkdir(parents=True, exist_ok=True)
    records=json.loads((src/'candidates.json').read_text())['records']
    queries=query_report(json.loads((src/'query_audit.json').read_text()))
    summary=json.loads((src/'summary.json').read_text())
    totals=collections.Counter()
    for row in queries:
        totals[row['status']]+=1
    result={'source_run_id':a.run_id, 'source_artifact_id':a.artifact_id,
            'source_generated_utc':summary.get('generated_utc'), 'candidate_records':len(records),
            'sha256':{name:hashlib.sha256((src/name).read_bytes()).hexdigest()
                      for name in ('candidates.json','query_audit.json','summary.json')},
            'query_group_status_counts':dict(totals),
            'historical_error_events':sum(x['historical_error_events'] for x in queries),
            'latest_attempt_error_events':sum(x['latest_attempt_error_events'] for x in queries),
            'independent_recall':None, 'scientific_release_permitted':False,
            'limitations':['Page resets infer attempts: original logs lack run IDs and event timestamps.',
                          'End-of-results only concerns that query/source, not field completeness.',
                          'Source queries show recorded routes, not source-specific causal attribution.',
                          'No independent human decisions or scientific sign-off supplied.'],
            'queries':queries}
    reg_path=src/'electrical_treatment_screening_queue.json'
    cls_path=src/'electrical_treatment_coverage_audit.json'
    if reg_path.exists() and cls_path.exists():
        reg=json.loads(reg_path.read_text());cls=json.loads(cls_path.read_text())
        rows=reconcile(records,reg['papers'],cls['sentinels'])
        result['clinical_sentinels']=rows
        with (out/'clinical_landmarks.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader()
            writer.writerows({k:'; '.join(v) if isinstance(v,list) else v for k,v in row.items()} for row in rows)
    (out/'release_evidence_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    with (out/'query_retry_queue.csv').open('w',newline='') as f:
        fields=['source','query','query_families','status','latest_attempt_last_page','reported_total','latest_error']
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader()
        for row in queries:
            if row['status']!='end_observed':
                w.writerow(dict(row,query_families='; '.join(row['query_families'])))
    print(json.dumps({k:v for k,v in result.items() if k not in ('queries','clinical_sentinels')},indent=2))
if __name__=='__main__':main()
