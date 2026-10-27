"""Regression checks for failed authentication and partial retrieval reporting."""
import contextlib
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'validation'))
import retry_priority_queries as retry
import collect_literature as collect


class RetrievalDiagnosticTests(unittest.TestCase):
    report = {'queries': [{'source': 'OpenAlex', 'query': 'drug delivery',
                          'status': 'error', 'query_families': ['electropharmaceutics']}]}

    def run_with_events(self, events):
        def search(query, pages, perpage, records, audit):
            audit.extend(dict(e, source='OpenAlex', query=query) for e in events)
        with patch.dict(os.environ, {'OPENALEX_API_KEY': 'test-only-key'}), \
                patch.object(retry, 'openalex_search', side_effect=search):
            return retry.run_diagnostic(self.report, limit=1, pages=2, source='OpenAlex',
                                        require_authenticated_pagination=True)[0]

    def test_missing_credential_makes_no_requests(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(retry, 'openalex_search') as search:
            result, records, events = retry.run_diagnostic(
                self.report, source='OpenAlex', require_authenticated_pagination=True)
        self.assertEqual(result['status'], 'BLOCKED_MISSING_OPENALEX_CREDENTIAL')
        search.assert_not_called()
        self.assertFalse(records or events or result['scientific_release_permitted'])

    def test_page_two_401_is_failure(self):
        result = self.run_with_events([
            {'page': 1, 'retrieved': 100, 'complete_for_query': False},
            {'page': 2, 'retrieved': 0, 'error': 'HTTP Error 401: Unauthorized'}])
        self.assertEqual(result['status'], 'SOURCE_ERROR')
        self.assertEqual(result['queries_with_end_observed'], 0)

    def test_two_pages_pass_diagnostic_without_claiming_completion(self):
        result = self.run_with_events([
            {'page': 1, 'retrieved': 100, 'complete_for_query': False},
            {'page': 2, 'retrieved': 100, 'complete_for_query': False}])
        self.assertEqual(result['status'], 'PAGINATION_DIAGNOSTIC_PASSED')
        self.assertEqual(result['queries_with_end_observed'], 0)
        self.assertFalse(result['scientific_release_permitted'])

    def test_short_first_page_does_not_demonstrate_page_two(self):
        result = self.run_with_events([
            {'page': 1, 'retrieved': 4, 'complete_for_query': True}])
        self.assertEqual(result['status'], 'PAGINATION_NOT_DEMONSTRATED')

    def test_page_two_endpoint_is_recorded(self):
        result = self.run_with_events([
            {'page': 1, 'retrieved': 100, 'complete_for_query': False},
            {'page': 2, 'retrieved': 0, 'complete_for_query': True}])
        self.assertEqual(result['status'], 'PAGINATION_DIAGNOSTIC_PASSED')
        self.assertEqual(result['queries_with_end_observed'], 1)

    def test_actual_search_forwards_credential_and_next_cursor(self):
        responses = [{'results': [{'id': 'W' + str(i), 'title': str(i)} for i in range(100)],
                      'meta': {'count': 101, 'next_cursor': 'page-two-cursor'}},
                     {'results': [{'id': 'W100', 'title': 'last'}],
                      'meta': {'count': 101, 'next_cursor': None}}]
        with patch.dict(os.environ, {'OPENALEX_API_KEY': 'test-only-key'}), \
                patch.object(collect, 'fetch', side_effect=responses) as fetch, \
                patch.object(collect.time, 'sleep'):
            result, records, events = retry.run_diagnostic(
                self.report, limit=1, pages=2, source='OpenAlex',
                require_authenticated_pagination=True)
        self.assertEqual(result['status'], 'PAGINATION_DIAGNOSTIC_PASSED')
        self.assertEqual(len(records), 101)
        self.assertEqual(fetch.call_args_list[1].args[1]['cursor'], 'page-two-cursor')
        self.assertEqual(fetch.call_args_list[1].args[1]['api_key'], 'test-only-key')

    def test_cli_preserves_failure_artifact_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'audit.json').write_text(json.dumps(self.report))
            args = ['retry', '--audit', str(root / 'audit.json'), '--output', str(root / 'out'),
                    '--source', 'OpenAlex', '--pages', '2', '--require-authenticated-pagination']
            with patch.dict(os.environ, {}, clear=True), patch.object(sys, 'argv', args), \
                    contextlib.redirect_stdout(io.StringIO()):
                code = retry.main()
            self.assertEqual(code, 2)
            self.assertEqual(json.loads((root / 'out/retry_summary.json').read_text())['status'],
                             'BLOCKED_MISSING_OPENALEX_CREDENTIAL')
            self.assertEqual(json.loads((root / 'out/query_audit.json').read_text()), [])

    def test_request_error_cannot_publish_credential(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'audit.json').write_text(json.dumps(self.report))
            args = ['retry', '--audit', str(root / 'audit.json'), '--output', str(root / 'out')]
            def search(query, pages, perpage, records, audit):
                audit.append({'source': 'OpenAlex', 'query': query, 'page': 1,
                              'error': 'request https://example.org/?api_key=test-only-key'})
            with patch.dict(os.environ, {'OPENALEX_API_KEY': 'test-only-key'}), \
                    patch.object(retry, 'openalex_search', side_effect=search), \
                    patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()) as stdout:
                code = retry.main()
            self.assertEqual(code, 2)
            self.assertNotIn('test-only-key', stdout.getvalue())
            for artifact in (root / 'out').iterdir():
                self.assertNotIn('test-only-key', artifact.read_text())


if __name__ == '__main__':
    unittest.main()
