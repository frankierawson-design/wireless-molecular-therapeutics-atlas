# Systematic evidence and researcher-ranking protocol (draft 0.1)

**Status (11 October 2026):** prospective screening protocol. Database discovery and author disambiguation have not yet been validated. The public site must not represent candidate output as an exhaustive census.

## Review question

Who has contributed to primary research on **electrically, electromagnetically or otherwise externally actuated therapeutic cellular and molecular effects**, including TTFields, electrochemotherapy, electroporation, neuromodulation, tissue electrical stimulation, electrochemical redox therapies, ultrasound, magnetic, optical and hybrid technologies? Wired clinical interventions can qualify within the five expanded electrical-treatment categories. Remote actuation remains a specific requirement only where the stated category definition requires it.

## Eligibility

Inclusion at full-text review:
1. Primary research with documented external-field, electrical-stimulation or wirelessly delivered energy. Wired treatment modalities are eligible within their correctly labelled electrical-treatment categories.
2. Demonstrates a directly relevant molecular/cellular transduction mechanism or therapeutically relevant biological endpoint (e.g., controlled delivery, therapeutic cell modulation, tumour intervention).
3. Defines experimental system, stimulus, and endpoint with sufficient detail to classify evidence.
4. Peer-reviewed original study or clearly labelled preprint; retain preprints in a distinct stratum.

Exclusions from the **therapeutic research score**:
- Reviews/editorials (keep as reference expansion leads).
- Purely diagnostic sensors with no therapeutic biological intervention.
- Wired-only electrochemical redox mechanisms that do not meet the Wireless Electrochemical pathway's actuation criteria are excluded from that pathway, but genuine wired electrochemotherapy, electroporation, neuromodulation and tissue stimulation must remain eligible under their distinct treatment categories.
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

## Ranking methodology — provisional machine-screened results versus a verified ranking

Proposed scores within field-specific peer groups:
- 35% field- and year-normalised citation impact, capped sensitivity to single outliers.
- 25% relevant original research outputs in eligible therapy corpus.
- 20% independent authorship/leadership contribution (first, last, corresponding authorship where available; explicitly account for discipline differences).
- 10% experimentally evidenced therapeutic translation (clinical stage or independently corroborated in vivo/in vitro evidence; criteria published before scoring).
- 10% sustained field-specific research activity.

Each component must have published definitions, source snapshot dates, confidence/coverage grades, treatment of missing data and sensitivity analyses. Missing values are not automatically scored zero. Keep overall and modality-specific ranks separate. Overall ranks will use normalized within-modality measures to avoid privileging the largest publishing modality.

**Publication status:** The Atlas currently releases provisional, dataset-relative machine-screened positions for discovery and quality assurance, explicitly labelled as such. It does **not** claim a validated worldwide league table. A definitive field- or career-normalised scientist ranking remains withheld until eligibility, identities, citation denominators, and independent assessment are established. A provisional position must not be used as evidence that a researcher is higher- or lower-impact than researchers whose papers are incompletely harvested.

## Reproducibility and review status

Downloaded candidate records are available as GitHub Actions artifacts and require human screening. Submission of a DOI via GitHub Issues is not proof of eligibility or influence. Publish the final flow diagram and reproducibility scripts when screening is complete.

## Electrochemical expansion (11 October 2026)

The original five electrochemical searches severely underrepresented wireless bipolar electrochemistry, photo-driven organic ion pumps, wirefree controlled release, bioelectronic tumour interventions and remotely powered therapeutic pumps. A targeted expanded query family now covers those mechanisms with separate search provenance and capped per-query pagination; new records are merged into the broader deduplicated corpus. Abstract-index reconstruction improves recall when a paper's title alone lacks the therapeutic molecular mechanism.

**Mechanism-specific eligibility:** Conventional wired-only electrochemotherapy is now eligible for the separate Electrochemotherapy therapeutic pathway. The remote/contactless criterion remains for the Wireless Electrochemical redox pathway. Electrochemical sensors, analytical-only platforms and deposition papers without a therapeutic biological endpoint do not receive therapeutic score credit.

**Evidence tier labels:** Machine-screened papers are preliminarily flagged as biological therapeutic candidate, molecular-delivery platform candidate, or therapeutic-mechanism candidate. These labels are *not* verified efficacy claims. Reviews, title-only misleading matches and preprints are excluded from primary numerical scores under documented rules. Unresolved studies remain in a review queue.

**Sentinel retrieval audit:** Nine independently DOI-identified papers were selected prospectively to test coverage of wireless apoptosis, glioblastoma membrane-potential modulation, bipolar electrode biomolecular platforms, conducting polymer release, photovoltaic ion pumps and device-enabled dosing. A perspective/review and analytical impedance study serve as negative controls. The public DOI audit reports retrieved/missing and machine-included/excluded separately. A missed sentinel is a known search gap, not evidence the study does not exist.

**Provisional score in the live version:** 35% within-harvest, modality/year citation percentile; 25% relevant paper output; 20% first/last author proxy; 10% title-level translation proxy; 10% active publication years. This is **not** robust external field-normalisation or proof of clinical impact. Full source DOIs, evidence titles, recorded institutions and current screening audit must accompany any reported position. Ranking positions can change when query coverage improves.

**Next validation stage:** Independent title/abstract screening, sampled precision/recall review per modality, full-text adjudication, author cross-database reconciliation and defensible career-stage/field-normalised measures.

## Expanded electrical intervention literature (11 October 2026)

A coverage audit revealed that the historical wireless-focused search and its generic `electric.field` electrochemical classifier missed major established electrical therapies and could mislabel electric-field cancer treatment as electrochemistry.

The new **six-pathway** taxonomy is: (1) Tumour Treating Fields (TTFields), including alternating fields in oncology; (2) Electrochemotherapy, including electrode-assisted delivery of chemotherapy; (3) Electroporation and pulsed-field ablation, including reversible and irreversible pulses, H-FIRE, nsPEF and cardiac PFA; (4) Electrical neuromodulation, including DBS, VNS, SCS, tDCS, tACS and PNS; (5) Electrical stimulation of cells and tissues, including wound healing and regeneration; (6) Electrochemical redox and bipolar wireless systems.

**Exclusion hierarchy:** Identify original work and source DOI; retain pure reviews and abstracts only in the bibliography; distinguish clinical patient intervention, in vivo animal efficacy, in vitro mechanistic intervention, and enabling-device research. Label original articles with more than one treatment approach separately. Multiple terms describing electricity do not create a Hybrid classification unless genuinely independent energy-delivery families are used.

**Coverage audit:** The workflow fetches Europe PMC and OpenAlex publications from targeted search expressions and uses independent source-confirmed DOI sentinels for EF-14, ESOPE, IRE, pulsed-field cardiac ablation, deep-brain/tDCS neuromodulation and wound stimulation. The public `electrical_treatment_coverage_audit.json` reports for each treatment class the sentinel counts, machine-classified candidate count and query errors. It is a *discovery quality smoke test*, not scientific completeness or validated recall, and all full-text screening fields remain at zero pending assessment.

**A defensible claim of comprehensive coverage requires** independently designed synonyms and database searches, search-string sensitivity comparisons, page-cap and reported-total audits, prospective capture–recapture/novel-hit saturation analysis, systematic forward/backward citation expansion, duplicate adjudication, blinded dual article-type and intervention screening, per-category precision/recall estimates with confidence intervals, and ORCID + publisher and institution reconciliation. A pass of the DOI sentinel tests is insufficient.

**Ranking release:** Overall scores computed before and after this expansion have different comparison populations and should not be compared as changes in an investigator's actual scientific standing. Core and intervention-specific positions remain **exploratory** until independent screening and field/year/career-stage normalization have been established.
