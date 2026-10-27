#!/usr/bin/env python3
"""Bounded diagnostics. Never replace the frozen corpus or authorize release."""
import argparse
import datetime
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'methods'))
from collect_literature import epmc_search, openalex_search


def run_diagnostic(report, limit=3, pages=6, source=None,
                   require_authenticated_pagination=False):
    families = {'electropharmaceutics', 'electrochemotherapy', 'electrochemical'}
    rows = [r for r in report['queries']
            if r['source'] in {'OpenAlex', 'Europe PMC'}
            and (source is None or r['source'] == source)
            and r['status'] != 'end_observed'
            and families.intersection(r['query_families'])]
    rows.sort(key=lambda r: (r['status'] != 'error',
                            'electropharmaceutics' not in r['query_families'],
                            r['query'], r['source']))
    selected = rows[:limit]
    credential_present = bool(os.environ.get('OPENALEX_API_KEY', '').strip())
    records, events, outcomes = {}, [], []
    status = 'NO_PRIORITY_QUERIES' if not selected else None
    if require_authenticated_pagination and not credential_present:
        status = 'BLOCKED_MISSING_OPENALEX_CREDENTIAL'
    if status is None:
        for row in selected:
            started = datetime.datetime.now(datetime.timezone.utc).isoformat()
            before = len(events)
            search = openalex_search if row['source'] == 'OpenAlex' else epmc_search
            search(row['query'], pages, 100, records, events)
            current = events[before:]
            for event in current:
                event['attempt_started_utc'] = started
            errors = any(e.get('error') for e in current)
            page_two = any(e.get('page') == 2 and not e.get('error') for e in current)
            end_observed = bool(current and not errors and current[-1].get('complete_for_query'))
            outcomes.append({'source': row['source'], 'query': row['query'],
                             'page_two_succeeded': page_two,
                             'end_observed': end_observed,
                             'status': 'SOURCE_ERROR' if errors else
                             'END_OBSERVED' if end_observed else 'BOUNDED_OR_UNRESOLVED'})
        if any(o['status'] == 'SOURCE_ERROR' for o in outcomes):
            status = 'SOURCE_ERROR'
        elif require_authenticated_pagination:
            status = ('PAGINATION_DIAGNOSTIC_PASSED' if
                      all(o['page_two_succeeded'] for o in outcomes) else
                      'PAGINATION_NOT_DEMONSTRATED')
        else:
            status = ('SELECTED_QUERIES_END_OBSERVED' if
                      all(o['end_observed'] for o in outcomes) else 'BOUNDED_OR_UNRESOLVED')
    result = {'status': status, 'selected_queries': selected, 'query_results': outcomes,
              'openalex_credential_present': credential_present,
              'authenticated_pagination_required': require_authenticated_pagination,
              'new_candidate_records': len(records),
              'error_events': sum(bool(e.get('error')) for e in events),
              'queries_with_end_observed': sum(o['end_observed'] for o in outcomes),
              'scientific_release_permitted': False,
              'note': 'Separate bounded diagnostic; page-two success is not complete retrieval, '
                      'search saturation, independent recall or scientific validation.'}
    return result, records, events


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--audit', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--limit', type=int, default=3)
    p.add_argument('--pages', type=int, default=6)
    p.add_argument('--source', choices=('OpenAlex', 'Europe PMC'))
    p.add_argument('--require-authenticated-pagination', action='store_true')
    a = p.parse_args()
    if not 1 <= a.limit <= 5 or not 1 <= a.pages <= 10:
        p.error('limit 1–5, pages 1–10')
    if a.require_authenticated_pagination and (a.source != 'OpenAlex' or a.pages < 2):
        p.error('authenticated pagination requires --source OpenAlex and --pages >= 2')
    result, records, events = run_diagnostic(
        json.loads(pathlib.Path(a.audit).read_text()), a.limit, a.pages, a.source,
        a.require_authenticated_pagination)
    out = pathlib.Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    payloads = {'query_audit.json': events,
                'candidate_delta.json': {'records': list(records.values()),
                                         'status': 'UNSCREENED_DIAGNOSTIC_DELTA'},
                'retry_summary.json': result}
    # Source exceptions can contain request URLs. Never publish the API key.
    credential = os.environ.get('OPENALEX_API_KEY', '')
    from urllib.parse import quote, quote_plus
    def safe_json(value):
        text = json.dumps(value, indent=2)
        if credential:
            for token in (credential, quote(credential, safe=''), quote_plus(credential)):
                text = text.replace(token, '[REDACTED]')
        return text + '\n'
    for name, value in payloads.items():
        (out / name).write_text(safe_json(value))
    print(safe_json(result), end='')
    return 0 if result['status'] in {
        'PAGINATION_DIAGNOSTIC_PASSED', 'SELECTED_QUERIES_END_OBSERVED'} else 2


if __name__ == '__main__':
    sys.exit(main())

