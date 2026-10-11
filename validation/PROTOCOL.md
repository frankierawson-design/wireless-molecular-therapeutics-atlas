# Validation Study V1 — Wireless Molecular Therapeutics Atlas

**Protocol version:** 1.0 — 2026-10-11. **Status:** implemented infrastructure; independent review NOT started.  
**Study:** systematic evidence mapping, author-identity validation and exploratory bibliometric measurement validation.  
**Scope:** electrochemical pilot first; ultrasound, magnetic, optical, radiofrequency and hybrid extension after pilot performance analysis.

## Prospective commitments and important limits

This protocol is fixed **after** multiple exploratory searches and known author-ranking defects. It is therefore **not a preregistration of the prior analyses**. It is the prospective plan for the *next* validation phase. Git history timestamps changes and amendments, but a public protocol is not equivalent to external protocol registration. Register its next frozen version (e.g. OSF) **before** reviewers see their assigned records and before final thresholds are evaluated. Record amendments with reason and date.

Freeze the harvest using `validation/frozen_snapshot.json`, including SHA-256 of the exact source files and the originating GitHub Actions run. Subsequent retrievals are distinct discovery cohorts; never replace the freeze in-place.

## Primary validation question

Can the Atlas retrieve and accurately classify qualifying remotely actuated molecular or cellular therapeutic original research across modalities, link papers to the correct researchers and support meaningful, reproducible comparison under specified missingness?

**Separate estimands:**

1. *Discovery recall*: fraction of independently assembled known-eligible reference publications retrieved; measure by modality.
2. *Screening precision*: fraction of machine-positive papers independently judged eligible for that particular tier.
3. *Screening false negatives*: verified eligible records in probability-sampled machine-negative strata. Estimate error by stratum and, where appropriate, survey-weighted estimates for the fixed harvested frame. This **cannot** measure papers absent from the databases; use independent reference-set recall for that.
4. *Identifier accuracy*: matched author-paper affiliations with source-linked ORCID/OpenAlex/publisher bylines.
5. *Ranking measurement stability*: rank distribution under alternative reasonable metric weights, citation sources, data completeness and uncertain eligibility. Stability alone is not correctness.

## Definitions and eligibility (fixed before reviewer decisions)

**Unit:** one distinct primary research work (a journal article or verified equivalent original peer-reviewed report) associated with a DOI/publisher page. A preprint and published version are one work and preprints are held in a separate stratum. Thesis, editorial, conference abstract, review, book, methods-only repository duplicate, data descriptor and conference-only report do **not** score as original intervention.

**Physical intervention:** distinguish remote energy input (e.g. ultrasound, light, magnetic, RF, field-coupled, wireless bipolar polarization) from localized molecular transduction (ion pumping, electrochemistry, molecular release, neuromodulation, membrane potential, etc.). Do not infer remote actuation from an electroactive material alone.

**Evidence levels:**
- **T — therapeutic biological effect demonstrated:** experimental biological modulation associated with an explicit plausible therapeutic endpoint, disease model or biological response measured under remote actuation.
- **P — remotely actuated molecular delivery/therapeutic platform:** drug or bioactive-molecule actuation/release shown, but therapeutic biological benefit not yet demonstrated.
- **E — enabling/methodological:** materials, transport, electrochemistry or simulation relevant to a possible future therapy without verified remote molecular therapeutic actuation.
- **D — diagnostics-only.**
- **R — review/non-original.**
- **U — uncertain pending full text or source verification.**

The primary therapy-effect outcome is T only. Report P separately; *do not* combine T and P without explicitly describing an expanded secondary estimand. E, D and R are not eligible for therapy-performance rankings. Multimodal classification may have multiple labels.

## Sampling and blinding

**Pilot:** review **all** records in the frozen electrochemical discovery queue. Additionally draw reproducible random samples of 70 plausible hard negatives and 70 remaining negatives from distinct, non-overlapping groups of the frozen corpus. Actual sample sizes are capped by stratum availability and recorded with inclusion probabilities. This is a **pilot**, not sufficient to assert fieldwide completeness.

Two independently assigned reviewers (A and B) receive CSVs with blind IDs, title, year and abstract but **no author names, journal, DOI, citation scores, previous machine status or rankings**. An identifiable title can still compromise blinding; document that limitation. Reviewers must not copy each other's decisions. No LLM-generated label counts as either human reviewer. Empty or blank worksheet cells indicate **not screened**, never exclude.

At title/abstract pass, reviewers code document type, remote/wired energy, modality, molecular mechanism, measured outcome, tier T/P/E/D/R/U, rationale and confidence. Full-text adjudication requires independent reading of the original paper. Capture full-text source and page/figure/section evidence; title-only review can only be preliminary.

Disagreement: independent adjudicator records final decision *with rationale* after seeing both review sheets; if unresolved, U. Report raw percentage agreement and unweighted Cohen's kappa (undefined if prevalence degenerates). Reviewer codes and decisions must remain attributable and immutable by version.

## Independent reference set and recall

At least 30–50 **independently selected known-relevant original works per modality**, balanced across historical periods, institutions, author networks, nations and venues. Obtain the set outside Atlas search outputs, e.g. domain expert submissions, handsearch of precommitted journal issues and citation chaining from external textbooks/reviews. Curators document a bibliographic source and eligibility rationale. Exclude already-identified Atlas sentinel papers from *held-out validation* (they may remain named calibration cases). Freeze gold DOIs before testing Atlas retrieval, and record disagreements.

\[
\mathrm{recall}_{m}= \frac{N(\text{gold works retrieved by Atlas},m)}{N(\text{eligible held-out gold works},m)}
\]
Use Wilson 95% intervals; if a modality has fewer than 30 agreed-on independent gold works, label recall inconclusive. **Proposed pilot go/no-go target:** point-estimate recall ≥95% in each modality *with uncertainty reported*; a point estimate alone cannot prove sufficient recall. Track missed publication families and amend searches only on a training cohort; re-evaluate on a *new* untouched holdout.

## Quantitative acceptance criteria (prospective **targets**, not validated achievements)

| Gate | Proposed criterion | Independent evidence needed |
|---|---|---|
| Search recall | ≥95% per-modality point estimate on ≥30 independent eligible held-out papers, plus 95% interval | externally curated frozen set |
| Screen precision | ≥90% primary-T precision on representative selected positives, with CI; test P separately | dual review and adjudication |
| Screening agreement | Cohen's κ ≥0.80 when defined; raw agreement reported | two independent reviewers |
| Original publication status | 100% of works to be scored verified via publisher or database document type and bibliographic source | article check with source provenance |
| Author identity | ≥99% independently verified correct paper-author links and **zero unresolved author identities in released ranking** | ORCID, publisher authorship, institutional and coauthor evidence |
| Duplicate integrity | zero known duplicate works or preprint/journal double-counts in scored set | identifier / version adjudication |
| Retrieval audit | source failures disclosed; no unanswered high-relevance query failure at release | query audit |
| Ranking robustness | threshold stability prespecified (e.g. ≥80% top-20 overlap and Spearman ρ ≥0.90 across plausible weights), with rank uncertainty intervals | alternative weighting and source cohorts |
| Final ranking readiness | all gates, independent sign-off and disclosed limitations | reviewers + protocol amendments |

With 30 reference papers, observing 29/30 is 96.7% but still has a relatively wide confidence interval. Do **not** imply a world ranking is proven from passing these numbers. Field normalization requires externally sourced year, work type and subject citation baselines, not within-harvest percentiles.

## Ranking sensitivity analysis

Calculate existing scores from the published components using baseline weights (35/25/20/10/10), citation-focused (55/20/15/5/5), output-focused (20/45/15/10/10), leadership-focused (25/15/40/10/10) and equal-weights (20/20/20/20/20). Compare Spearman rank correlation, median and 90th-percentile absolute percentile-rank shifts, top-20 overlap and the effects of excluding metadata-unverified papers. A bootstrap over papers conditional on the *incomplete* sample is a narrow model uncertainty estimate and must not be called international rank confidence.

Keep T-only, P-only and T+P exploratory comparisons **separate**. Never declare a scientist inferior solely because the Atlas missed their publications, or because their platform work is not a demonstrated clinical therapy.

## Release rules and responsibilities

- Scripts/tests and **blank** review packets can be published immediately.
- Two reviewers must independently fill worksheets. Do not backfill automatic labels into their decisions.
- A third adjudicator records disagreements and source evidence.
- Recalculate accuracy and rankings only when verified decisions exist.
- Release a *validated* comparison only after full original-work and author verification in its candidate population, a correctly sized reference recall assessment, methodological review, sensitivity disclosure and independent sign-off.
- Keep the current public rankings marked **exploratory**, not validated.
- Review must respect publisher copyright, lawful access and sensitive personal data; do not bulk distribute publisher full-text PDFs.

## Files

`validation/frozen_snapshot.json`: immutable published-input checksum and retrieval provenance.  
`validation/create_review_packets.py`: blinded review sheets, sample selection and reconciliation maps.  
`validation/evaluate_reviews.py`: strict inter-reviewer agreement, adjudication and Wilson intervals.  
`validation/evaluate_reference_recall.py`: independently frozen reference-set retrieval assessment.  
`validation/ranking_sensitivity.py`: alternative-weights model stress test.  
`validation/tests/`: synthetic regression tests of incomplete reviews, agreement, recall and stability.  
`.github/workflows/validation-pilot.yml`: GitHub Actions frozen-baseline reproducibility run.

No independent reviewer judgments have been made by generating these files.
