# T1 GO label sets: build report

> **GO: 1020 dark proteins in NK+LK summed across namespaces (threshold 200).**

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

## Notes and deviations

- EBI's GOA FTP was unreachable, so both GAFs come from the GO Consortium release archive (user decision). The T0 file is GOA human 2022-11-17 plus PAINT IBA rows; IBA is not an allowed evidence code, so those rows are filtered out.
- T0 GOA release is 45 days before T0, over the 6-week limit; accepted by the user.
- T0 file covers the UniProt reference proteome (goa_human); T1 file covers all UniProt human entries. Both are restricted to the same protein universe; see the scope check.
- Protein universe: one UniProt entry per HPA v22 gene (user decision). HPA lists accessions alphabetically, so the entry present in the T0 GAF is preferred, else the first listed. Proteins absent from the T0 GAF that share a GeneID or symbol with a T0-file protein are dropped as same-gene artifacts of goa_human's one-protein-per-gene scope.
- Proteins with several GeneIDs take the max paper count over their GeneIDs (user decision).
- Secondary accessions that map to several current entries are dropped (user decision): T0 [], T1 [].
- The pre-T0 TCRD download host was unreachable, so TDL is the current Pharos value (Pharos dbVersion pharos319 (current, post-T0)) and reflects knowledge gained after T0.
- PMID boundary: 36585753 (Entrez date 2022/12/30 23:53).
- Proteins without a GeneID: 318 of 18882 (1.7%); listed at the end.

## Row counts per filter step

| table | step | before | after | removed |
|---|---|---|---|---|
| proteins | Swiss-Prot human at T1 | 20429 | 20429 | 0 |
| proteins | sequence last modified <= 2023-01-01 | 20429 | 20081 | 348 |
| proteins | HPA v22 gene, one protein per gene (T0-file entry preferred) | 20081 | 18888 | 1193 |
| proteins | not a same-gene product missing from the T0 GAF | 18888 | 18882 | 6 |
| T0 | UniProtKB, taxon 9606 | 626136 | 626136 | 0 |
| T0 | evidence codes | 626136 | 337902 | 288234 |
| T0 | NOT qualifier | 337902 | 336925 | 977 |
| T0 | protein binding | 336925 | 130643 | 206282 |
| T0 | accession mapping | 130643 | 130643 | 0 |
| T0 | Swiss-Prot universe | 130643 | 130636 | 7 |
| T0 | sequence filter | 130636 | 128897 | 1739 |
| T0 | HPA v22 gene set and same-gene filter | 128897 | 128166 | 731 |
| T1 | UniProtKB, taxon 9606 | 910476 | 862694 | 47782 |
| T1 | evidence codes | 862694 | 448915 | 413779 |
| T1 | NOT qualifier | 448915 | 447749 | 1166 |
| T1 | protein binding | 447749 | 169630 | 278119 |
| T1 | accession mapping | 169630 | 169630 | 0 |
| T1 | Swiss-Prot universe | 169630 | 169626 | 4 |
| T1 | sequence filter | 169626 | 167183 | 2443 |
| T1 | HPA v22 gene set and same-gene filter | 167183 | 165847 | 1336 |
| T0 | GO term in T0 ontology (after alt_id/obsolete mapping) | 128166 | 128160 | 6 |
| T0 | propagated (protein, term) pairs, roots removed | 98201 | 711944 | -613743 |
| T1 | GO term in T0 ontology (after alt_id/obsolete mapping) | 165847 | 164494 | 1353 |
| T1 | propagated (protein, term) pairs, roots removed | 110749 | 769291 | -658542 |
| ground truth | T1 propagated pairs -> new at T1 | 769291 | 123995 | 645296 |
| gene2pubmed | taxon 9606, distinct links | 3348186 | 3348186 | 0 |
| gene2pubmed | PMIDs with <= 100 human genes | 3348186 | 2521108 | 827078 |
| gene2pubmed | PMID <= 36585753 | 2521108 | 2300403 | 220705 |

## GO term mapping onto the T0 ontology

| snapshot | status | rows | terms |
|---|---|---|---|
| T0 | current | 127932 | 12368 |
| T0 | obsolete_replaced | 228 | 4 |
| T0 | obsolete_unmapped | 6 | 3 |
| T1 | absent | 1329 | 305 |
| T1 | current | 164491 | 12689 |
| T1 | obsolete_replaced | 3 | 2 |
| T1 | obsolete_unmapped | 24 | 4 |

## Test set summary (proteins per namespace x knowledge type x stratum)

| namespace | knowledge_type | stratum | proteins |
|---|---|---|---|
| MF | LK | dark | 103 |
| MF | LK | intermediate | 465 |
| MF | LK | well-studied | 181 |
| MF | NK | dark | 165 |
| MF | NK | intermediate | 261 |
| MF | NK | unassigned | 1 |
| MF | NK | well-studied | 57 |
| MF | PK | dark | 116 |
| MF | PK | intermediate | 965 |
| MF | PK | unassigned | 2 |
| MF | PK | well-studied | 1121 |
| BP | LK | dark | 98 |
| BP | LK | intermediate | 334 |
| BP | LK | well-studied | 103 |
| BP | NK | dark | 165 |
| BP | NK | intermediate | 227 |
| BP | NK | unassigned | 1 |
| BP | NK | well-studied | 44 |
| BP | PK | dark | 143 |
| BP | PK | intermediate | 1266 |
| BP | PK | unassigned | 1 |
| BP | PK | well-studied | 1428 |
| CC | LK | dark | 84 |
| CC | LK | intermediate | 352 |
| CC | LK | well-studied | 216 |
| CC | NK | dark | 405 |
| CC | NK | intermediate | 432 |
| CC | NK | unassigned | 2 |
| CC | NK | well-studied | 82 |
| CC | PK | dark | 370 |
| CC | PK | intermediate | 1900 |
| CC | PK | unassigned | 1 |
| CC | PK | well-studied | 1191 |

## Checks

| check | result | detail |
|---|---|---|
| gzip opens: goa_human_t0_go2023-01-01.gaf.gz | PASS | md5 082ce90c7565a48721f403c73b23419c |
| gzip opens: goa_human_t1_go2026-08-05.gaf.gz | PASS | md5 f74b40c53bdf8ed39d300a491eaf852d |
| gzip opens: gene2pubmed.gz | PASS | md5 c0435aa0c5564c4328fe984eb7a06767 |
| zip opens: proteinatlas_v22.tsv.zip | PASS | md5 89601316ffe9c0972623f96d6372d5ac |
| gzip opens: uniprot_sprot_human.txt.gz | PASS | md5 cdfe580d07365aeb32dc4f2bec06bc6d |
| T0 GOA release on or before 2023-01-01 | PASS | 2022-11-17 |
| T0 GOA release within 42 days of T0 | ACCEPTED | 2022-11-17 is 45 days before T0; accepted by user (EBI unreachable) |
| T1 GOA release after T0 | PASS | 2026-07-28 |
| GO ontology is the 2023-01-01 release | PASS | releases/2023-01-01 |
| T0 GAF 2.2 rows have 17 columns | PASS | 626136 rows read, 0 malformed |
| T1 GAF 2.2 rows have 17 columns | PASS | 910476 rows read, 0 malformed |
| One protein per HPA gene | PASS | 18882 proteins |
| T0 retained rows are taxon 9606 and UniProtKB | PASS | 128166 rows |
| T1 retained rows are taxon 9606 and UniProtKB | PASS | 165847 rows |
| T0 propagated sets closed under parents (all 12866 proteins) | PASS | 0 missing parent links |
| T1 propagated sets closed under parents (all 13897 proteins) | PASS | 0 missing parent links |
| Report mapped obsolete / alt_id / dropped T1 terms | PASS | T0 obsolete_replaced: 228 rows, 4 terms; T0 obsolete_unmapped: 6 rows, 3 terms; T1 absent: 1329 rows, 305 terms; T1 obsolete_replaced: 3 rows, 2 terms; T1 obsolete_unmapped: 24 rows, 4 terms |
| No ground-truth term existed at T0 (after propagation) | PASS | 0 overlapping |
| NK/LK/PK mutually exclusive per protein and namespace | PASS | 0 conflicts |
| No root terms in ground truth | PASS | 0 root rows |
| No empty ground-truth sets | PASS | 0 empty |
| No NK protein is a same-gene product missing from the T0 GAF (scope check) | PASS | 0 artifacts; 31 of 1164 NK proteins absent from the T0 file with no same-gene T0 protein (kept as NK): A0A1B0GTL2, A0A1B0GTR4, B1AJZ9, B2RC85, E9PRG8, P0C881, P0DMU8, Q32NC0, Q5M9N0, Q5RHP9, Q5SZB4, Q5T1B0, Q6PB30, Q6PIY5, Q6X4T0, Q7L0X2, Q86V59, Q8IY85, Q8N0U7, Q8N128, Q8N5N4, Q8N5U0, Q96BQ5, Q96CX6, Q96F63, Q96HJ3, Q96MR6, Q9BY89, Q9H098, Q9H4I3, Q9Y546 |
| PMID boundary entry date on or before 2022-12-31 | PASS | PMID 36585753, Entrez date 2022/12/30 23:53 |
| Proteins without GeneID get no stratum | PASS | 318 of 18882 (1.7%) unmapped |
| Spot-check genes found | PASS | TP53, BRCA1, LYSET |

## Spot check for manual review

| selection | accession | gene | entrez_id | pmid_count_t0 | stratum | tdl |
|---|---|---|---|---|---|---|
| named | Q8N6I4 | LYSET | 26175 | 4 | dark | Tdark |
| named | P04637 | TP53 | 7157 | 18089 | well-studied | Tchem |
| named | P38398 | BRCA1 | 672 | 5856 | well-studied | Tchem |
| random dark | Q8N801 | STPG4 | 285051 | 1 | dark | Tdark |
| random dark | Q8TCN5 | ZNF507 | 22847 | 3 | dark | Tdark |
| random dark | Q96C00 | ZBTB9 | 221504 | 1 | dark | Tdark |
| random dark | F2Z333 | FNDC10 | 643988 | 0 | dark | Tdark |
| random dark | A6NNL0 | NUTM2B | 729262 | 7 | dark | Tdark |
| random intermediate | Q9Y3M2 | CBY1 | 25776 | 49 | intermediate | Tbio |
| random intermediate | Q9BXF6 | RAB11FIP5 | 26056 | 30 | intermediate | Tbio |
| random intermediate | P20648 | ATP4A | 495 | 33 | intermediate | Tclin |
| random intermediate | Q16558 | KCNMB1 | 3779 | 66 | intermediate | Tbio |
| random intermediate | P05386 | RPLP1 | 6176 | 47 | intermediate | Tbio |
| random well-studied | Q9UMD9 | COL17A1 | 1308 | 124 | well-studied | Tbio |
| random well-studied | P04798 | CYP1A1 | 1543 | 1524 | well-studied | Tchem |
| random well-studied | P51654 | GPC3 | 2719 | 538 | well-studied | Tbio |
| random well-studied | O76061 | STC2 | 8614 | 124 | well-studied | Tbio |
| random well-studied | Q8IZY2 | ABCA7 | 10347 | 127 | well-studied | Tbio |

## Proteins without a GeneID mapping (no stratum)

<details><summary>318 proteins</summary>

O75022 (LILRB3), P01597 (IGKV1-39), P01615 (IGKV2D-28), P01764 (IGHV3-23), P23083 (IGHV1-2), P01593 (IGKV1D-33), P01594 (IGKV1-33), P06312 (IGKV4-1), P01619 (IGKV3-20), P01699 (IGLV1-44), P01700 (IGLV1-47), P01742 (IGHV1-69), P01814 (IGHV2-70), P51784 (USP11), P59047 (NLRP5), O43316 (PAX4), P01768 (IGHV3-30), Q9P1A6 (DLGAP2), A6NNM8 (TTLL13), A6PVC2 (TTLL8), P01602 (IGKV1-5), P01701 (IGLV1-51), P01704 (IGLV2-14), P01705 (IGLV2-23), P01706 (IGLV2-11), P01709 (IGLV2-8), P01721 (IGLV6-57), P01772 (IGHV3-33), P0DOY3 (IGLC3), P36268 (GGT2P), P57078 (RIPK4), Q8IZF7 (ADGRF2P), Q92637 (FCGR1BP), P01714 (IGLV3-19), P01825 (IGHV4-59), Q66K41 (ZNF385C), Q7Z7M1 (ADGRD2), Q8N1D0 (SLC67A1-AS), A0A075B6N1 (TRBV19), A0A087WT01 (TRAV27), P01599 (IGKV1-17), P01715 (IGLV3-1), P01717 (IGLV3-25), P01763 (IGHV3-48), P04211 (IGLV7-43), A0A075B6J9 (IGLV2-18), A0A0K0K1A5 (TRBV6-5), G9CGD6 (CNK3/IPCEF1), P01601 (IGKV1D-16), P01743 (IGHV1-46), P01762 (IGHV3-11), P01780 (IGHV3-7), P01817 (IGHV2-5), P04433 (IGKV3-11), P04435 (TRBV7-9), P06315 (IGKV5-2), P06331 (IGHV4-34), P0DOY2 (IGLC2), P80748 (IGLV3-21), A8CG34 (POM121C), P01611 (IGKV1D-12), P01624 (IGKV3-15), P01703 (IGLV1-40), P01718 (IGLV3-27), P01766 (IGHV3-13), P01767 (IGHV3-53), P04430 (IGKV1-16), Q92617 (NPIPB3), P01614 (IGKV2D-40), P01733 (TRBV12-3), P01824 (IGHV4-39), P04432 (IGKV1D-39), P04437 (TRAV29DV5), P06310 (IGKV2-30), Q9BXT5 (TEX15), A0A075B6I0 (IGLV8-61), A0A075B6I6 (IGLV1-50), A0A075B6K6 (IGLV4-3), A0A075B6P5 (IGKV2-28), A0A075B6R9 (IGKV2D-24), A0A075B6S4 (IGKV1D-17), A0A075B6S6 (IGKV2D-30), A0A075B6T6 (TRAV12-2), A0A075B6T7 (TRAV6), A0A075B6T8 (TRAV9-1), A0A075B6U4 (TRAV7), A0A075B6W5 (TRAV23DV6), A0A087WW87 (IGKV2-40), A0A0A0MRZ7 (IGKV2D-26), A0A0A0MRZ8 (IGKV3D-11), A0A0A0MRZ9 (IGLV5-52), A0A0A0MS14 (IGHV1-45), A0A0A6YYG3 (TRBV6-8), A0A0B4J1U7 (IGHV6-1), A0A0B4J1Y8 (IGLV9-49), A0A0B4J1Z2 (IGKV1D-43), A0A0B4J235 (TRAV13-2), A0A0B4J237 (TRAV8-2), A0A0B4J248 (TRAV1-1), A0A0B4J265 (TRAV26-2), A0A0B4J274 (TRAV20), A0A0B4J280 (TRAV40), A0A0C4DH25 (IGKV3D-20), A0A0C4DH27 (TRGV8), A0A0C4DH32 (IGHV3-20), A0A0C4DH41 (IGHV4-61), A0A0C4DH55 (IGKV3D-7), A0A0C4DH59 (TRBV5-4), A0A0C4DH72 (IGKV1-6), A0A0G2JMI3 (IGHV1-69-2), A0A0K0K1G6 (TRBV10-3), A0A1B0GX56 (TRDV1), A0A577 (TRBV4-1), P01737 (TRAV8-4), Q0VAA5 (PLCXD2), Q5JPF3 (ANKRD36C), Q96KJ4 (MSLNL), A0A075B6H7 (IGKV3-7), A0A075B6I4 (IGLV10-54), A0A075B6N3 (TRBV24-1), A0A075B6Q5 (IGHV3-64), A0A075B6R2 (IGHV4-4), A0A075B6S5 (IGKV1-27), A0A075B6V5 (TRAV36DV7), A0A087WSX0 (IGLV5-45), A0A087WSZ0 (IGKV1D-8), A0A087WT02 (TRAV9-2), A0A087WT03 (TRAV26-1), A0A0A0MS00 (IGLV3-32), A0A0A6YYG2 (TRBV6-6), A0A0A6YYK7 (TRAV19), A0A0B4J1V0 (IGHV3-15), A0A0B4J1V2 (IGHV2-26), A0A0B4J1X5 (IGHV3-74), A0A0B4J1X8 (IGHV3-43), A0A0B4J234 (TRAV2), A0A0B4J263 (TRAV39), A0A0B4J264 (TRAV38-1), A0A0B4J271 (TRAV12-3), A0A0B4J275 (TRAV17), A0A0C4DH26 (IGKV6D-41), A0A0C4DH29 (IGHV1-3), A0A0C4DH39 (IGHV1-58), A0A539 (TRBV4-2), A0A576 (TRBV3-1), A0A5B7 (TRBV29-1), P0CJ72 (MTRNR2L5), P0DP08 (IGHV4-38-2), Q8NH09 (OR8S1), Q9BXX2 (ANKRD30B), A0A075B6H8 (IGKV1D-42), A0A075B6H9 (IGLV4-69), A0A075B6I3 (IGLV11-55), A0A075B6J2 (IGLV2-33), A0A075B6K2 (IGLV3-12), A0A075B6K4 (IGLV3-10), A0A075B6K5 (IGLV3-9), A0A075B6N4 (TRBV25-1), A0A075B6X5 (TRAV18), A0A087WSY4 (IGHV4-30-2), A0A0A0MT36 (IGKV6D-21), A0A0A6YYD4 (TRBV13), A0A0A6YYK6 (TRAV16), A0A0B4J1U3 (IGLV1-36), A0A0B4J1U4 (TRGV5), A0A0B4J1U6 (TRBV9), A0A0B4J1V7 (IGHV7-81), A0A0B4J1Y9 (IGHV3-72), A0A0B4J238 (TRAV1-2), A0A0B4J262 (TRAV8-6), A0A0B4J276 (TRAV25), A0A0B4J2D9 (IGKV1D-13), A0A0B4J2E0 (TRBV12-4), A0A0C4DH34 (IGHV4-28), A0A0C4DH35 (IGHV3-35), A0A0C4DH67 (IGKV1-8), A0A0C4DH68 (IGKV2-24), A0A0C4DH69 (IGKV1-9), A0A0K0K1A3 (TRBV10-1), A0A0K0K1C0 (TRBV11-1), A0A1B0GVH4 (PRSS51), A0A1B0GX78 (TRBV12-5), A0A5A6 (TRBV11-3), A0A5B0 (TRBV14), A0JD37 (TRDV3), B1ANS9 (WDR64), P0C7A2 (FAM153B), Q5SY68 (S100A7L2), Q7RTY3 (PRSS45P), Q8NGC2 (OR4E2), Q8WZ33 (MAFIP), Q96R69 (OR4F4), Q9HBF5 (ST20), A0A075B6I9 (IGLV7-46), A0A075B6J1 (IGLV5-37), A0A075B6R0 (TRGV2), A0A075B6S2 (IGKV2D-29), A0A075B6S9 (IGKV1-37), A0A087WSY6 (IGKV3D-15), A0A087WSZ9 (TRAV30), A0A087WV62 (TRBV16), A0A0A0MS15 (IGHV3-49), A0A0A6YYJ7 (TRAV8-3), A0A0B4J1V1 (IGHV3-21), A0A0B4J1V6 (IGHV3-73), A0A0B4J240 (TRAV10), A0A0B4J241 (TRAV13-1), A0A0B4J244 (TRAV3), A0A0B4J245 (TRAV12-1), A0A0B4J268 (TRAV4), A0A0B4J273 (TRAV34), A0A0B4J279 (TRAV21), A0A0C4DH30 (IGHV3-16), A0A0C4DH31 (IGHV1-18), A0A0C4DH38 (IGHV5-51), A0A0C4DH42 (IGHV3-66), A0A0J9YVY3 (IGHV7-4-1), A0A0J9YX35 (IGHV3-64D), A0A0J9YXX1 (IGHV5-10-1), A0A0K0K1B3 (TRBV30), A0A0K0K1D8 (TRBV6-1), A0A0K0K1E9 (TRBV7-7), A0A0K0K1G8 (TRBV10-2), A0A1B0GX31 (TRBV7-6), A0A1B0GX49 (TRBV6-4), A0A1B0GX95 (TRBV7-4), A0A597 (TRBV5-5), A0A5B6 (TRBV28), A0JD36 (TRDV2), P03979 (TRGV3), P0DSN7 (IGKV1D-37), P51861 (CDR1), Q8WX39 (LCN9), Q96L11 (SOFU1), Q99603 (TRGV9), A0A075B6I1 (IGLV4-60), A0A075B6I7 (IGLV5-48), A0A075B6J6 (IGLV3-22), A0A075B6K0 (IGLV3-16), A0A075B6N2 (TRBV20-1), A0A087X0M5 (TRBV18), A0A0A6YYC5 (TRAV14DV4), A0A0A6YYK1 (TRAV8-1), A0A0B4J249 (TRAV5), A0A0B4J266 (TRAV41), A0A0B4J272 (TRAV24), A0A0B4J277 (TRAV22), A0A0B4J2H0 (IGHV1-69D), A0A0C4DH24 (IGKV6-21), A0A0C4DH28 (TRGV4), A0A0C4DH33 (IGHV1-24), A0A0C4DH36 (IGHV3-38), A0A0C4DH43 (IGHV2-70D), A0A0C4DH73 (IGKV1-12), A0A0J9YXY3 (TRBV6-2), A0A0K0K1C4 (TRBV27), A0A1B0GX68 (TRBV2), A0A1B0GXF2 (TRBV7-2), A0A578 (TRBV5-1), A0A599 (TRBV5-6), A0JD32 (TRAV38-2DV8), A8MWA4 (ZNF705EP), A8MYZ6 (FOXO6), P0DP72 (VSIG10L2), Q30KQ1 (DEFB133), Q8TAV5 (KCNJ5-AS1), Q9H5J0 (ZBTB3), A0A0A0MT76 (IGLJ1), A0A0C4DH62 (IGHJ1), A0A0J9YX06 (TRBJ1-2), C9JG80 (NPIPB4), P0CJ71 (MTRNR2L4), P0CJ74 (MTRNR2L7), P0CJ75 (MTRNR2L8), Q17RQ9 (NKPD1), Q4UJ75 (ANKRD20A4P), Q4V326 (GAGE2E), Q6ZRR7 (LRRC9), Q6ZVN7 (SEM1), Q96FA7 (ZBED10P), Q96PG1 (MS4A4E), S4R3Y5 (MTRNR2L11), A0A075B6Y9 (TRAJ42), A0A0B4J200 (TRBJ2-3), A0A0J9YWX3 (TRBJ1-6), A6NN90 (C2orf81), D6RBM5 (USP17L23), P0DPI4 (TRBD1), P0DPR3 (TRDD1), Q5SQ80 (ANKRD20A2P), Q5VUR7 (ANKRD20A3P), Q9UBP8 (KAAG1), A0A0A0MT78 (TRBJ2-7), A0A0A0MTA7 (TRBJ2-1), A2A2Z9 (ANKRD18B), P0CJ77 (MTRNR2L10), P0DMP1 (MTRNR2L12), A0A075B6S0 (TRGJ1), A0A075B6Y3 (TRAJ3), A0A075B706 (TRDJ1), P0DOY5 (IGHD1-1), Q8N8C0 (ZNF781), Q8N8D7 (NKAIN3), Q9BVW6 (SMIM2), A0A0A0MT89 (IGKJ1), A6NKX4 (SLC22A31), O14603 (PRY), P0CJ68 (MTRNR2L1), P0CJ70 (MTRNR2L3), P0CJ73 (MTRNR2L6), S4R3P1 (MTRNR2L13), Q8NFD4 (-), A0A075B700 (TRAJ31), A8MWE9 (EFCAB8), A0A0J9YXA8 (TRBJ1-1), A0A0J9YWP8 (TRBJ1-3), A0A0J9YXG5 (TRBJ1-4), A0A0J9YXM7 (TRBJ1-5)

</details>
