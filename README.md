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
