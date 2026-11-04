# T1 GO label sets: build report

> **GO: 629 unique dark proteins in NK+LK in any namespace (threshold 200); 949 protein-namespace pairs.**

## Source versions and dates

| source | file | release/date | md5 | downloaded | url |
|---|---|---|---|---|---|
| gaf_t0 | goa_human_t0_go2023-01-01.gaf.gz | GO release 2023-01-01; GOA date-generated 2022-11-17 12:25 | 082ce90c7565a48721f403c73b23419c | 2026-11-04 | https://release.geneontology.org/2023-01-01/annotations/goa_human.gaf.gz |
| gaf_t1 | goa_human_t1_go2026-08-05.gaf.gz | GO release 2026-08-05; GOA date-generated 2026-07-28 19:42 | f74b40c53bdf8ed39d300a491eaf852d | 2026-11-04 | https://release.geneontology.org/2026-08-05/annotations/gaf/HUMAN-uniprot.gaf.gz |
| gene2pubmed | gene2pubmed.gz |  | c0435aa0c5564c4328fe984eb7a06767 | 2026-11-04 | https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2pubmed.gz |
| go_obo_t0 | go-basic_2023-01-01.obo | releases/2023-01-01 | 1208619d97a7bba65757c7c1fa4738d1 | 2026-11-04 | https://release.geneontology.org/2023-01-01/ontology/go-basic.obo |
| hpa_v22 | proteinatlas_v22.tsv.zip |  | 89601316ffe9c0972623f96d6372d5ac | 2026-11-04 | https://v22.proteinatlas.org/download/proteinatlas.tsv.zip |
| pharos_tdl | pharos_tdl.tsv | Pharos dbVersion pharos319 (current, post-T0) | ee6e04618be517a405eb83ee3dc8c142 | 2026-11-04 | https://pharos-api.ncats.io/graphql |
| uniprot_sprot_human | uniprot_sprot_human.txt.gz |  | cdfe580d07365aeb32dc4f2bec06bc6d | 2026-11-04 | https://rest.uniprot.org/uniprotkb/search?compressed=true&format=txt&size=500&query=%28organism_id%3A9606%29+AND+%28reviewed%3Atrue%29 |
| gene2ensembl | gene2ensembl.gz |  | 8ed7ecf8c9d560fd9fe2e0e9f9fbdebd | 2026-11-04 | https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2ensembl.gz |

## Notes and deviations

- EBI's GOA FTP was unreachable, so both GAFs come from the GO Consortium release archive (user decision). The T0 file is GOA human 2022-11-17 plus PAINT IBA rows; IBA is not an allowed evidence code, so those rows are filtered out.
- T0 GOA release is 45 days before T0, over the 6-week limit; accepted by the user.
- T0 file covers the UniProt reference proteome (goa_human); T1 file covers all UniProt human entries. Both are restricted to the same protein universe; see the scope check.
- Protein universe: one UniProt entry per HPA v22 gene (user decision). HPA lists accessions alphabetically, so the entry present in the T0 GAF is preferred, else the first listed. Proteins absent from the T0 GAF are dropped: their T0 state is unknown (user decision).
- Annotations with references ['GO_REF:0000052'] (HPA immunofluorescence) are removed from T0 and T1: they overlap with T2 and leak into models using HPA image features.
- GeneIDs missing from UniProt were recovered for 276 proteins via HPA Ensembl ID and NCBI gene2ensembl.
- Proteins with several GeneIDs take the max paper count over their GeneIDs (user decision).
- Secondary accessions that map to several current entries are dropped (user decision): T0 [], T1 [].
- The pre-T0 TCRD download host was unreachable, so TDL is the current Pharos value (Pharos dbVersion pharos319 (current, post-T0)) and reflects knowledge gained after T0.
- PMID boundary: 36585753 (Entrez date 2022/12/30 23:53).
- Proteins without a GeneID: 30 of 18467 (0.2%); listed at the end.

## Row counts per filter step

| table | step | before | after | removed |
|---|---|---|---|---|
| proteins | Swiss-Prot human at T1 | 20429 | 20429 | 0 |
| proteins | sequence last modified <= 2023-01-01 | 20429 | 20081 | 348 |
| proteins | HPA v22 gene, one protein per gene (T0-file entry preferred) | 20081 | 18888 | 1193 |
| proteins | present in the T0 GAF (any evidence) | 18888 | 18467 | 421 |
| T0 | UniProtKB, taxon 9606 | 626136 | 626136 | 0 |
| T0 | evidence codes | 626136 | 337902 | 288234 |
| T0 | NOT qualifier | 337902 | 336925 | 977 |
| T0 | protein binding | 336925 | 130643 | 206282 |
| T0 | HPA-derived references | 130643 | 120682 | 9961 |
| T0 | accession mapping | 120682 | 120682 | 0 |
| T0 | Swiss-Prot universe | 120682 | 120681 | 1 |
| T0 | sequence filter | 120681 | 119061 | 1620 |
| T0 | HPA v22 gene set and same-gene filter | 119061 | 118331 | 730 |
| T1 | UniProtKB, taxon 9606 | 910476 | 862694 | 47782 |
| T1 | evidence codes | 862694 | 448915 | 413779 |
| T1 | NOT qualifier | 448915 | 447749 | 1166 |
| T1 | protein binding | 447749 | 169630 | 278119 |
| T1 | HPA-derived references | 169630 | 161262 | 8368 |
| T1 | accession mapping | 161262 | 161262 | 0 |
| T1 | Swiss-Prot universe | 161262 | 161262 | 0 |
| T1 | sequence filter | 161262 | 158899 | 2363 |
| T1 | HPA v22 gene set and same-gene filter | 158899 | 157528 | 1371 |
| T0 | GO term in T0 ontology (after alt_id/obsolete mapping) | 118331 | 118325 | 6 |
| T0 | propagated (protein, term) pairs, roots removed | 89560 | 675959 | -586399 |
| T1 | GO term in T0 ontology (after alt_id/obsolete mapping) | 157528 | 156176 | 1352 |
| T1 | propagated (protein, term) pairs, roots removed | 104285 | 743542 | -639257 |
| ground truth | T1 propagated pairs -> new at T1 | 743542 | 121499 | 622043 |
| gene2pubmed | taxon 9606, distinct links | 3348186 | 3348186 | 0 |
| gene2pubmed | PMIDs with <= 100 human genes | 3348186 | 2521108 | 827078 |
| gene2pubmed | PMID <= 36585753 | 2521108 | 2300403 | 220705 |

## GO term mapping onto the T0 ontology

| snapshot | status | rows | terms |
|---|---|---|---|
| T0 | current | 118097 | 12368 |
| T0 | obsolete_replaced | 228 | 4 |
| T0 | obsolete_unmapped | 6 | 3 |
| T1 | absent | 1328 | 305 |
| T1 | current | 156173 | 12687 |
| T1 | obsolete_replaced | 3 | 2 |
| T1 | obsolete_unmapped | 24 | 4 |

## Test set summary (proteins per namespace x knowledge type x stratum)

| namespace | knowledge_type | stratum | proteins |
|---|---|---|---|
| MF | LK | dark | 74 |
| MF | LK | intermediate | 374 |
| MF | LK | well-studied | 167 |
| MF | NK | dark | 193 |
| MF | NK | intermediate | 352 |
| MF | NK | well-studied | 71 |
| MF | PK | dark | 117 |
| MF | PK | intermediate | 965 |
| MF | PK | well-studied | 1122 |
| BP | LK | dark | 73 |
| BP | LK | intermediate | 258 |
| BP | LK | well-studied | 90 |
| BP | NK | dark | 182 |
| BP | NK | intermediate | 302 |
| BP | NK | well-studied | 57 |
| BP | PK | dark | 143 |
| BP | PK | intermediate | 1267 |
| BP | PK | well-studied | 1428 |
| CC | LK | dark | 89 |
| CC | LK | intermediate | 457 |
| CC | LK | well-studied | 269 |
| CC | NK | dark | 338 |
| CC | NK | intermediate | 496 |
| CC | NK | well-studied | 93 |
| CC | PK | dark | 249 |
| CC | PK | intermediate | 1460 |
| CC | PK | well-studied | 1029 |

## Checks

| check | result | detail |
|---|---|---|
| gzip opens: goa_human_t0_go2023-01-01.gaf.gz | PASS | md5 082ce90c7565a48721f403c73b23419c |
| gzip opens: goa_human_t1_go2026-08-05.gaf.gz | PASS | md5 f74b40c53bdf8ed39d300a491eaf852d |
| gzip opens: gene2pubmed.gz | PASS | md5 c0435aa0c5564c4328fe984eb7a06767 |
| zip opens: proteinatlas_v22.tsv.zip | PASS | md5 89601316ffe9c0972623f96d6372d5ac |
| gzip opens: uniprot_sprot_human.txt.gz | PASS | md5 cdfe580d07365aeb32dc4f2bec06bc6d |
| gzip opens: gene2ensembl.gz | PASS | md5 8ed7ecf8c9d560fd9fe2e0e9f9fbdebd |
| T0 GOA release on or before 2023-01-01 | PASS | 2022-11-17 |
| T0 GOA release within 42 days of T0 | ACCEPTED | 2022-11-17 is 45 days before T0; accepted by user (EBI unreachable) |
| T1 GOA release after T0 | PASS | 2026-07-28 |
| GO ontology is the 2023-01-01 release | PASS | releases/2023-01-01 |
| T0 GAF 2.2 rows have 17 columns | PASS | 626136 rows read, 0 malformed |
| T1 GAF 2.2 rows have 17 columns | PASS | 910476 rows read, 0 malformed |
| One protein per HPA gene | PASS | 18467 proteins |
| T0 retained rows are taxon 9606 and UniProtKB | PASS | 118331 rows |
| T1 retained rows are taxon 9606 and UniProtKB | PASS | 157528 rows |
| T0 propagated sets closed under parents (all 12152 proteins) | PASS | 0 missing parent links |
| T1 propagated sets closed under parents (all 13353 proteins) | PASS | 0 missing parent links |
| Report mapped obsolete / alt_id / dropped T1 terms | PASS | T0 obsolete_replaced: 228 rows, 4 terms; T0 obsolete_unmapped: 6 rows, 3 terms; T1 absent: 1328 rows, 305 terms; T1 obsolete_replaced: 3 rows, 2 terms; T1 obsolete_unmapped: 24 rows, 4 terms |
| No ground-truth term existed at T0 (after propagation) | PASS | 0 overlapping |
| NK/LK/PK mutually exclusive per protein and namespace | PASS | 0 conflicts |
| No root terms in ground truth | PASS | 0 root rows |
| No empty ground-truth sets | PASS | 0 empty |
| No NK protein is absent from the T0 GAF (scope check) | PASS | 0 of 1227 NK proteins absent |
| PMID boundary entry date on or before 2022-12-31 | PASS | PMID 36585753, Entrez date 2022/12/30 23:53 |
| Proteins without GeneID get no stratum | PASS | 30 of 18467 (0.2%) unmapped |
| Spot-check genes found | PASS | TP53, BRCA1, LYSET |

## Spot check for manual review

| selection | accession | gene | entrez_id | pmid_count_t0 | stratum | tdl |
|---|---|---|---|---|---|---|
| named | Q8N6I4 | LYSET | 26175 | 4 | dark | Tdark |
| named | P04637 | TP53 | 7157 | 18089 | well-studied | Tchem |
| named | P38398 | BRCA1 | 672 | 5856 | well-studied | Tchem |
| random dark | Q9H305 | CDIP1 | 29965 | 8 | dark | Tbio |
| random dark | Q8NA19 | L3MBTL4 | 91133 | 6 | dark | Tbio |
| random dark | Q14CX5 | SLC68A1 | 79847 | 4 | dark | Tdark |
| random dark | Q2M3W8 | ZNF181 | 339318 | 1 | dark | Tdark |
| random dark | Q86VS3 | IQCH | 64799 | 3 | dark | Tdark |
| random intermediate | O60858 | TRIM13 | 10206 | 35 | intermediate | Tbio |
| random intermediate | Q14240 | EIF4A2 | 1974 | 42 | intermediate | Tbio |
| random intermediate | Q9HBJ7 | USP29 | 57663 | 27 | intermediate | Tbio |
| random intermediate | O43290 | SART1 | 9092 | 87 | intermediate | Tbio |
| random intermediate | Q8NFW1 | COL22A1 | 169044 | 17 | intermediate | Tbio |
| random well-studied | Q9UMD9 | COL17A1 | 1308 | 124 | well-studied | Tbio |
| random well-studied | P04637 | TP53 | 7157 | 18089 | well-studied | Tchem |
| random well-studied | P51654 | GPC3 | 2719 | 538 | well-studied | Tbio |
| random well-studied | O75955 | FLOT1 | 10211 | 115 | well-studied | Tbio |
| random well-studied | Q8IZY2 | ABCA7 | 10347 | 127 | well-studied | Tbio |

## T0/T1 pipeline-difference checks

- Delta rows (direct T1 rows not known at T0): 27865.
- Delta rows with annotation date before the T0 GOA release (2022-11-17): 4296 (15.4%). By year: {2003: 1, 2004: 1, 2005: 10, 2006: 104, 2007: 54, 2008: 90, 2009: 170, 2010: 80, 2011: 193, 2012: 165, 2013: 128, 2014: 293, 2015: 135, 2016: 149, 2017: 556, 2018: 141, 2019: 194, 2020: 398, 2021: 311, 2022: 1123}.
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
| GO_Central | 0.0083 | 0.0064 |
| Reactome | 0.0049 | 0.0053 |
| UOS_MCB | 0.0 | 0.0052 |
| SynGO | 0.0039 | 0.0044 |
| HGNC-UCL | 0.0124 | 0.0026 |
| CAFA | 0.0172 | 0.0011 |

## Proteins without a GeneID mapping (no stratum)

<details><summary>30 proteins</summary>

P36268 (GGT2P), Q8IZF7 (ADGRF2P), Q92637 (FCGR1BP), P01715 (IGLV3-1), G9CGD6 (CNK3/IPCEF1), Q92617 (NPIPB3), A0A0A0MRZ9 (IGLV5-52), P0CJ72 (MTRNR2L5), P0DP08 (IGHV4-38-2), Q5SY68 (S100A7L2), Q7RTY3 (PRSS45P), Q8WZ33 (MAFIP), A0A0J9YXX1 (IGHV5-10-1), P51861 (CDR1), A8MWA4 (ZNF705EP), A8MYZ6 (FOXO6), A0A0A0MT76 (IGLJ1), P0CJ71 (MTRNR2L4), P0CJ74 (MTRNR2L7), P0CJ75 (MTRNR2L8), S4R3Y5 (MTRNR2L11), D6RBM5 (USP17L23), P0CJ77 (MTRNR2L10), P0DMP1 (MTRNR2L12), Q8N8C0 (ZNF781), Q9BVW6 (SMIM2), P0CJ68 (MTRNR2L1), P0CJ70 (MTRNR2L3), P0CJ73 (MTRNR2L6), S4R3P1 (MTRNR2L13)

</details>
