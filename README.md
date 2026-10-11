# Wireless Molecular Therapeutics Atlas

An open, reproducible evidence map of research on externally activated molecular and cellular therapies.

**Status: Provisional machine-screened researcher rankings are published on the GitHub Pages website. No exhaustive or validated world-ranking claim is made.**

## Scope

Includes wireless energy input across electrical/inductive, ultrasound/acoustic, magnetic, optical, radiofrequency, and hybrid systems, provided a biological/therapeutic mechanism can be evidenced. Energy delivery and molecular transduction are recorded separately.

## Literature discovery

The workflow in `.github/workflows/literature-census.yml` retrieves candidate scholarly records from OpenAlex and Europe PMC, retains query provenance, deduplicates by DOI/PMID/title-year, and exports a reproducible screening register and search audit. A source API failure or page cap is logged, never silently called exhaustive.

Records are *candidates*, not included evidence. The resulting list requires human title/abstract screening, full-text review, document-type classification and author identity validation before rankings. Google Scholar profile counts alone do not identify the field-specific corpus.

## Run

From **Actions → Literature census → Run workflow**. A push to main also initiates one run. Inspect the run artifact `literature-candidates-and-audit`.

## Methodological safeguards

1. Candidate queries do not represent an exhaustive census; log the date, endpoint, query, pagination and errors.
2. De-duplicate and preserve all source identifiers and affiliations.
3. Screen full texts against pre-registered modality, transduction, and therapeutic endpoint criteria.
4. Verify authors with ORCID, OpenAlex and institution/DOI evidence; flag unresolved name collisions.
5. Reconcile cross-database citation counts and document field normalization before a scored ranking.
6. Do not publish numerical researcher ranks from an incomplete or unvalidated candidate harvest.

This research atlas is independent, not an official Stanford–Elsevier or institutional scientist ranking. Contributions, correction requests, and methodological feedback can be submitted as GitHub issues.


## Publish the website

The repository contains a lightweight responsive landing page. The original full interactive Atlas may be uploaded as **`atlas_site.zip`** (ZIP must contain `index.html` and `assets/`, `data/`, `methods/` at its root). The deployment workflow will unpack it automatically and publish the complete site.

One-time owner setup: **Settings → Pages → Build and deployment → Source: GitHub Actions**. Because GitHub's default workflow token cannot enable Pages itself, this must be set by a repository administrator. Then run **Actions → Publish atlas website → Run workflow**. The deployed Pages URL will be visible on the successful workflow run.

## Running and reviewing the literature search

**Actions → Literature census (candidate harvest) → Run workflow.** Choose a page limit. Artifacts are uploaded as `literature-candidates-and-audit`, including JSON/CSV and the dual-review screening form. The number of candidate records is *not* the number of eligible studies. A page cap or failed query prevents any completeness claim.

The dedicated **Scholarly API connectivity smoke test** workflow confirms Europe PMC/OpenAlex connectivity independently of collection.

## Current provisional rankings

The published website reads `data/provisional_rankings.json` and `data/provisional_rankings.csv`, generated on each deployment from the latest successful Europe PMC/OpenAlex candidate-harvest artifact. Rankings are supplied for overall, ultrasound, magnetic, optical, radiofrequency, electrochemical and hybrid pathways. A category with fewer than ten scored researchers shows evidence records without ordinal rankings.

The provisional score is 35% harvested-cohort citation percentiles, 25% machine-matched original-paper output, 20% first/last authorship, 10% title-based translational indicators, and 10% active publication years. The overall table requires 3 matched papers and pathway tables require 2. Source DOIs, OpenAlex IDs, included papers and score breakdowns are included. These are not independent full-text-verified, exhaustive, Scopus-harmonised or global field-normalised rankings. Some major researchers may be missing until identities and publication histories are reconciled. The site will automatically update when a successful new harvest completes.

## Author identity and affiliations (October 2026 upgrade)

* When a DOI occurs in both Europe PMC and OpenAlex, the importer retains OpenAlex's author-specific IDs, author order and per-paper institutional affiliations, rather than losing these when abbreviated Europe PMC bylines are ingested first.
* ORCID-only bylines can be resolved to an OpenAlex author ID only when a unique, source-linked ORCID–OpenAlex pair occurs in the harvested metadata. Author names by themselves are **never** sufficient to merge two people. Ambiguous mappings are counted in the output quality audit.
* The Institution column is **the most recent affiliation supported by work-level institutional metadata in the harvested corpus**, with the supporting publication year. It is not asserted to be an independently verified current appointment.
* Versioned preprints (bioRxiv/ChemRxiv) remain discoverable but are excluded from numerical scoring, to avoid artificially counting a preprint and journal paper as two separate research outputs.
* Expanded wireless-bioelectronic terms recognise molecular therapy publications that the initial narrow electrochemical classifier missed. We retain the machine-screening and uncertain-completeness labels until full independent literature review.
* The repository includes offline regression tests in `tests/test_identity_and_affiliations.py`. The Pages deployment will not proceed if an author identity, duplicate-paper or institutional-provenance test fails.

## Ranking data-quality audit

See [the 11 October 2026 quality and reliability report](methods/QUALITY_AND_RELIABILITY_REPORT.md) and the public [machine-readable quality audit](https://frankierawson-design.github.io/wireless-molecular-therapeutics-atlas/data/quality_audit.json). The automated candidate rankings must **not** be presented as confirmed worldwide scientist standings; 0 publications have been independently full-text screened. The Pages publication workflow now blocks known dissertations, other non-original publication types, DOI-less unverified works, and same-title double counting, with regression tests and a numerical quality audit. Passing software tests cannot validate the science.

## Known author-coverage issue: Robert J. Forster (11 October 2026)

The Atlas now has a named public correction case for Robert J. Forster (Dublin City University; ORCID `0000-0001-5079-3123`). Four papers are DOI sentinels: `10.1016/j.elecom.2024.107832` (review), `10.1039/d4cc03996c` (wireless polymer deposition), `10.1021/acs.analchem.4c04454` (wirefree deposition mechanism), and `10.1002/celc.202400506` (polymer deposition and modelling). The four authorship records are independently supported by publisher or university sources, but DOI retrieval into *this* corpus and the exact work-level machine author-ID assignment need checking separately.

The DOI audit independently reports: **not harvested**, **retrieved but not machine included**, or **machine included**; and **ORCID matched in work metadata**, **name-only match**, or **author absent/unresolved**. Review and enabling-only research is **not** automatically eligible for a therapeutic researcher score. A missing ranking position must **not** be interpreted as the scientist having no relevant work. No missing item is silently imputed and no synthetic rank is manufactured. Other unresolved author-matching issues remain in the quality audit.

## Expansion: therapeutic electric fields, neuromodulation and electrochemistry

**October 2026 development status: broadened automated literature capture; NOT a validated exhaustive census.**

The original Atlas was biased toward contactless/molecular drug delivery. This missed important electrical treatments, including those using wired electrodes. The new taxonomy explicitly separates:

- **TTFields** — tumour-treating intermediate-frequency alternating fields, oncology mechanisms and trials.
- **Electrochemotherapy** — pulses facilitating anticancer-drug transport (including ESOPE, bleomycin and cisplatin).
- **Electroporation** — reversible/irreversible electroporation, nanosecond pulses, H-FIRE, tumour and cardiac pulsed-field ablation, electrotransfer.
- **Neuromodulation** — DBS, VNS, spinal-cord stimulation, tDCS/tACS, peripheral and transcutaneous electrical nerve stimulation.
- **Electrical Stimulation** — cell and tissue electrical stimulation, wound healing, bone repair and rehabilitation.
- **Electrochemical** — electrode-mediated redox, remotely driven bipolar electrochemistry and electrochemical release.

These are related but **not mechanistically interchangeable**. Conventional wired delivery is permitted for the five new therapeutic intervention classes, but does not automatically make an intervention "electrochemical" or "hybrid". An article enters Hybrid only when independent physical energy families are evidenced. Eligibility requires human checks of article type, treatment delivery, molecular/cellular effect, mechanisms and actual intervention.

### Capture and reporting

The new [Electrical therapies expansion harvest](.github/workflows/electrical-therapies-expansion.yml) incrementally merges OpenAlex and Europe PMC retrieval for all five previously neglected pathways with a substantial baseline; exact DOI lookups check a documented reference set and all query failures or caps are recorded. The [electrical treatment coverage audit](methods/electrical_treatment_coverage_audit.py) discloses individual known-paper DOI recovery, machine-classification status, query errors and category-level candidate counts. Its zero independent full-text reviews and incomplete searches must not be interpreted as coverage validated.

**Release limitations:** DOI sentinel recall is a smoke test, not statistical recall or field saturation; a minimum number of candidates does not show worldwide coverage. The score weights were designed for an earlier narrower corpus; no overall comparison should be used professionally until prospective search saturation, field-specific recall/precision assessment, independent dual full-text screening, clinical/translational classification, ORCID author reconciliation and external field/year normalisation are finished. Expansion necessarily changes the comparison population and past ranks are not directly comparable.

Landmark DOI sentinels include EF-14 2015/2017 (TTFields), ESOPE 2006 (electrochemotherapy), first-in-man renal IRE and ADVENT PFA (electroporation), Deuschl et al. DBS 2006 and ELECT-tDCS 2017 (neuromodulation), and randomised electrical wound-healing studies. The exact bibliographic evidence is listed in the audit code, not hardcoded as scored researcher contributions.
