# Task: build the T1 temporal GO label sets for a human protein function benchmark

## Context
We are building a benchmark that evaluates protein function prediction on human
proteins, stratified by how well-studied each protein is. This task covers ONLY
the T1 data layer: the T0 knowledge snapshot, the T1 ground truth, and the
study-level strata. Do not build models, baselines, or evaluation metrics.

If a check fails, or a decision is not covered below, STOP and ask me.
Never silently work around a problem.

## Fixed decisions
- T0: GO ontology release 2023-01-01 (the CAFA5 snapshot), and the latest GOA
  human release generated on or before 2023-01-01. If that GOA release is more
  than 6 weeks before 2023-01-01, stop and ask.
- T1: the current GOA human release.
- Proteins: reviewed (Swiss-Prot) human entries (taxon 9606) at T1, excluding
  entries whose sequence was modified after 2023-01-01. Methods must predict for
  the same sequence they would have seen at T0.
- Evidence codes: EXP, IDA, IPI, IMP, IGI, IEP. Keep this as a config list;
  high-throughput codes (HTP, HDA, HMP, HGI, HEP) are off by default.
- Drop annotations with a NOT qualifier.
- Drop GO:0005515 (protein binding). It is uninformative and inflates the MF
  test set.
- Isoform IDs (P12345-2) collapse to the canonical accession. Secondary
  accessions in the T0 file map to current primary accessions.
- Propagate annotations with the T0 ontology, using is_a and part_of edges only.
  Map obsolete or alternative T1 terms via alt_id/replaced_by. Drop T1 terms
  that do not exist in the T0 ontology, because methods trained at T0 cannot
  predict them. Log how many are dropped.
- Never use the three root terms as ground truth.
- The test set is the snapshot difference between T0 and T1, not the GAF date
  column. That column is unreliable for when a function was first asserted.
- Knowledge types, defined per namespace (MF, BP, CC):
  - NK: no experimental annotations in any namespace at T0; gains annotations
    in this namespace at T1.
  - LK: has annotations in other namespaces at T0, none in this one; gains
    annotations in this namespace at T1.
  - PK: has annotations in this namespace at T0; gains new terms in this
    namespace at T1. Ground truth = new terms only.
- Study level: count PubMed papers per gene from NCBI gene2pubmed (taxon 9606).
  - Only count PMIDs with an Entrez date on or before 2022-12-31. Find the PMID
    boundary via E-utilities, because gene2pubmed has no dates and PMIDs are
    assigned in entry order.
  - Exclude PMIDs linked to more than 100 human genes. Large-scale screens
    inflate counts without adding real knowledge of a protein.
  - Map Entrez Gene IDs to UniProt accessions via UniProt.
  - Strata: dark (<10 papers), intermediate (10–100), well-studied (>100).
- Pharos target development level (TDL) is a secondary annotation only. Use a
  TCRD/Pharos release from before 2023-01-01 if obtainable. Otherwise use the
  current TDL, labelled as post-T0. The current TDL reflects knowledge gained
  after T0.

## Code requirements
- Python 3.11+. Use pandas, requests, networkx and obonet for the ontology, and
  pytest. No other dependencies without asking.
- Small, typed functions and plain readable syntax.
- Comments explain WHY a decision was made, briefly. Never comment on what the
  code does.
- Every step logs row counts before and after each filter.
- Raw downloads are cached and never re-downloaded if already present.

## Repo structure
```
README.md
requirements.txt
.gitignore              # data/raw/
src/darkbench/
    config.py           # dates, URLs, evidence codes, thresholds
    download.py
    ontology.py         # parse, alt_id/obsolete mapping, propagation
    annotations.py      # GAF parsing and filtering
    proteins.py         # Swiss-Prot universe, accession mapping, sequence filter
    literature.py       # PMID boundary, paper counts, strata
    ground_truth.py     # T0/T1 delta, NK/LK/PK
    report.py
scripts/build_t1.py     # runs the full pipeline end to end
tests/
data/raw/  data/processed/  reports/
```

## Steps and required checks

**1. Download**
- Fetch the T0 and T1 GOA human GAF files, the GO 2023-01-01 go-basic.obo,
  gene2pubmed, and the UniProt human Swiss-Prot table. The UniProt table needs
  these fields: accession, secondary accessions, gene name, GeneID xref,
  sequence version, date of last sequence modification.
- Check: each gzip opens. Record md5, URL and download date for every file.
- Check: read the GAF headers (date-generated, gaf-version) and the ontology
  data-version. Confirm the dates match the decisions above. Print them.

**2. Parse and filter annotations**
- Check: GAF row column counts are as expected for the file's GAF version.
  Handle both 2.1 and 2.2 qualifiers.
- Check: all retained rows are taxon 9606 and DB UniProtKB.
- Check: report row counts after each filter (evidence, NOT, protein binding,
  accession mapping, Swiss-Prot universe, sequence filter).

**3. Ontology and propagation**
- Check: every propagated annotation set is closed under its parents. Verify
  on all proteins.
- Check: report counts of mapped obsolete terms, alt_id terms, and dropped T1
  terms.

**4. Ground truth**
- Check: no ground truth term per protein and namespace already existed at T0
  (after propagation).
- Check: NK, LK and PK are mutually exclusive per protein and namespace.
- Check: there are no roots in the ground truth, and no empty ground truth sets.

**5. Literature strata**
- Check: print the PMID boundary along with that paper's entry date.
- Check: report the share of proteins without a GeneID mapping and list
  them. Unmapped proteins get no stratum; they are not assigned to dark.
- Check: print the stratum and paper count for TP53, BRCA1, TMEM251 (LYSET),
  and 5 random proteins per stratum, so I can review them by hand.

**6. Tests (pytest)**
- Write a toy ontology plus annotations with three proteins covering
  NK, LK and PK.
- Assert propagation, root removal, the delta, and knowledge-type assignment.
- Assert that alt_id/obsolete mapping works.

## Outputs (data/processed/, TSV)
- `proteins.tsv`: accession, gene, entrez_id, pmid_count_t0, stratum, tdl,
  tdl_source, and has_exp_t0 for each of mf, bp and cc.
- `annotations_t0.tsv`: propagated T0 annotations (accession, namespace, go_id).
  This is the training signal.
- `ground_truth_t1.tsv`: accession, namespace, go_id, knowledge_type.
- `test_set_summary.tsv`: protein counts per namespace × knowledge type ×
  stratum.
- `provenance.json`: every source file with URL, md5, release/date, and the
  config used.

## Report (reports/t1_report.md)
- Source versions and dates.
- Row-count tables for every filter step.
- The test set summary table.
- Results of every check above, as pass/fail.
- Go/no-go line: if dark proteins in NK+LK total fewer than 200 across all
  namespaces, flag it clearly at the top.
- The spot-check protein list for manual review.

Finish by running the full pipeline and the tests, then summarise the report
for me. Do not proceed to any further step.
