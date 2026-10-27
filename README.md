# Electro-Mediated Pharmaceutics Atlas

An independent, reproducible candidate-literature map of research where an electrical or electrochemical process **mediates pharmaceutical action**: delivery, release, activation, uptake, drug resistance, intracellular trafficking or molecular therapeutic signalling.

**Status: provisional machine-screened comparison only; not an independently validated international league table.** A researcher's absence does not indicate lack of relevant publications.

## Scientific scope

An eligible original paper must show (1) defined electrical/electrochemical intervention and (2) an effect on a medicinal agent, drug-delivery process or bioactive therapeutic molecular mechanism. Wired and wireless approaches may qualify.

Examples: electrochemotherapy-mediated bleomycin or cisplatin uptake; AC modulation of drug sensitivity; electrically triggered delivery and release; bioelectronic redox-mediated medicine; electrically actuated therapeutic biomolecules.

Standalone TTFields combined with chemotherapy, generic electric-field oncology, cardiac ablation, DBS/VNS/SCS/tDCS, wound electrostimulation, diagnostic impedance, and electron-transport studies without pharmacological intervention are **not automatically scored**. Related mechanistic and enabling work can be shown separately with full citation provenance.

**The earlier broad electrical-treatment, ultrasound, magnetic, optical and radiofrequency ranking framework is superseded for the active public site.** Older tools remain in the repository for reproducibility.

## Researcher publication coverage

A missing original DOI must be distinguished from a legitimately excluded paper and from an author-matching error. The reference file at evidence/rawson_publisher_reference_dois.json contains six publisher-verified Rawson journal works. It is an **incomplete reference sample**, not a full bibliography. His published ORCID is 0000-0002-4872-8928.

The tool methods/audit_researcher_publications.py checks each reference DOI against harvested source work records and reports whether the named author has an ORCID on the same work. This method is reusable for other academics and does not artificially credit publications because they appear in a manual list.

A genuinely complete biography of publications requires comparison against an ORCID works export and university/Scopus bibliography, identification of duplicates and versions, adjudication of author collisions, and independent original-work eligibility screening.

## Data and automation

- methods/collect_literature.py: collects from OpenAlex and Europe PMC. Default query families now target electro-mediated pharmaceutical action, electrochemistry and electrochemotherapy, plus DOI sentinels.
- methods/electropharmaceutics_focus.py: scores only provisional original electro-mediated pharmaceutical intervention candidates, with all other treatment classes absent from active ranking output.
- methods/audit_researcher_publications.py: publisher-source bibliography sample audit; do not mistake the six-work sample for a complete career history.
- .github/workflows/electrical-therapies-expansion.yml: now named Electro-mediated pharmaceutics harvest; merges a substantial prior source corpus and performs the focused search.
- .github/workflows/publish-website.yml: regenerates focused rankings, candidate/context evidence register, Rawson audit and harvest provenance for the GitHub Pages website.

The source DOI reference tests improve recovery of known publications but do not establish comprehensive literature coverage or a validated scientific ranking.

## Provisional score, not independent validation

The experimental index uses 35% within-harvest/year citation percentile, 25% eligible candidate publication output, 20% first/last authorship, 10% title-level translation and 10% research activity. These weighting choices and author assignments require independent full-text, field-normalization, identity and sensitivity validation. Avoid citing numerical positions as worldwide rankings.

Research protocol: methods/SCREENING_AND_RANKING_PROTOCOL.md.
Public site: https://frankierawson-design.github.io/wireless-molecular-therapeutics-atlas/
Source repository: https://github.com/frankierawson-design/wireless-molecular-therapeutics-atlas


## 22 October release-gate audit

See [scope and validation amendment](validation/AMENDMENT_v1_1.md) and [artifact evidence audit](validation/audits/2026-10-22/README.md). Clinical sentinel recovery is 9/9 in the broad artifact, but three are DOI-only; independent recall and rankings remain unvalidated.
