# T1 temporal GO label sets: methods, results and decisions

This document describes how the T1 data layer was built: what every step does, why each decision was made, and what came out. It is written so that each step can be checked against the specification in `README.md`. All numbers come from the final pipeline run (`scripts/build_t1.py`, build date 2026-11-04), and they match `reports/t1_report.md` and `data/processed/`.

Scope: the T0 knowledge snapshot, the T1 ground truth and the study-level strata. No models, baselines or metrics are built.

---

## 1. Summary

| Item | Value |
|---|---|
| T0 | GO ontology 2023-01-01; GOA human generated 2022-11-17 |
| T1 | GOA human generated 2026-07-28 (GO release 2026-08-05) |
| Protein universe | 18,221 reviewed human proteins |
| T0 training annotations (propagated) | 665,071 (protein, term) pairs on 12,145 proteins |
| Ground truth (propagated, new at T1) | 97,946 rows on 6,609 proteins; 83,616 rows in the strict subset |
| Strata | 5,565 dark, 9,003 intermediate, 3,628 well-studied, 25 unassigned |
| Go/no-go | **GO**: 577 unique dark proteins in NK+LK (threshold 200); 508 in the strict subset |
| Checks | 27 PASS, 0 FAIL, 1 ACCEPTED (T0 GOA lag of 45 days, accepted by the user) |
| Tests | 5 pytest tests pass |

---

## 2. Data sources

| Source | File | Release / date | Why this source |
|---|---|---|---|
| T0 annotations | `goa_human.gaf.gz` from GO release 2023-01-01 | GOA date-generated 2022-11-17 12:25, GAF 2.2 | EBI's GOA FTP was unreachable, from this environment and for the user. The GO Consortium release archive redistributes the GOA human file. |
| T1 annotations | `HUMAN-uniprot.gaf.gz` from GO release 2026-08-05 | GOA date-generated 2026-07-28 19:42, GAF 2.2 | The latest GO release. Recent releases no longer include `goa_human.gaf.gz`; `HUMAN-uniprot` is GOA's human file passed through with UniProt's own header. |
| Ontology | `go-basic.obo` from GO release 2023-01-01 | `data-version: releases/2023-01-01` | The CAFA5 snapshot, as specified. `go-basic` has no cross-namespace links, so propagation stays inside each namespace. |
| Proteins | UniProt REST, reviewed human, flat-file format | Downloaded 2026-11-04 | The TSV export has no secondary-accession field. The flat file has every required field: accession, secondary accessions, gene name, GeneID xref, and sequence version with its date (the `DT` line). |
| Literature | NCBI `gene2pubmed.gz` | Downloaded 2026-11-04 | As specified. |
| GeneID fallback | NCBI `gene2ensembl.gz` | Downloaded 2026-11-04 | Recovers GeneIDs that UniProt does not cross-reference (Section 7.3). |
| PMID boundary | NCBI E-utilities (esearch, esummary) | Queried 2026-11-04 | gene2pubmed has no dates (Section 7.1). |
| Protein-coding gene set | Human Protein Atlas v22 `proteinatlas.tsv.zip` | v22, December 2022 | Defines the protein-coding universe as it stood at T0 (Section 4). |
| TDL | Pharos GraphQL API | `pharos319` (current) | No pre-T0 TCRD release was obtainable, so the current TDL is used and labelled post-T0 (Section 8). |

Every raw file is cached in `data/raw/` and never downloaded again. Its URL, md5 and download date are recorded in `data/raw/manifest.json` and copied to `data/processed/provenance.json`.

### 2.1 Deviations from the specified sources

1. **GO Consortium copies instead of EBI files** (user decision). The T0 file is GOA's 2022-11-17 human file with PAINT IBA annotations merged in (61,323 rows). IBA is not an allowed evidence code, so the evidence filter removes those rows. Beyond that, GO only applies validation fixes, so this is essentially a copy of the GOA file.
2. **T0 GOA lag of 45 days, over the 6-week limit** (user accepted). The newest GOA human release available in the GO archive before 2023-01-01 is from 2022-11-17. Both the 2022-12-04 and 2023-01-01 GO releases contain that same file, and the next GOA release (2023-02-07) is after T0. Knowledge curated between 2022-11-17 and 2023-01-01 therefore counts as "new at T1". At most about 6 weeks of curation are affected, out of roughly 3.7 years between snapshots.
3. **The two files have different scopes.** `goa_human` (T0) covers the UniProt reference proteome, one protein per gene. `HUMAN-uniprot` (T1) covers every human UniProt entry. Sections 4 and 6.6 deal with the consequences.

---

## 3. Source checks (README step 1)

| Check | Result |
|---|---|
| Every gzip opens (read to the end, so the CRC is verified) and the HPA zip passes `testzip` | PASS for all 6 compressed files |
| T0 GOA generated on or before 2023-01-01 | PASS (2022-11-17) |
| T0 GOA within 42 days of T0 | ACCEPTED (45 days) |
| T1 GOA generated after T0 | PASS (2026-07-28) |
| Ontology data-version is `releases/2023-01-01` | PASS |

**How the GOA date is read.** The GO Consortium copies nest the upstream headers inside blocks separated by `!====` lines. The GOA release date is taken from the block that contains `generated-by: UniProt`. That gives the date the GOA file itself was generated, not the date GO repackaged it.

---

## 4. Protein universe

| Step | Before | After | Removed | Why |
|---|---|---|---|---|
| Reviewed (Swiss-Prot) human entries at T1 | 20,429 | 20,429 | 0 | As specified. |
| Sequence last modified on or before 2023-01-01 | 20,429 | 20,081 | 348 | Methods must predict for the sequence they would have seen at T0. Entries created after T0 are removed here too, because their sequence date is their creation date. |
| One entry per HPA v22 gene | 20,081 | 18,888 | 1,193 | User decision: keep only protein-coding genes, without duplicates. See below. |
| Present in the T0 GAF (any evidence code) | 18,888 | 18,467 | 421 | User decision. A protein missing from `goa_human` was outside that file's scope, which does not mean it had no annotations. Its T0 state is unknown, so it cannot be labelled NK. |
| Not an Ig/TR V/D/J/C gene segment | 18,467 | 18,221 | 246 | User decision. Gene segments are not proteins with their own function. They contributed 2 proteins to the ground truth but 232 to the dark stratum, which would make that stratum look padded with non-proteins. Pattern: `^(IG[HKL][VDJC]\|TR[ABDG][VDJC])`. |

**Choosing one entry per HPA gene.** HPA lists a gene's UniProt accessions in alphabetical order, so the first one listed is arbitrary. For example, for AKAP7 it lists O43687 first, while the T0 file has Q9P0M2. Taking the first entry would put a protein in the universe whose T0 annotations sit on a different entry, so it would look NK. The rule is therefore: keep the listed accession that appears in the T0 GAF; if none does, keep the first one listed. HPA accessions are mapped to current primary accessions first.

**How these filters fixed the scope problem.** The first run found 68 of 1,213 NK proteins missing from the T0 file altogether. Many were second products of a gene whose main product is in `goa_human`, such as CALCA P06881 (T0 has P01258) and MOCS2 O96033 (T0 has O96007). The HPA filter, the preference for the T0 entry and the T0-presence filter remove all such cases. Final scope check: 0 of 1,104 NK proteins are absent from the T0 file.

---

## 5. Annotation parsing and filtering (README step 2)

### 5.1 Parsing

- Header lines (`!`) are skipped, and each row is split on tabs. Both files are GAF 2.2. GAF 2.1 and 2.2 both have 17 columns, so a single column-count check covers both versions. **Check:** 0 malformed rows in T0 (626,136 rows) and in T1 (910,476 rows).
- **NOT qualifier:** a row is negated if `NOT` is one of the `|`-separated qualifier values. That covers 2.1 qualifiers (`NOT`, `NOT|contributes_to`) and 2.2 qualifiers (`NOT|enables`).
- **Taxon:** only the first taxon in column 13 is used. A second taxon means an interacting organism, not the organism of the annotated protein.

### 5.2 Filter steps (row counts)

| Step | T0 before → after | T1 before → after | Why |
|---|---|---|---|
| DB = UniProtKB and taxon 9606 | 626,136 → 626,136 | 910,476 → 862,694 | The T1 file also holds RNAcentral and ComplexPortal objects. |
| Evidence in {EXP, IDA, IPI, IMP, IGI, IEP} | → 337,902 | → 448,915 | As specified. The codes are a config list, and the high-throughput codes are off (`INCLUDE_HTP = False`). |
| Drop NOT | → 336,925 | → 447,749 | As specified. |
| Drop GO:0005515 (protein binding) | → 130,643 | → 169,630 | As specified: uninformative, and it inflates MF. It also comes back through propagation (Section 6.4). |
| Drop HPA-derived references | → 120,679 | → 161,204 | User decision; see 5.3. |
| Accession mapping | → 120,679 | → 161,204 | Isoform IDs collapse to the canonical accession, and secondary accessions map to current primaries. Both files already use canonical, current IDs in column 2: 0 isoform rows and 0 secondary rows needed mapping. Secondary accessions that map to more than one current entry (demerged entries) are dropped by user decision; none remained after the earlier filters. |
| In the Swiss-Prot universe | → 120,678 | → 161,204 | |
| Sequence filter | → 119,058 | → 158,841 | |
| Final protein universe (Section 4) | → 118,298 | → 157,444 | |

**Check:** every retained row is taxon 9606 and UniProtKB, in both files. PASS.

### 5.3 HPA-derived annotations

UniProt curates HPA immunofluorescence results into GO as IDA cellular-component annotations. Before removal, 110 of the 405 CC dark NK proteins (27%) were supported **only** by such rows. Another 20 CC LK and 72 CC PK dark proteins were HPA-only, and none in MF or BP. Leaving these rows in would mean that:
- the CC task partly measures "predict HPA localization", which overlaps with T2;
- the ground truth leaks into any model that uses HPA image features.

**Other routes for HPA data.** HPA results can also reach GO when UniProt cites an HPA paper by PMID. To check, I took 3,305 PMIDs from PubMed matching `"Lundberg E"[Author] OR "Uhlen M"[Author] OR "Human Protein Atlas"[Title/Abstract]` and intersected them with the PMIDs cited by UniProt-assigned CC IDA rows. Only 164 of 21,372 such rows at T0, and 224 of 27,084 at T1, cite one of these papers. The flagship subcellular atlas paper (Thul et al. 2017) is not cited at all; HPA cell-atlas data comes in through `GO_REF:0000052`. Only one paper contributes in a meaningful way: **PMID:31429579** (Pineau et al. 2019, HPA's antibody-based testis study), with 55 rows on 49 proteins, all new at T1. Before it was removed, it was the second most-cited PMID among CC dark NK rows. It is excluded, together with **PMID:22042635** (HPA's antibody-based profiling of chromosome 21; 3 rows), which carries the same kind of data. PMID:21399614 (a 2011 centrosome proteomics study that used HPA antibodies; 152 rows) is kept. It is not an HPA atlas paper, and its rows are the same at T0 and T1, so it adds nothing to the ground truth.

Final exclusion list (`EXCLUDED_REFERENCES`): `GO_REF:0000052`, `PMID:31429579`, `PMID:22042635`. It removes 9,964 T0 rows and 8,426 T1 rows.

**Why remove them from both snapshots.** Removing them from T1 only would be inconsistent: HPA localizations would still count as knowledge at T0, but no longer as discoveries at T1. With both removed, the benchmark consistently treats HPA localization as outside the knowledge it measures. One consequence is that a protein whose only T0 knowledge was an HPA localization now counts as NK.

---

## 6. Ontology mapping, propagation and ground truth (README steps 3 and 4)

### 6.1 Ontology

`go-basic.obo` (2023-01-01) is read with `obonet`, keeping obsolete terms so their `replaced_by` can be used. The propagation graph contains only non-obsolete terms and only `is_a` and `part_of` edges. Other relations, such as `regulates`, do not imply the parent function, so they are left out. Each term's namespace (MF, BP, CC) comes from the ontology.

### 6.2 Term mapping (applied to both snapshots)

Each GO ID in an annotation is mapped onto the T0 ontology in this order:
1. it is a current term: keep it;
2. it is an `alt_id`: map to the primary term;
3. it is obsolete with exactly one `replaced_by` that is a current term: map to the replacement. Several replacements would mean guessing which one the curator meant, so those are not mapped;
4. otherwise drop it: obsolete with no usable replacement, or not in the T0 ontology. Methods trained at T0 cannot predict terms that did not exist yet.

| Snapshot | Status | Rows | Distinct terms |
|---|---|---|---|
| T0 | current | 118,064 | 12,367 |
| T0 | obsolete, replaced | 228 | 4 |
| T0 | obsolete, dropped | 6 | 3 |
| T1 | current | 156,089 | 12,686 |
| T1 | obsolete, replaced | 3 | 2 |
| T1 | obsolete, dropped | 24 | 4 |
| T1 | **not in T0 ontology, dropped** | **1,328** | **305** |

No annotation in either snapshot used an `alt_id`. The mapping is still in place and is covered by the tests. In total 1,352 T1 rows (311 terms) are dropped.

### 6.3 Propagation

For each protein, its directly annotated terms are closed under their `is_a`/`part_of` ancestors. T0 goes from 89,530 direct (protein, term) pairs to 665,071 propagated pairs; T1 goes from 104,216 to 731,907.

**Check:** every propagated set is closed under its parents, verified on all proteins (12,145 at T0, 13,347 at T1). For each protein and each term, every non-excluded parent must be present. 0 missing parent links. PASS.

### 6.4 Terms removed after propagation

After propagation, these terms are removed from both the T0 annotations and the ground truth:
- **The three roots** (GO:0003674, GO:0008150, GO:0005575), as specified.
- **GO:0005515 (protein binding)** (user decision). It is removed from the direct annotations, but its children (for example *enzyme binding*) re-add it through propagation. Before this fix it appeared in 334 ground-truth rows and 4,450 T0 rows. It added no proteins to the test set, but it sat in the MF term sets.
- **GO:0005488 (binding)** (user decision). It is the parent of protein binding, one level below the MF root, and just as uninformative. Nothing further up was excluded.

**Check:** 0 rows with these terms in the T0 annotations or the ground truth. PASS.

### 6.5 Ground truth definition

For each protein and namespace, the ground truth is the set of T1 propagated terms minus the T0 propagated terms. This is the snapshot difference, not the GAF date column, which does not record when a function was first asserted.

Knowledge type (per namespace), as specified:
- **NK:** the protein has no experimental annotation in any namespace at T0 and gains terms in this namespace at T1.
- **LK:** the protein has T0 annotations in other namespaces but none in this one, and gains terms in this one.
- **PK:** the protein has T0 annotations in this namespace and gains new terms in it. The ground truth is the new terms only.

"Annotation at T0" means a non-empty propagated set after every filter above, including the removal of roots and binding terms.

### 6.6 Ground-truth refinements (user decisions)

| Step | Rows before | Rows after | Why |
|---|---|---|---|
| T1 propagated pairs, keep those new at T1 | 731,907 | 120,472 | Snapshot difference. |
| Remove pairs curated at T0 as TAS, NAS or IC (propagated) | 120,472 | 97,946 | About a third of the new rows with an old date were pairs already asserted at T0 by authors or curators (TAS/NAS/IC) and only upgraded to experimental evidence later. That knowledge was already curated at T0, and a method reading the full GOA could simply copy it. The T0 TAS/NAS/IC rows (not negated, on universe proteins) are term-mapped and propagated, and any ground-truth pair in that set is removed. Pairs that existed at T0 only as IEA or ISS are **kept**, because confirming a prediction is what the benchmark should reward. |
| Strict subset flag | 97,946 | 83,616 flagged | See 6.7. |

### 6.7 Strict subset (sensitivity analysis)

`ground_truth_t1.tsv` has a boolean `strict` column, which is not in the README's output spec; it was added by user decision. A row is strict when the pair is supported by at least one direct T1 row that is new at T1 and dated on or after 2022-11-17 (the T0 GOA release), counting propagation to ancestors.

**Why.** Because T0 and T1 come from different file pipelines, some "new" rows may reflect processing differences rather than new biology (Section 6.8). A date threshold would rely on the unreliable date column to define the main set. Instead, the main set keeps every row, and the strict subset is a sensitivity analysis. If method rankings agree on both sets, the pipeline question doesn't matter. If they differ, that is a finding worth reporting.

### 6.8 Pipeline-difference diagnostics

These are reported, not filtered on. The "delta" here means direct T1 rows whose (protein, term) was not known at T0: 27,824 rows.

- **Dated before 2022-11-17:** 4,294 rows (15.4%). Most are recent (2022: 1,121; 2021: 311; 2020: 398), with a tail back to 2003. An earlier analysis of these rows found:
  - about a third were TAS/NAS/IC-to-experimental upgrades, which are now removed (6.6);
  - the rest are absent from the T0 file entirely, mostly assigned by UniProt. They could be slow curation or pipeline differences, and the strict subset is there to tell the two apart.
- **Who assigned the new rows**, as a share of T0 rows versus delta rows:

  | Source | T0 share | Delta share |
  |---|---|---|
  | UniProt | 62.4% | 77.8% |
  | ComplexPortal | 3.2% | 6.6% |
  | BHF-UCL | 13.6% | 5.1% |
  | MGI | 4.2% | 1.9% |

- **Sources found only in the delta:** UOS_MCB (0.5% of delta rows; a curation group that has started contributing since T0) and LncRNAWiki (negligible).

### 6.9 Ground-truth checks

| Check | Result |
|---|---|
| No ground-truth term already existed at T0 for that protein (after propagation) | PASS (0 overlapping) |
| NK/LK/PK mutually exclusive per protein and namespace | PASS (0 conflicts) |
| No root terms | PASS |
| No protein binding or binding | PASS |
| No empty ground-truth sets | PASS (a protein and namespace only appear if they have rows) |
| No NK protein absent from the T0 file (scope) | PASS (0 of 1,104) |

### 6.10 Ground-truth results

Rows: BP 60,909, CC 22,310, MF 14,727; PK 61,679, NK 20,818, LK 15,449. Median new terms per protein and namespace: BP 12, CC 5, MF 3.

Protein–namespace sets per knowledge type. These are counted from `ground_truth_t1.tsv` and include every protein whatever its stratum. In the final build all of them have a stratum, so each cell equals dark + intermediate + well-studied in Section 9:

| | NK | LK | PK |
|---|---|---|---|
| MF | 537 | 571 | 2,078 |
| BP | 518 | 383 | 2,703 |
| CC | 733 | 563 | 2,340 |

---

## 7. Literature strata (README step 5)

### 7.1 PMID boundary

gene2pubmed has no dates, and PMIDs are assigned in order of entry. The boundary is the largest PMID whose Entrez date is on or before 2022-12-31.

**Method.** Run an esearch for `"YYYY/MM/DD"[EDAT]` for each of the 7 days up to 2022-12-31 (20,340 PMIDs). Then go through those PMIDs from the highest down, fetching esummary in batches of 200, and stop at the first one whose recorded Entrez date (`history`, `pubstatus = entrez`) is on or before the cutoff.

**Why not simply take the maximum.** The first version took the largest PMID in the date window and got PMID 42694844, which was entered in 2026. Records added years later can carry a back-dated `[EDAT]` index value, so they match a 2022 date search. The check on the boundary's entry date caught this. 160 such back-dated PMIDs were skipped.

**Result.** PMID **36585753**, entered 2022/12/30 23:53. **Check:** PASS.

### 7.2 Paper counts

| Step | Before | After | Why |
|---|---|---|---|
| gene2pubmed human (taxon 9606), distinct (gene, PMID) links | 3,348,186 | 3,348,186 | |
| Drop PMIDs linked to more than 100 human genes | 3,348,186 | 2,521,108 | Large-scale screens inflate counts without adding real knowledge of a protein (827,078 links removed). |
| Keep PMIDs ≤ 36585753 | 2,521,108 | 2,300,403 | Only papers from before T0. |

The count is the number of distinct PMIDs per GeneID. The more-than-100-genes rule uses the current gene2pubmed links, as specified.

### 7.3 GeneID to protein mapping

- **Primary source:** UniProt `DR GeneID` cross-references.
- **Fallback** (user request): if UniProt gives no GeneID, use the protein's HPA v22 Ensembl gene ID and map it through NCBI `gene2ensembl` (human). This recovered 36 proteins in the final universe, including USP11, PAX4, RIPK4, NLRP5, ZBTB3, TEX15 and DLGAP2.
- **Proteins with several GeneIDs** (87; for example gene copies such as histone and defensin clusters, or SMN1/SMN2): the paper count is the **maximum over the GeneIDs** (user decision). The copies share most papers, so the best-studied copy stands for the protein. A union of PMIDs would mostly re-count the same papers.
- **Unmapped:** 25 proteins (0.1%), mostly pseudogenes and MTRNR2L peptides, plus FOXO6, whose HPA Ensembl ID is not in gene2ensembl (left unmapped by user decision). Unmapped proteins get **no stratum**; they are not assumed to be dark. They are listed at the end of the report. **Check:** PASS.

### 7.4 Strata

| Stratum | Rule | Proteins |
|---|---|---|
| dark | fewer than 10 papers | 5,565 |
| intermediate | 10–100 papers | 9,003 |
| well-studied | more than 100 papers | 3,628 |
| none | no GeneID | 25 |

A protein with a GeneID but no gene2pubmed links gets 0 papers and is dark. This is deliberate: it is mapped, and it has no literature.

### 7.5 Spot check (for manual review)

| Gene | Accession | Papers before T0 | Stratum | TDL |
|---|---|---|---|---|
| TP53 | P04637 | 18,089 | well-studied | Tchem |
| BRCA1 | P38398 | 5,856 | well-studied | Tchem |
| LYSET (TMEM251) | Q8N6I4 | 4 | dark | Tdark |

LYSET's function was mostly characterised in 2022–2023, so being dark at T0 is what we'd expect. The report also lists 5 random proteins per stratum (seed 0).

---

## 8. Target development level (TDL)

The pre-T0 TCRD download host (`juniper.health.unm.edu`) was unreachable. As the README allows, the **current** Pharos TDL is used (dbVersion `pharos319`). It is labelled in `tdl_source` as post-T0, because it reflects knowledge gained after T0. TDL is a secondary annotation and is not used in any filter or stratum.

Pharos accessions are mapped to current primary accessions. Distribution: Tbio 11,980, Tdark 3,681, Tchem 1,863, Tclin 679, missing 18.

---

## 9. Test set summary

Proteins per namespace, knowledge type and stratum. The strict subset is in brackets. Values are dark / intermediate / well-studied.

| | NK | LK | PK |
|---|---|---|---|
| MF | 176 (160) / 308 (291) / 53 (48) | 71 (68) / 340 (316) / 160 (136) | 112 (96) / 910 (819) / 1,056 (969) |
| BP | 174 (160) / 290 (272) / 54 (45) | 64 (57) / 235 (214) / 84 (70) | 141 (127) / 1,199 (1,074) / 1,363 (1,219) |
| CC | 301 (261) / 377 (330) / 55 (50) | 72 (56) / 329 (281) / 162 (146) | 237 (186) / 1,245 (1,078) / 858 (783) |

No ground-truth protein lacks a stratum in the final build: the 25 unmapped proteins have no new annotations at T1. `test_set_summary.tsv` would list such proteins as `unassigned`, but it has no such rows.

**Go/no-go.** The rule counts dark proteins in NK+LK. They are counted as **unique proteins**, because summing over namespaces counts a protein up to three times.
- Full set: 577 unique dark proteins (858 protein–namespace pairs).
- Strict subset: 508 unique.

Both are well above the threshold of 200. **GO.**

Unique proteins per knowledge type (in any namespace): NK 1,104 (410 dark), LK 1,297 (167 dark), PK 4,940 (401 dark).

### 9.1 What NK means in practice

NK means "no experimental annotation **left after filtering** at T0". Because of the filters, NK includes proteins that did have experimental annotations at T0, but only of kinds the benchmark does not count as knowledge. `nk_origin` in `scripts/build_t1.py` goes back to the T0 GAF rows (allowed evidence codes, not negated) of every NK protein and classifies why they did not survive:

| Origin of NK protein | NK proteins | of which dark |
|---|---|---|
| Only protein binding / binding (GO:0005515, GO:0005488) | 455 | 173 |
| No experimental annotation at all | 401 | 171 |
| HPA-derived plus protein binding / binding only | 160 | 44 |
| Only HPA-derived (localization) | 87 | 22 |
| Obsolete or root term plus protein binding only | 1 | 0 |
| **Total** | **1,104** | **410** |

So only 36% of NK proteins (401) had no experimental annotation of any kind at T0. The other 64% had only "binds protein X" (an IPI to protein binding) and/or an HPA localization. Both follow from deliberate decisions: protein binding is uninformative (README), and HPA data is excluded to avoid overlap with T2 and leakage (5.3). They matter for interpreting results. Prediction tasks with an NK protein whose only T0 knowledge was a single interaction are not the same as ones on a truly uncharacterised protein. A per-origin breakdown of results (or restricting to the 401) is the natural answer if a reviewer asks; the table is in the report.

---

## 10. Tests (README step 6)

`tests/test_pipeline.py` uses a toy ontology (`tests/toy.obo`) and three proteins:
- **P1** is PK in MF: it has MF at T0, and its new T1 term comes in through an `alt_id`.
- **P2** is LK in BP: it is known in CC, and its new BP term comes in through an obsolete term with `replaced_by`.
- **P3** is NK in CC.

| Test | What it asserts |
|---|---|
| `test_alt_id_and_obsolete_mapping` | alt_id → primary; obsolete with `replaced_by` → replacement; obsolete without a replacement and terms missing from the ontology are dropped |
| `test_propagation_uses_is_a_and_part_of_only` | `is_a` and `part_of` propagate and `regulates` does not; the result is closed under parents |
| `test_roots_removed` | root terms are removed after propagation |
| `test_delta_contains_only_new_terms` | the ground truth contains only terms new at T1; no T0 term, no roots, no empty sets |
| `test_knowledge_types` | P1 → PK (MF), P2 → LK (BP), P3 → NK (CC); the types are mutually exclusive |

Result: 5 passed.

---

## 11. Outputs (`data/processed/`, TSV)

| File | Rows | Columns |
|---|---|---|
| `proteins.tsv` | 18,221 | accession, gene, entrez_id (`;`-joined if several), pmid_count_t0, stratum, tdl, tdl_source, has_exp_t0_mf/bp/cc |
| `annotations_t0.tsv` | 665,071 | accession, namespace, go_id: the propagated T0 training signal |
| `ground_truth_t1.tsv` | 97,946 | accession, namespace, go_id, knowledge_type, strict |
| `test_set_summary.tsv` | 27 | namespace, knowledge_type, stratum, proteins, proteins_strict |
| `provenance.json` | | every source (URL, md5, release, download date), GAF headers, ontology version, PMID boundary, accession-mapping stats, the full config, build date |

The report is in `reports/t1_report.md`.

---

## 12. Decision log

| # | Decision | Who decided | Reason |
|---|---|---|---|
| 1 | Use the GO Consortium archive copies of the GOA GAFs | User | EBI unreachable; the copies match GOA apart from IBA rows, which are filtered out anyway |
| 2 | Accept the 45-day T0 lag | User | No GOA human release between 2022-11-17 and T0 is obtainable |
| 3 | Protein-coding universe from HPA v22, one protein per gene | User | Remove non-coding entries and same-gene duplicates; v22 matches T0 |
| 4 | Per HPA gene, prefer the entry in the T0 GAF, else the first listed | Claude (after "no more questions") | HPA's order is alphabetical, so the first entry is arbitrary; the T0 entry keeps T0 and T1 on the same protein |
| 5 | Drop proteins absent from the T0 GAF | User | Their T0 state is unknown |
| 6 | Exclude Ig/TR gene segments | User | Not proteins with their own function; they pad the dark stratum |
| 7 | Remove HPA-derived references (`GO_REF:0000052`, PMID:31429579, PMID:22042635) from T0 and T1 | User suggestion, Claude decision | Overlaps with T2 and leaks into HPA-image models; removing from both snapshots keeps it consistent. The two PMIDs are HPA antibody papers cited by UniProt |
| 8 | Remove ground-truth pairs curated at T0 as TAS/NAS/IC; keep IEA/ISS | User | An evidence upgrade is not a discovery; confirming a prediction is |
| 9 | Add a `strict` flag (rows dated on or after T0 GOA) for a sensitivity analysis | User | Separates pipeline differences from real discoveries without using the date column to define the main set |
| 10 | Remove protein binding and binding after propagation | User | Children re-add them, and they are uninformative |
| 11 | Paper count = max over GeneIDs | User | Gene copies share papers |
| 12 | Drop demerged secondary accessions | User | Can't tell which entry the old annotation describes |
| 13 | GeneID fallback via HPA Ensembl and gene2ensembl; FOXO6 left unmapped | User | Real genes were missing GeneIDs; one protein doesn't matter |
| 14 | Go/no-go on unique proteins | User | Summing over namespaces counts proteins up to three times |
| 15 | PMID boundary: largest PMID with a verified Entrez date on or before the cutoff | Claude (bug fix found by a check) | `[EDAT]` matches back-dated records added later |
| 16 | UniProt flat file instead of TSV | Claude | The TSV export lacks secondary accessions |
| 17 | Current Pharos TDL, labelled post-T0 | README fallback | Pre-T0 TCRD not obtainable |

---

## 13. Known limitations

1. **The T0 snapshot is 45 days old.** Curation from 2022-11-17 to 2022-12-31 counts as new at T1.
2. **The pipeline differences are diagnosed, not removed.** 15.4% of new direct rows carry an earlier date. The strict subset is how to test whether this matters.
3. **gene2pubmed links are current.** Links added after T0 to papers from before T0 still count. This follows the specification, and the PMID boundary limits the papers but not the links.
4. **The PMID-order assumption.** The boundary relies on PMIDs being assigned in entry order. Back-dated records show this does not hold for every record, but the paper counts depend only on which PMIDs fall below the boundary. That is approximately right, because back-dated records have higher PMIDs and are excluded.
5. **TDL is post-T0** and must not be used as a T0 feature.
6. **The HPA reference filter covers `GO_REF:0000052` and the two HPA antibody-profiling PMIDs found in Section 5.3.** HPA antibodies used in other labs' papers are not removed; those are independent studies, not HPA atlas data.
7. **NK includes proteins with filtered-out T0 knowledge** (Section 9.1): 703 of 1,104 NK proteins had only protein-binding and/or HPA annotations at T0.
