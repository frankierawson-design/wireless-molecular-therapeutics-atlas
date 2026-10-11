# Wireless Molecular Therapeutics Atlas

An open, reproducible evidence map of research on externally activated molecular and cellular therapies.

**Status: Research infrastructure under development. No global researcher rankings have been validated or published.**

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
