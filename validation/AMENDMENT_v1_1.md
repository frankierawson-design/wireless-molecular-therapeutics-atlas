# Validation amendment v1.1 — 22 October 2026

Status: software safeguards and preparation, **not completed independent validation**. This dated amendment applies to future review using the updated tools. It neither retrospectively registers earlier analyses nor certifies that reviewers have not seen public results. Reviewers must declare prior exposure and conflicts before starting. Preserve the original v1 protocol and frozen baseline as historical records.

## Three separate scopes

| CLI scope | Intended question | Eligibility and reference categories |
|---|---|---|
| `legacy_wireless` | Historical 24,904-record pilot | Original remote-actuated T2–T3 studies; Electrochemical, Ultrasound, Magnetic, Optical, Radiofrequency, Hybrid. Not evidence for the current site. |
| `electrical_therapies` | Broad evidence map in issue #11 | Original biological/therapeutic electrical interventions, wired or wireless; TTFields, Electrochemotherapy, Electroporation, Neuromodulation, Electrical Stimulation, Electrochemical. Retain enabling evidence separately. |
| `electropharmaceutics` | Active public comparison | Original T2–T3 electrically mediated drug/bioactive-molecule action, wired or wireless. Reference category: Electro-Mediated Pharmaceutics. Standalone electrical treatment does not establish pharmaceutical mediation. |

Remote actuation is a descriptive field, **not an exclusion rule** for the latter two scopes. Physical power delivery, electrical modality and molecular transduction must be separately recorded in rationale/evidence fields. The active classifier's 2000–2026 date boundary and metadata requirements are machine rules to audit, not independent judgments of scientific relevance. Report errors by year and missing-metadata strata. An older eligible study excluded by the date rule is a documented scope difference or false negative, never silently discarded.

The broad scope requires 30–50 independently discovered eligible references **per pathway**. The focused scope initially requires 30–50 for its one declared category, spanning drug uptake/electrochemotherapy, controlled release/delivery and molecular actuation; report each mechanism subgroup and expand underrepresented groups. This is a preliminary reference-set target, not proof of complete coverage. All known software DOI controls are excluded from every independent recall denominator. Corpus-derived papers and the three diagnostic query retries are not an independent holdout.

## Frozen focused preparation

Source run 38212243948, artifact 11730302371, generated 12 October 2026. `candidates.json` SHA-256: `86519362e8e52083ddb1d18729f12ffe037199b0add51e54b7aae1ab0cf33323`. This is a separate 44,047-record snapshot; do not overwrite `frozen_snapshot.json` or combine its validation results with the old pilot.

Seed 20261022 yields 2,253 records: census of 2,043 focused candidate/context source records plus 70 sampled from each of three excluded strata. The historical `electro_queue_census` column name is retained for compatibility and means the selected scope's queue. Frame populations, weights and file hashes are in `audits/2026-10-22/focused/packet_manifest.json`.

Packets retain DOI-less source records using OpenAlex/PMID identity before title fallback. They do not equate same-title records with a verified unique study. Reviewers must reconcile duplicates and document corrected analysis weights before scientific estimates are released. The manifest count is source records, not unique eligible studies. New PMID fallback changes some identifiers relative to v1; do not mix versions of packets, keys or completed reviews.

## Reviewer evidence and refusal rules

- Distribute A and B separately. Keep the coordinator key private; public artifact labels are not access controls. At least one reviewer/adjudicator must be outside the evaluated researchers' networks. Record real declarations of independence, conflicts and exposure to earlier artifacts.
- Both reviewers supply dated decisions and reasons. Agreement alone is insufficient: record full-text evidence URL, page/quotation, original-type and DOI/PMID verification, and T2/T3 for inclusion. Unavailable full text remains unresolved. Full-text confirmation of excluded records is deliberately conservative for this validation sample.
- Discordance/uncertainty requires a distinct adjudicator, dated reviewer locks, an adjudication date after both locks, full-text provenance and exclusion reason when applicable.
- Evaluate against the packet manifest: corpus and coordinator-key hashes and scope must match. Never fabricate or infer independent decisions.
- Duplicate references, known sentinels and unknown reference categories cannot satisfy the independent reference gate. Screening recall ≥95%, precision ≥90%, reference recall ≥95%, minimum reference count and identity checks must all pass before a pilot passes its numerical checks. Report uncertainty intervals regardless of point thresholds.
- Passing pilot checks returns `PILOT_THRESHOLDS_MET_SIGNOFF_PENDING`, never a validated ranking. The software always reports `scientific_release_permitted: false`: source coverage/saturation, all ranked identities, external normalization, rank uncertainty and independent scientific sign-off remain separately required.

These checks verify supplied fields, not the honesty or independence of a person. The protocol's independent scientific sign-off is a human gate. Do not close issue #11 on a software test result.

## Reproduce focused preparation

Download the named artifact to `frozen-focused/`, then:

```bash
python validation/generate_review_packets.py --candidates frozen-focused/candidates.json --scope electropharmaceutics --expected-sha256 86519362e8e52083ddb1d18729f12ffe037199b0add51e54b7aae1ab0cf33323 --seed 20261022 --output packets
python validation/evaluate_reviews.py --scope electropharmaceutics --packet-manifest packets/packet_manifest.json --reviewer-a packets/reviewer_A_blinded.csv --reviewer-b packets/reviewer_B_blinded.csv --adjudicator-key packets/adjudicator_key_DO_NOT_SHARE_WITH_REVIEWERS.csv --adjudications packets/adjudication_BLANK.csv --reference-set packets/independent_reference_set_BLANK.csv --author-audit packets/author_identity_audit_BLANK.csv --candidates frozen-focused/candidates.json --output packets/readiness.json
```

Blank inputs must produce `NOT_STARTED_OR_INCOMPLETE`, no screening accuracy and no release permission. Completed reviewer files belong in a private coordinator workspace, not this repository.
