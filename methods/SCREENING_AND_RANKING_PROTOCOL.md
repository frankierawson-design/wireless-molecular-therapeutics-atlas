# Systematic evidence and researcher-ranking protocol (draft 0.1)

**Status (11 October 2026):** prospective screening protocol. Database discovery and author disambiguation have not yet been validated. The public site must not represent candidate output as an exhaustive census.

## Review question

Who has contributed to peer-reviewed research on **therapeutic molecular or cellular effects remotely activated by externally delivered energy**, including electrical/inductive, ultrasound/acoustic, magnetic, optical, radiofrequency and hybrid systems?

## Eligibility

Inclusion at full-text review:
1. Primary research with documented externally applied or wirelessly delivered energy.
2. Demonstrates a directly relevant molecular/cellular transduction mechanism or therapeutically relevant biological endpoint (e.g., controlled delivery, therapeutic cell modulation, tumour intervention).
3. Defines experimental system, stimulus, and endpoint with sufficient detail to classify evidence.
4. Peer-reviewed original study or clearly labelled preprint; retain preprints in a distinct stratum.

Exclusions from the **therapeutic research score**:
- Reviews/editorials (keep as reference expansion leads).
- Purely diagnostic sensors with no therapeutic biological intervention.
- Conventional wired-only stimulation without remote actuation (retain as adjacent background).
- Non-therapeutic materials characterization or simulations without linked biological mechanism (retain as enabling evidence, not a demonstrated therapy).
- Generic radiation oncology or unrelated phototherapy studies without a qualifying molecular-actuation pathway.

## Search coverage

Europe PMC (including PubMed-indexed articles) and OpenAlex are public primary discovery sources. Supplement using Crossref DOI validation, institutional or Scopus exports where legitimately available, and citation-network expansion. Record date, exact query, year bounds, source API response totals, pagination, retrieval errors, deduplication and screening denominator.

The present GitHub Actions job has a **user-configurable page cap**. No output from this job alone can be described as comprehensive. Perform successive search-term refinement and backward/forward citation chasing; report saturation and unresolved database access constraints.

## Screening

- First pass: independent title/abstract reviewers; **include / exclude / uncertain**.
- Second pass: obtain eligible full texts; verify physical energy stimulus, transduction mechanism and therapeutic endpoint.
- Resolve discordant screening decisions and log exclusions.
- Preserve provenance of source abstracts, DOI links, reviewers and screening decisions.
- Retain modality labels for multimodal papers; do not infer electrochemistry from wireless delivery alone.

## Author identity reconciliation

Use validated ORCID where present; corroborate OpenAlex author identity with byline, institution and coauthor network, DOI/publisher page, and publication chronology. Name-only matches are **unverified**. Do not aggregate unrelated scholars who share names.

## Ranking methodology — withheld until validation

Proposed scores within field-specific peer groups:
- 35% field- and year-normalised citation impact, capped sensitivity to single outliers.
- 25% relevant original research outputs in eligible therapy corpus.
- 20% independent authorship/leadership contribution (first, last, corresponding authorship where available; explicitly account for discipline differences).
- 10% experimentally evidenced therapeutic translation (clinical stage or independently corroborated in vivo/in vitro evidence; criteria published before scoring).
- 10% sustained field-specific research activity.

Each component must have published definitions, source snapshot dates, confidence/coverage grades, treatment of missing data and sensitivity analyses. Missing values are not automatically scored zero. Keep overall and modality-specific ranks separate. Overall ranks will use normalized within-modality measures to avoid privileging the largest publishing modality.

**Do not release a numeric ranked list** until eligible literature is systematically screened, author identities verified, citation denominators documented and independent review completed. Per-researcher paper lists and evidence grades may be published before rankings.

## Reproducibility and review status

Downloaded candidate records are available as GitHub Actions artifacts and require human screening. Submission of a DOI via GitHub Issues is not proof of eligibility or influence. Publish the final flow diagram and reproducibility scripts when screening is complete.
