# T1 GO label sets: build report

> **GO: 590 unique dark proteins in NK+LK in any namespace (threshold 200); 872 protein-namespace pairs; 521 unique in the strict subset.**

## Source versions and dates

| source | file | release/date | md5 | downloaded | url |
|---|---|---|---|---|---|
| gaf_t0 | goa_human_t0_go2023-01-01.gaf.gz | GO release 2023-01-01; GOA date-generated 2022-11-17 12:25 | 082ce90c7565a48721f403c73b23419c | 2026-11-04 | https://release.geneontology.org/2023-01-01/annotations/goa_human.gaf.gz |
| gaf_t1 | goa_human_t1_go2026-08-05.gaf.gz | GO release 2026-08-05; GOA date-generated 2026-07-28 19:42 | f74b40c53bdf8ed39d300a491eaf852d | 2026-11-04 | https://release.geneontology.org/2026-08-05/annotations/gaf/HUMAN-uniprot.gaf.gz |
| gene2ensembl | gene2ensembl.gz |  | 8ed7ecf8c9d560fd9fe2e0e9f9fbdebd | 2026-11-04 | https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2ensembl.gz |
| gene2pubmed | gene2pubmed.gz |  | c0435aa0c5564c4328fe984eb7a06767 | 2026-11-04 | https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2pubmed.gz |
| go_obo_t0 | go-basic_2023-01-01.obo | releases/2023-01-01 | 1208619d97a7bba65757c7c1fa4738d1 | 2026-11-04 | https://release.geneontology.org/2023-01-01/ontology/go-basic.obo |
| hpa_v22 | proteinatlas_v22.tsv.zip |  | 89601316ffe9c0972623f96d6372d5ac | 2026-11-04 | https://v22.proteinatlas.org/download/proteinatlas.tsv.zip |
| pharos_tdl | pharos_tdl.tsv | Pharos dbVersion pharos319 (current, post-T0) | ee6e04618be517a405eb83ee3dc8c142 | 2026-11-04 | https://pharos-api.ncats.io/graphql |
| uniprot_sprot_human | uniprot_sprot_human.txt.gz |  | cdfe580d07365aeb32dc4f2bec06bc6d | 2026-11-04 | https://rest.uniprot.org/uniprotkb/search?compressed=true&format=txt&size=500&query=%28organism_id%3A9606%29+AND+%28reviewed%3Atrue%29 |

## Notes and deviations

- EBI's GOA FTP was unreachable, so both GAFs come from the GO Consortium release archive (user decision). The T0 file is GOA human 2022-11-17 plus PAINT IBA rows; IBA is not an allowed evidence code, so those rows are filtered out.
- T0 GOA release is 45 days before T0, over the 6-week limit; accepted by the user.
- T0 file covers the UniProt reference proteome (goa_human); T1 file covers all UniProt human entries. Both are restricted to the same protein universe; see the scope check.
- Protein universe: one UniProt entry per HPA v22 gene (user decision). HPA lists accessions alphabetically, so the entry present in the T0 GAF is preferred, else the first listed. Proteins absent from the T0 GAF are dropped: their T0 state is unknown (user decision).
- Ig/TR V/D/J/C gene segments are excluded: they are not proteins with their own function (user decision).
- Ground-truth pairs already curated at T0 as TAS/NAS/IC (after propagation) are removed: an evidence upgrade is not a discovery. Pairs known only as IEA/ISS are kept (user decision).
- `strict` column in ground_truth_t1.tsv: pair supported by a T1 row dated on or after 2022-11-17. Report results on the full set and the strict subset (sensitivity analysis; user decision).
- Annotations with references ['GO_REF:0000052'] (HPA immunofluorescence) are removed from T0 and T1: they overlap with T2 and leak into models using HPA image features.
- GeneIDs missing from UniProt were recovered for 36 proteins via HPA Ensembl ID and NCBI gene2ensembl.
- Proteins with several GeneIDs take the max paper count over their GeneIDs (user decision).
- Secondary accessions that map to several current entries are dropped (user decision): T0 [], T1 [].
- The pre-T0 TCRD download host was unreachable, so TDL is the current Pharos value (Pharos dbVersion pharos319 (current, post-T0)) and reflects knowledge gained after T0.
- PMID boundary: 36585753 (Entrez date 2022/12/30 23:53).
- Proteins without a GeneID: 25 of 18221 (0.1%); listed at the end.

## Row counts per filter step

| table | step | before | after | removed |
|---|---|---|---|---|
| proteins | Swiss-Prot human at T1 | 20429 | 20429 | 0 |
| proteins | sequence last modified <= 2023-01-01 | 20429 | 20081 | 348 |
| proteins | HPA v22 gene, one protein per gene (T0-file entry preferred) | 20081 | 18888 | 1193 |
| proteins | present in the T0 GAF (any evidence) | 18888 | 18467 | 421 |
| proteins | not an Ig/TR gene segment | 18467 | 18221 | 246 |
| T0 | UniProtKB, taxon 9606 | 626136 | 626136 | 0 |
| T0 | evidence codes | 626136 | 337902 | 288234 |
| T0 | NOT qualifier | 337902 | 336925 | 977 |
| T0 | protein binding | 336925 | 130643 | 206282 |
| T0 | HPA-derived references | 130643 | 120682 | 9961 |
| T0 | accession mapping | 120682 | 120682 | 0 |
| T0 | Swiss-Prot universe | 120682 | 120681 | 1 |
| T0 | sequence filter | 120681 | 119061 | 1620 |
| T0 | HPA v22 gene set and same-gene filter | 119061 | 118301 | 760 |
| T1 | UniProtKB, taxon 9606 | 910476 | 862694 | 47782 |
| T1 | evidence codes | 862694 | 448915 | 413779 |
| T1 | NOT qualifier | 448915 | 447749 | 1166 |
| T1 | protein binding | 447749 | 169630 | 278119 |
| T1 | HPA-derived references | 169630 | 161262 | 8368 |
| T1 | accession mapping | 161262 | 161262 | 0 |
| T1 | Swiss-Prot universe | 161262 | 161262 | 0 |
| T1 | sequence filter | 161262 | 158899 | 2363 |
| T1 | HPA v22 gene set and same-gene filter | 158899 | 157491 | 1408 |
| T0 | GO term in T0 ontology (after alt_id/obsolete mapping) | 118301 | 118295 | 6 |
| T0 | propagated (protein, term) pairs, roots removed | 89533 | 675786 | -586253 |
| T1 | GO term in T0 ontology (after alt_id/obsolete mapping) | 157491 | 156139 | 1352 |
| T1 | propagated (protein, term) pairs, roots removed | 104254 | 743367 | -639113 |
| ground truth | T1 propagated pairs -> new at T1 | 743367 | 121476 | 621891 |
| ground truth | not curated at T0 as TAS/NAS/IC (propagated) | 121476 | 98850 | 22626 |
| ground truth | strict subset (annotation date >= 2022-11-17) | 98850 | 84387 | 14463 |
| gene2pubmed | taxon 9606, distinct links | 3348186 | 3348186 | 0 |
| gene2pubmed | PMIDs with <= 100 human genes | 3348186 | 2521108 | 827078 |
| gene2pubmed | PMID <= 36585753 | 2521108 | 2300403 | 220705 |

## GO term mapping onto the T0 ontology

| snapshot | status | rows | terms |
|---|---|---|---|
| T0 | current | 118067 | 12367 |
| T0 | obsolete_replaced | 228 | 4 |
| T0 | obsolete_unmapped | 6 | 3 |
| T1 | absent | 1328 | 305 |
| T1 | current | 156136 | 12686 |
| T1 | obsolete_replaced | 3 | 2 |
| T1 | obsolete_unmapped | 24 | 4 |

## Test set summary (proteins per namespace x knowledge type x stratum)

| namespace | knowledge_type | stratum | proteins | proteins_strict |
|---|---|---|---|---|
| MF | LK | dark | 71 | 68 |
| MF | LK | intermediate | 338 | 314 |
| MF | LK | well-studied | 158 | 134 |
| MF | NK | dark | 176 | 160 |
| MF | NK | intermediate | 308 | 291 |
| MF | NK | well-studied | 53 | 48 |
| MF | PK | dark | 112 | 96 |
| MF | PK | intermediate | 912 | 821 |
| MF | PK | well-studied | 1058 | 971 |
| BP | LK | dark | 64 | 57 |
| BP | LK | intermediate | 235 | 214 |
| BP | LK | well-studied | 85 | 71 |
| BP | NK | dark | 174 | 160 |
| BP | NK | intermediate | 290 | 272 |
| BP | NK | well-studied | 53 | 44 |
| BP | PK | dark | 141 | 127 |
| BP | PK | intermediate | 1199 | 1074 |
| BP | PK | well-studied | 1363 | 1219 |
| CC | LK | dark | 74 | 58 |
| CC | LK | intermediate | 329 | 281 |
| CC | LK | well-studied | 162 | 146 |
| CC | NK | dark | 313 | 273 |
| CC | NK | intermediate | 382 | 335 |
| CC | NK | well-studied | 55 | 50 |
| CC | PK | dark | 237 | 186 |
| CC | PK | intermediate | 1249 | 1082 |
| CC | PK | well-studied | 860 | 785 |

## Checks

| check | result | detail |
|---|---|---|
| gzip opens: goa_human_t0_go2023-01-01.gaf.gz | PASS | md5 082ce90c7565a48721f403c73b23419c |
| gzip opens: goa_human_t1_go2026-08-05.gaf.gz | PASS | md5 f74b40c53bdf8ed39d300a491eaf852d |
| gzip opens: gene2ensembl.gz | PASS | md5 8ed7ecf8c9d560fd9fe2e0e9f9fbdebd |
| gzip opens: gene2pubmed.gz | PASS | md5 c0435aa0c5564c4328fe984eb7a06767 |
| zip opens: proteinatlas_v22.tsv.zip | PASS | md5 89601316ffe9c0972623f96d6372d5ac |
| gzip opens: uniprot_sprot_human.txt.gz | PASS | md5 cdfe580d07365aeb32dc4f2bec06bc6d |
| T0 GOA release on or before 2023-01-01 | PASS | 2022-11-17 |
| T0 GOA release within 42 days of T0 | ACCEPTED | 2022-11-17 is 45 days before T0; accepted by user (EBI unreachable) |
| T1 GOA release after T0 | PASS | 2026-07-28 |
| GO ontology is the 2023-01-01 release | PASS | releases/2023-01-01 |
| T0 GAF 2.2 rows have 17 columns | PASS | 626136 rows read, 0 malformed |
| T1 GAF 2.2 rows have 17 columns | PASS | 910476 rows read, 0 malformed |
| One protein per HPA gene | PASS | 18221 proteins |
| T0 retained rows are taxon 9606 and UniProtKB | PASS | 118301 rows |
| T1 retained rows are taxon 9606 and UniProtKB | PASS | 157491 rows |
| T0 propagated sets closed under parents (all 12146 proteins) | PASS | 0 missing parent links |
| T1 propagated sets closed under parents (all 13347 proteins) | PASS | 0 missing parent links |
| Report mapped obsolete / alt_id / dropped T1 terms | PASS | T0 obsolete_replaced: 228 rows, 4 terms; T0 obsolete_unmapped: 6 rows, 3 terms; T1 absent: 1328 rows, 305 terms; T1 obsolete_replaced: 3 rows, 2 terms; T1 obsolete_unmapped: 24 rows, 4 terms |
| No ground-truth term existed at T0 (after propagation) | PASS | 0 overlapping |
| NK/LK/PK mutually exclusive per protein and namespace | PASS | 0 conflicts |
| No root terms in ground truth | PASS | 0 root rows |
| No empty ground-truth sets | PASS | 0 empty |
| No NK protein is absent from the T0 GAF (scope check) | PASS | 0 of 1119 NK proteins absent |
| PMID boundary entry date on or before 2022-12-31 | PASS | PMID 36585753, Entrez date 2022/12/30 23:53 |
| Proteins without GeneID get no stratum | PASS | 25 of 18221 (0.1%) unmapped |
| Spot-check genes found | PASS | TP53, BRCA1, LYSET |

## Spot check for manual review

| selection | accession | gene | entrez_id | pmid_count_t0 | stratum | tdl |
|---|---|---|---|---|---|---|
| named | Q8N6I4 | LYSET | 26175 | 4 | dark | Tdark |
| named | P04637 | TP53 | 7157 | 18089 | well-studied | Tchem |
| named | P38398 | BRCA1 | 672 | 5856 | well-studied | Tchem |
| random dark | Q8N7C7 | RNF148 | 378925 | 4 | dark | Tdark |
| random dark | Q8N4M1 | SLC44A3 | 126969 | 4 | dark | Tbio |
| random dark | A4D256 | CDC14C | 168448 | 4 | dark | Tdark |
| random dark | Q8TDN6 | BRIX1 | 55299 | 6 | dark | Tbio |
| random dark | Q8NH53 | OR52N1 | 79473 | 0 | dark | Tdark |
| random intermediate | Q6P3S1 | DENND1B | 163486 | 17 | intermediate | Tbio |
| random intermediate | Q6X4U4 | SOSTDC1 | 25928 | 56 | intermediate | Tbio |
| random intermediate | Q13003 | GRIK3 | 2899 | 35 | intermediate | Tclin |
| random intermediate | Q9ULR3 | PPM1H | 57460 | 18 | intermediate | Tbio |
| random intermediate | O95996 | APC2 | 10297 | 57 | intermediate | Tbio |
| random well-studied | Q9UMD9 | COL17A1 | 1308 | 124 | well-studied | Tbio |
| random well-studied | P04637 | TP53 | 7157 | 18089 | well-studied | Tchem |
| random well-studied | P51654 | GPC3 | 2719 | 538 | well-studied | Tbio |
| random well-studied | O75955 | FLOT1 | 10211 | 115 | well-studied | Tbio |
| random well-studied | Q8IZY2 | ABCA7 | 10347 | 127 | well-studied | Tbio |

## T0/T1 pipeline-difference checks

- Delta rows (direct T1 rows not known at T0): 27858.
- Delta rows with annotation date before the T0 GOA release (2022-11-17): 4294 (15.4%). By year: {2003: 1, 2004: 1, 2005: 10, 2006: 104, 2007: 54, 2008: 90, 2009: 170, 2010: 80, 2011: 193, 2012: 165, 2013: 128, 2014: 293, 2015: 135, 2016: 149, 2017: 556, 2018: 141, 2019: 194, 2020: 398, 2021: 311, 2022: 1121}.
- Sources present only in the delta, not in T0: ['LncRNAWiki', 'UOS_MCB'].

| assigned_by | T0 share | delta share |
|---|---|---|
| UniProt | 0.6244 | 0.7784 |
| ComplexPortal | 0.0319 | 0.0664 |
| BHF-UCL | 0.1361 | 0.0508 |
| MGI | 0.0417 | 0.0188 |
| FlyBase | 0.0081 | 0.0174 |
| ARUK-UCL | 0.0408 | 0.0173 |
| DisProt | 0.0036 | 0.0085 |
| IntAct | 0.0203 | 0.0083 |
| ParkinsonsUK-UCL | 0.0203 | 0.0069 |
| GO_Central | 0.0083 | 0.0063 |
| Reactome | 0.0049 | 0.0053 |
| UOS_MCB | 0.0 | 0.0052 |
| SynGO | 0.0039 | 0.0044 |
| HGNC-UCL | 0.0124 | 0.0026 |
| CAFA | 0.0172 | 0.0011 |

## Proteins without a GeneID mapping (no stratum)

<details><summary>25 proteins</summary>

P36268 (GGT2P), Q8IZF7 (ADGRF2P), Q92637 (FCGR1BP), G9CGD6 (CNK3/IPCEF1), Q92617 (NPIPB3), P0CJ72 (MTRNR2L5), Q5SY68 (S100A7L2), Q7RTY3 (PRSS45P), Q8WZ33 (MAFIP), P51861 (CDR1), A8MWA4 (ZNF705EP), A8MYZ6 (FOXO6), P0CJ71 (MTRNR2L4), P0CJ74 (MTRNR2L7), P0CJ75 (MTRNR2L8), S4R3Y5 (MTRNR2L11), D6RBM5 (USP17L23), P0CJ77 (MTRNR2L10), P0DMP1 (MTRNR2L12), Q8N8C0 (ZNF781), Q9BVW6 (SMIM2), P0CJ68 (MTRNR2L1), P0CJ70 (MTRNR2L3), P0CJ73 (MTRNR2L6), S4R3P1 (MTRNR2L13)

</details>
