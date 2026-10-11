# Ranking reliability assessment — 11 October 2026

**Scientific status: NOT A VALIDATED WORLD RANKING.**

The Atlas is a useful discovery and evidence-tracing system, but numerical scientist positions are only provisional outputs of an incomplete title/abstract-based bibliographic model. **They should not be used in CVs, promotion, funding or institutional comparisons as verified worldwide positions.**

## Measured data-quality findings

The deployed audit for source run `38142034213` and the revised ranking code reports:

- **24,904** deduplicated search candidates, **1,516** machine-classified qualifying study candidates after corrections.
- **911** unique scored-work records across the published researcher comparison tables.
- **35** scored works explicitly typed as `article` by source metadata; **876** scored works with missing document-type metadata. Missing type is *not* proof a work is non-original; it prevents validation.
- **128** conflicting ORCID-to-OpenAlex identifier mappings observed in the broader corpus. These are conflicts requiring adjudication, *not* 128 proven incorrect authorships.
- **18** retrieval errors in the persisted bibliographic search audit.
- **135** groups with the same normalized title and year among the harvested records, which may include preprints, repositories, true duplicates or distinct versions.
- **0** independently full-text-screened publications.
- **0** known non-original document types counted, **0** DOI/PMID-less scored works and **0** exact-title duplicate evidence groups after the new gate was installed.

## Confirmed defects corrected in code

1. Europe's PMC byline metadata had sometimes overwritten article-linked OpenAlex author IDs and work-level affiliations. DOI-aware priority and corroborated ORCID matching now preserve this evidence.
2. Dissertation works, meeting materials, repository DOI copies and preprints were sometimes scored as journal originals. Known non-original record types and unsupported work identifiers are now excluded from scoring.
3. A publication title could be counted twice for the same academic if repository copies or duplicate DOI versions were indexed. Within-author exact-normalized title grouping now collapses them, retaining the stronger source record.
4. The therapy classifier missed wirefree conducting polymers and wireless electrical cell stimulation while sometimes admitting diagnostic or enabling-only work. Tests now cover these examples, although human review is still necessary.
5. A truncated bibliographic run could previously appear successful. The publication pipeline now rejects small, source-poor harvest artifacts before deployment.

## Remaining unresolved risks

- The search is not exhaustive or representative across ultrasound, magnetic, optical, radiofrequency and electrochemical therapeutic modalities.
- Database citations are internally normalized against the *harvested* works, not an independent field-normalized baseline.
- Title-level translation proxies do not measure clinical efficacy or technology readiness.
- Author first/last position is only a crude disciplinary proxy for intellectual leadership.
- Unknown document type and unresolved author IDs remain widespread.
- Human full-text review and duplicate-paper adjudication with at least two reviewers have not been completed.

## Release and validation conditions

A reproducible, publication-ready ranking requires a prospectively documented and saturation-tested search strategy; manual journal/publication-type verification; unique author ORCID/OpenAlex reconciliation with affiliation and original byline; fully recorded title/abstract and full-text dual-screen decisions; modality and career-stage normalization using defensible citation comparison cohorts; missing-data handling; sensitivity analyses; and independent sign-off.

**Automated tests passing means the implementation meets its specified checks. It does not independently establish that the scientific ranking is valid.**

Machine-readable evidence audit: [the published audit JSON](https://frankierawson-design.github.io/wireless-molecular-therapeutics-atlas/data/quality_audit.json).

Researcher positions in the Atlas remain explicitly exploratory. Users should cite paper-level evidence rather than an ordinal rank.
