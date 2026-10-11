# Wireless Molecular Therapeutics Atlas — prospective validation protocol v1.0

**Frozen on:** 11 October 2026 (UTC). **Status:** protocol and review materials implemented; independent validation NOT yet performed.  
**Design:** systematic evidence map + blinded diagnostic-accuracy study + researcher identity audit + bibliometric stability study.  
**Primary endpoint:** eligibility-screening recall on an independent adjudicated reference set (not the nine search sentinels).  
**Source:** 24,904-record baseline GitHub Actions run [38142034213](https://github.com/frankierawson-design/wireless-molecular-therapeutics-atlas/actions/runs/38142034213), generated 2026-10-11T13:16:27.797980Z. SHA-256 of `candidates.json`: `ee79f92617423900368049f5d1e2bbd0c097da8eb424f8a2eef7276e92f2bd59`. `query_audit.json`: `254b783379e69a756f4568885fca141a5f7260925ce5fa45810900b38db270ef`. These files are **frozen**, not rewritten by later harvests.

## Primary scientific questions
1. How completely do systematic OpenAlex/Europe PMC queries retrieve independent known original papers in each of six therapeutic modalities?
2. How accurately does the automated algorithm distinguish **original remotely actuated molecular/cellular therapeutic research** from reviews, wired-only interventions, diagnostic sensors, enabling-only work and preprints?
3. How often is publication ownership assigned to the correct researcher's ORCID/OpenAlex identity, without splitting or erroneously merging authors?
4. Do individual positions remain comparable under alternative defensible bibliometric models and incomplete coverage?

## Scope and decision hierarchy (document ALL reasons)

An original eligible study must (a) be a verifiable original journal article; (b) demonstrate externally/remote-actuated energy at the biological intervention; (c) establish a mechanistic molecular or cellular transduction process or a therapeutic intervention; and (d) report adequate methods and evidence. Therapeutic evidence is **tiered**, not collapsed:
- **T3 biological therapy demonstrated:** cell/animal/human functional therapeutic effect is experimentally measured, with stimulus-linked controls.
- **T2 molecular delivery/actuation demonstrated:** quantified controlled drug/ion/neurotransmitter release, uptake, or molecular actuation; no therapeutic efficacy claim is inferred.
- **T1 mechanism/enabling only:** material deposition, electron-transfer studies, sensing, stimulation hardware, or proof-of-concept lacking validated release or functional response.
- **T0 out of scope:** conventional wired-only intervention, purely diagnostic, unrelated physical stimulus, or nontherapeutic process.

For *evidence mapping*, keep all T1–T3 in distinct strata, but include **only adjudicated T2–T3 original journal articles** in the proposed *primary molecular therapeutic comparison*. A separate T3-only sensitivity analysis tests whether allowing delivery-platform evidence changes positions. T1 is never silently upgraded to therapy. Reviews, meeting abstracts, dissertations, book chapters, preprints, retractions, and duplicates remain searchable and explicitly excluded from primary numerical comparisons. Record physical energy modality separately from transduction: ultrasound may power an electrochemical pump, but ultrasound is not automatically electrochemical actuation.

## Independent reference set for retrieval recall
- Obtain **30–50 independently identified DOI/PMID papers per modality**, spanning multiple regions, labs, journals, years and citation levels. Include papers **outside** the Atlas and unrelated to its seed DOI list; avoid deriving the set entirely from Atlas authors or search results.
- A third party (information specialist or independent reviewer) documents bibliographic selection and eligible full-text evidence **before looking at harvest membership**.
- Keep all nine existing DOI sentinels as software calibration controls, **not** as independent recall denominator.
- Calculate each modality's recall `retrieved independent eligible papers / independently adjudicated eligible reference papers` with Wilson 95% confidence intervals. A 95% point-estimate target applies to each modality; report confidence intervals and any deficient subgroup. With 30–50 papers, precision remains limited and >95% lower confidence bound may be infeasible.
- Review search syntax with PRESS, log date/endpoint/filters/page caps, and document failed API requests, alternative database export coverage, backward/forward citation chasing and new-study saturation.

## Screening pilot: electrochemical modality
- **Census** of every publication in `build_electrochemical_queue.collect()`, which currently contains 142 records, plus a *prespecified* reproducible stratified negative audit from papers the queue omitted.
- Negative stratum S1: all/stratified records with an electrical term in title but excluded by remote/therapy checks. S2: candidates with remote energy vocabulary outside electrochemical classifier. S3: reproducible random negative controls from other retrieved articles. Record exact population sizes and sampling probabilities in adjudicator key.
- Two reviewers evaluate titles and abstracts *independently*, without machine labels, author names or rank positions; decisions: `include`, `exclude`, `uncertain`. Each separately codes type (original/review/preprint/dissertation/conference/unknown), external energy modality, remote stimulus yes/no/uncertain, molecular mechanism yes/no/uncertain, highest therapeutic evidence tier, and reason codes.
- After independent initial decisions, a reviewer other than the first two adjudicates all disagreements and uncertainties using publisher records and full text. Record full-text identifier, DOI, dated citation, adjudicator, decision and reason; record unavailable full text as **unresolved**.
- Compute Cohen's kappa (observed and chance agreement) and observed agreement. **Do not** auto-adjudicate or use predicted labels as ground truth.
- Compare machine results to *adjudicated* decisions; report sensitivity, specificity, precision, false-negative rate and false-positive rate **with strata-weighted estimates**, 95% uncertainty intervals, per-stratum confusion matrices and excluded/uncertain denominators.
- Target screening recall ≥95%, precision ≥90% on **held-out** adjudicated records, not just model calibration. Provisional thresholds for this study; do not represent them as a universal standard. Any missed landmark or clearly relevant paper triggers a documented search/classifier amendment, then re-evaluation on a distinct holdout set.

## Author verification
- Draw a prespecified identity audit, enriched for generic surnames, ORCID conflicts, multi-institution careers, reviews with many authors, and authors near ranking cut-offs. Include Rawson and Forster only as **known-positive regression tests**, never as sole validation cohort.
- Verify each sampled paper-byline against publisher DOI, ORCID record, OpenAlex author ID, documented affiliation and coauthor history. Code `correct`, `wrong-person`, `split-identity`, `ambiguous`, `unverifiable`; keep ambiguous identities out of validated scoring.
- Proposed point accuracy ≥99% for *verified* author–paper links, with confidence intervals, and **zero unresolved identities in any final public ranked cohort**. Strong validation requires a considerably larger independently verified sample than 100; 0 errors in 100 observations does **not** prove ≥99% accuracy.

## Bibliometrics and sensitivity
- Compare citation-year cohorts against an independent field-normalized reference database; within-harvest percentile is *not* global field-normalization.
- Recompute alternatives: citation-only normalized indicators, full versus fractional article counts, leave-one-paper-out, modality-specific normalization, zero/discounted translational proxies, different author-leadership weightings, preprint removal, and publication-year shifts.
- Bootstrap papers **within researcher** to estimate conditional rank uncertainty. This does not capture selection bias; show separate coverage/screening uncertainty.
- Report Spearman rank correlation, Kendall concordance, top-k Jaccard and individual rank intervals across assumptions. **Do not** treat high model agreement as validity if the corpus remains incomplete.
- Explicit conditional release rule: no independently validated international scientist ranking until independent retrieval, dual screening and author identity gates are passed; performance is reported as interval/band when positions materially depend on modelling choices.

## Workflow stages and lock policy
1. **Freeze** source corpus, protocol version, PR commit SHA, methodology, software and code tests.
2. Generate reviewer A and reviewer B blinded screening sheets and sealed machine-adjudicator key. Store outputs separately.
3. Obtain written independent screening and third-party adjudication; do not backfill/guess decisions.
4. Compute preregistered performance estimates and full flow counts, including `uncertain` and missing evidence.
5. Lock eligible corpus and author identities; then assess external citation normalization and rank stability.
6. Conduct independent sign-off and disclose all exclusions, disagreements, potential conflicts, author affiliations and scoring sensitivity.

**Pre-registration:** This public GitHub protocol is a timestamped prospective record only relative to *future* independent reviews, and is not an externally registered protocol. Any amendments after review begins must be dated, explained, versioned and analyzed separately.

**Conflict management:** The Atlas developer/researcher is an evaluated scientist. Their team may maintain the software, but independent reviewers should decide inclusion and identity without seeing how a decision changes their rank. At least one reviewer/adjudicator should be independent of the Rawson and Forster research networks.

**Guidance:** PRISMA 2020 (systematic review reporting), PRISMA-S (search reporting), PRESS (peer review of electronic search strategies), and Leiden Manifesto / DORA principles (responsible research assessment). Standards inform transparency; this is not a PRISMA-compliant completed systematic review at present.

## Stop conditions
- Missing/changed frozen corpus checksum → stop.
- Reviewer sheets incomplete, duplicate reviewer identities, or adjudication missing → refuse accuracy claims.
- An independent DOI reference set includes previously known sentinel-only entries → report separately; do not count as blind recall validation.
- Unverified article type, ambiguous identity, or unstable ranks → no validated positional claims.
