# Atlas scientific-validation pilot — operational handoff

**Current state:** Pilot infrastructure working; reviewer and adjudication decisions not provided. **No international scientist rankings have been scientifically validated.**

## Frozen data and validation run

- The source is the exact 24,904-record harvest from successful GitHub Actions run [38142034213](https://github.com/frankierawson-design/wireless-molecular-therapeutics-atlas/actions/runs/38142034213).
- SHA-256 `candidates.json`: `ee79f92617423900368049f5d1e2bbd0c097da8eb424f8a2eef7276e92f2bd59`.
- The screening pilot has **352 records**: 142 electrochemical queue papers (census), 70 title-electrical excluded controls from 1,662, 70 remote-therapy non-electrical controls from 3,417, and 70 random background controls from 19,683. Sampling seed = 20261011.
- The stratified audit samples **cannot themselves establish recall for all missing literature**; an independent DOI reference set is needed.
- Researcher-ranking sensitivity is evaluated *conditionally* on the frozen dataset; moving ranks do not measure worldwide scientific influence.

## Roles and blinding

**Reviewer A:** Obtain only `independent-reviewer-A`. Fill original document type, remote energy application, modality, molecular mechanism, evidence tier, include/exclude/uncertain, reason, reviewer code, date and confidence.

**Reviewer B:** Independently obtain only `independent-reviewer-B`. Do not consult Reviewer A or published Atlas rank tables. Complete the same decisions without seeing the algorithm's classifications.

**Adjudicator/coordinator:** Retain the `adjudicator_key_DO_NOT_SHARE_WITH_REVIEWERS.csv` separately, and **only after both reviews are locked**, use publisher DOI records/full text to resolve disagreement and uncertainty. Supply author-identity verification and a separate independent multi-modality reference set.

*Operational blinding limitation:* public repository artifacts may be visible to users who deliberately open the coordinator's files; title searches can reveal authors. The files suppress machine decisions, bylines, identifiers and rank position, but are **not cryptographically secured**. For stronger independence, distribute reviewer files directly, restrict coordinator files to a private review workspace, and document who had access to the key.

## Evidence classification

- **T3:** functional therapeutic response demonstrated with stimulus-linked controls.
- **T2:** controlled molecular/ion/drug delivery or other molecular actuation demonstrated, without asserting therapeutic efficacy.
- **T1:** mechanistic or materials enabling result, no verified therapy or controlled delivery.
- **T0:** no qualifying remotely actuated therapeutic/molecular platform.
- **Uncertain:** insufficient evidence at title/abstract stage; require full text.

A paper with `include` at abstract stage is **provisional** until original publication status and full text confirm T2/T3. A working system may use ultrasound as *power delivery* but electrochemistry as the *transduction mechanism*: record both explicitly.

## Required workflow

1. Commit/freeze the code and corpus before reviewers see papers. Record reviewer declarations of independence and conflicts.
2. Give reviewer A and B **different downloaded files**. Both independently screen all assigned records and lock decision fields. Export their `Screening` worksheet as UTF-8 CSV with the **original exact header names**; never use a spreadsheet containing both reviewers' rows.
3. Check both reviewers provided distinct reviewer codes, date, decision, type, energy and rationale.
4. Give the adjudicator the full publisher references, masked model classifications until adjudication is complete, and document source URL/pages/evidence.
5. Populate `independent_reference_set_BLANK.csv` with 30–50 independently discovered original T2/T3 references in **each** modality, excluding the nine known software sentinels from the blind recall denominator. Record that the reference was chosen before the Atlas match lookup, and document verification.
6. Populate `author_identity_audit_BLANK.csv` using original publisher bylines/ORCID/institution. Sample beyond known named researchers.
7. Run the evaluation (exact command below). Blank material produces only `NOT_STARTED_OR_INCOMPLETE`, **never** fictitious recall or precision.
8. Report strata-weighted screening metrics, uncertainty, reviewer kappa, per-modality independent recall, unresolved identities and failure/stop criteria. The definitive rank release requires separate scientific sign-off.

## Commands (Python 3.12, standard library)

Using the frozen artifact extracted to `frozen/`, run:

```bash
python -m unittest discover -s tests -v
python validation/generate_review_packets.py --candidates frozen/candidates.json --output validation_output --negative-per-stratum 70 --seed 20261011
python validation/evaluate_reviews.py \
  --reviewer-a validation_output/reviewer_A_blinded.csv \
  --reviewer-b validation_output/reviewer_B_blinded.csv \
  --adjudicator-key validation_output/adjudicator_key_DO_NOT_SHARE_WITH_REVIEWERS.csv \
  --adjudications validation_output/adjudication_BLANK.csv \
  --reference-set validation_output/independent_reference_set_BLANK.csv \
  --author-audit validation_output/author_identity_audit_BLANK.csv \
  --candidates frozen/candidates.json \
  --output validation_output/validation_readiness_report.json
python validation/ranking_sensitivity.py \
  --rankings frozen/provisional_rankings.json \
  --output validation_output/exploratory_ranking_sensitivity.json
```

Replace the reviewer, adjudication, reference and author-input files with **completed and provenance-documented copies** before an actual validation evaluation.

## Verified first pilot CI result

[Workflow run](https://github.com/frankierawson-design/wireless-molecular-therapeutics-atlas/actions/runs/38146571304): 30 tests passed, blinded packets generated for all 142 queue records plus 210 controls, independent reviewer decisions 0/352, and **no** screening accuracy asserted.

In the frozen *older* candidate ranking (405 overall researchers), 382 people's overall ordinal positions moved by >10 across five predefined score-weight scenarios. Frankie's electrochemical ordinal position varied from 1 to 8 across those alternatives (baseline 4); these are *conditional methodological sensitivity results*, not new or confidence-validated positions. The ranking-corpus and eligibility issues remain unresolved.

## Protocol provenance and sign-off

Read [PROTOCOL_v1.md](PROTOCOL_v1.md). This protocol is **prospectively timestamped for future independent screening**, not a retrospectively registered completed systematic review. Document review start, amendments, reviewer conflicts, exclusion reasons, data-access limitations and final independent sign-off. A peer-reviewed research-methods report is a possible future output only when a real independent review has been completed.

## Privacy and masked review (11 October amendment)

The repository and GitHub Actions workflow are **public**. GitHub artifact labels such as `coordinator-only` are not access controls. The reviewed scientific cohort must be distributed carefully: each reviewer receives only their own A/B masked worksheet; neither receives the coordinator key or the other reviewer's completed file before decisions are locked. Future public workflows **do not upload the source-to-record identity key**. A coordinator can regenerate it locally from the immutable 24,904-record source and the documented SHA-256/seed using `validation/generate_review_packets.py`. Preserve that mapping outside the public repository. If a privately downloaded older artifact contains the key, treat it as a convenience copy for the coordinator, not evidence that GitHub restricted access to it. The previous key already appeared in public workflow artifacts, so strict masking for anyone who inspected them cannot be guaranteed; record reviewer access/knowledge as a protocol deviation. Titles and abstracts are still visible and may themselves reveal researcher identity. Describe the process as **independent masked reviewer assessment**, not truly double-blind review.
