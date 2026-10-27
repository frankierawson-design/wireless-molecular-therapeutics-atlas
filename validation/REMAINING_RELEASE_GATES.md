# Completion status and next check

Updated 27 October 2026. Scientific release remains blocked. Software tests,
calibration DOI recovery and a green diagnostic do not validate scientific claims.

## Implemented fixes

The public page describes researchers through machine-screened candidate papers
and no longer calls a focused-scope deployment validated. The retrieval diagnostic
now writes explicit blocked, failed, bounded or endpoint-observed results. The
workflow checks one priority OpenAlex query through page 2. It preserves diagnostic
artifacts and fails the job when authenticated pagination is not demonstrated.
The frozen corpus and public scores are not replaced by this diagnostic.

## Immediate external dependency

The last recorded live diagnostic, run 39861353895, had no OpenAlex API key,
returned page-one data and failed all three second pages. No authenticated success
has been established. Add a working OPENALEX_API_KEY as a repository Actions secret.
Do not paste it into a public issue, committed file or reviewer packet.

Run the Issue 11 release-gate audit workflow. Check retry_summary.json for
PAGINATION_DIAGNOSTIC_PASSED and the query audit for a successful second page.
This establishes credentialed pagination only. Then rerun the same query with
--pages 10 and inspect whether its endpoint was observed. Reaching a page cap
remains bounded retrieval. Broader completion requires a suitable continuation
strategy and all relevant source/query groups to be audited.

## Requirements that remain incomplete

- Review the search with an information specialist. Resolve pagination errors,
  ordinary-query discovery for the three DOI-only landmarks, source coverage,
  and explicitly defined citation-chasing/search saturation.
- Obtain real independent A/B reviews and adjudication using the frozen focused
  packet manifest and prospective amendment. Record conflicts and prior exposure.
  Missing full text remains unresolved. Existing packets contain source records,
  not verified unique eligible studies.
- Curate held-out reference studies independently of the Atlas and calibration
  DOI list. Evaluate precision, recall and uncertainty against the declared scope.
- Reconcile duplicate studies, publisher author identities, institutions,
  mechanisms, modalities and actual translation evidence.
- Evaluate external normalization and inclusion/ranking uncertainty. Freeze the
  resulting reproducible dataset and obtain independent scientific sign-off.

No human reviewer decisions, credentials, saturation results or sign-off have
been supplied by these changes. Keep issue #11 open. A focused-scope validation
cannot close its broad electrical-therapy scope.
