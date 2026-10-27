# Issue #11 evidence audit — 22 October 2026

**Decision: public claims remain provisional; independent scientific release is blocked.**

Inspected main commit `19e18412954f8c55b658ecd0b6713bd1a85ecc09`, merged PRs #7/#10, the protocol and actual downloaded artifacts. This audit does not supply human review decisions.

| Frozen source | Broad electrical expansion | Active focused harvest |
|---|---:|---:|
| GitHub run | 38158350451 | 38212243948 |
| Artifact | 11709473620 | 11730302371 |
| Candidate records | 41,794 | 44,047 |
| Historical error events | 18 | 62 |
| Error events in latest inferred attempts | 0 | 44 |
| Source/query groups with end observed on latest inferred attempt | 77 | 58 |
| Source/query groups bounded or unresolved | 115 | 118 |

The logs accumulate prior harvests and lack run IDs/timestamps. Page-number resets infer the latest attempt. These are query/source-group diagnostics, not numbers of missed studies. A later successful first page does not prove complete pagination. Historical errors remain reported even when a later attempt succeeds. The 18 broad errors comprise sixteen 429s and two 504s; the focused log contains sixty 429s and two 504s cumulatively.

## Clinical landmark recovery

All nine clinical sentinel DOIs are present, in the broad register and machine-classified in their expected pathway. Six have an ordinary query recorded; three have **only exact DOI lookup** recorded:

- ESOPE: `10.1016/j.ejcsup.2006.08.002`
- Renal IRE: `10.1007/s00270-010-9964-1`
- DBS trial: `10.1056/nejmoa060281`

See [nine-row reconciliation](broad/clinical_landmarks.csv). Ordinary-query association does not prove independent retrieval: these are known calibration controls, and their recovery is not a recall estimate.

## Work completed

- Explicit broad, focused and legacy validation configurations; separate prospective amendment.
- Union of all calibration sentinel DOI exclusions, duplicate-reference and unknown-category checks.
- Dated independent review, full-text evidence, distinct adjudicator and reviewer-lock checks.
- Corpus/key hash and scope matching; numerical threshold checks; no automatic scientific release.
- Reproducible query audit and retry queues, preserving historical errors and pagination uncertainty.
- Focused A/B packets and coordinator templates prepared separately. There are 2,253 source records; no completed reviews, reference set, author audit or sign-off supplied. Blank evaluation correctly returns incomplete with no screening accuracy.
- A bounded diagnostic workflow retries three priority failed focused searches into a separate artifact. It does not deploy or replace the frozen corpus. Its outcome must be read from the actual workflow result, not assumed from the presence of this code.

## Still required

Information-specialist search review, ordinary-search recovery for the DOI-only landmarks, pagination/source coverage and citation-chasing saturation; independent dual screening and full-text adjudication; independently curated held-out reference sets; publisher-level author and modality reconciliation; duplicate-study adjudication; external normalization and rank/coverage uncertainty; independent scientific sign-off.

The current site's scope is narrower than issue #11. A focused pilot cannot close the broad-field gate. The original 352-record legacy pilot also cannot validate the active 44,047-record source. Preserve these distinctions in every public claim.

## Reproduce artifact diagnostics

```bash
python validation/audit_release_evidence.py --artifact-dir broad-harvest --run-id 38158350451 --artifact-id 11709473620 --output audit-broad
python validation/audit_release_evidence.py --artifact-dir focused-harvest --run-id 38212243948 --artifact-id 11730302371 --output audit-focused
```

See [prospective amendment](../../AMENDMENT_v1_1.md) for reviewer handoff and commands. The code and audit are reviewable work; they do not represent permission to promote validated rankings.
