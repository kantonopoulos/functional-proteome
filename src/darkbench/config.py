from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
REPORTS_DIR = ROOT_DIR / "reports"

T0_DATE = date(2023, 1, 1)
PMID_CUTOFF_DATE = date(2022, 12, 31)
TAXON_ID = 9606

GO_RELEASE_T0 = "2023-01-01"
# The latest GO release at build time. EBI's GOA FTP was unreachable, so both GAFs come
# from the GO Consortium release archive, which redistributes the GOA human files.
GO_RELEASE_T1 = "2026-08-05"

# GOA human releases are a few weeks apart; a larger gap means T0 misses real T0 knowledge.
MAX_T0_GOA_LAG_DAYS = 42
# Accepted by the user on 2026-11-04: the newest pre-T0 GOA human file obtainable is
# 2022-11-17 (45 days before T0), because EBI was unreachable.
T0_GOA_LAG_ACCEPTED = True

URLS = {
    "gaf_t0": f"https://release.geneontology.org/{GO_RELEASE_T0}/annotations/goa_human.gaf.gz",
    "gaf_t1": f"https://release.geneontology.org/{GO_RELEASE_T1}/annotations/gaf/HUMAN-uniprot.gaf.gz",
    "go_obo_t0": f"https://release.geneontology.org/{GO_RELEASE_T0}/ontology/go-basic.obo",
    "gene2pubmed": "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2pubmed.gz",
    "gene2ensembl": "https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2ensembl.gz",
    # The flat file is used because the TSV export has no secondary-accession field.
    "uniprot_sprot_human": (
        "https://rest.uniprot.org/uniprotkb/search?compressed=true&format=txt&size=500"
        "&query=%28organism_id%3A9606%29+AND+%28reviewed%3Atrue%29"
    ),
    # HPA v22 (Dec 2022) defines the protein-coding gene set as of T0 (user decision).
    "hpa_v22": "https://v22.proteinatlas.org/download/proteinatlas.tsv.zip",
    "pharos_graphql": "https://pharos-api.ncats.io/graphql",
    "eutils": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
}

RAW_FILES = {
    "gaf_t0": "goa_human_t0_go2023-01-01.gaf.gz",
    "gaf_t1": f"goa_human_t1_go{GO_RELEASE_T1}.gaf.gz",
    "go_obo_t0": "go-basic_2023-01-01.obo",
    "gene2pubmed": "gene2pubmed.gz",
    "gene2ensembl": "gene2ensembl.gz",
    "uniprot_sprot_human": "uniprot_sprot_human.txt.gz",
    "hpa_v22": "proteinatlas_v22.tsv.zip",
    "pharos_tdl": "pharos_tdl.tsv",
    "pmid_boundary": "pmid_boundary.json",
}

EVIDENCE_CODES = ["EXP", "IDA", "IPI", "IMP", "IGI", "IEP"]
HTP_EVIDENCE_CODES = ["HTP", "HDA", "HMP", "HGI", "HEP"]
INCLUDE_HTP = False

# Author/curator statements: a pair already asserted at T0 this way was curated knowledge,
# so an upgrade to experimental evidence at T1 is not a discovery.
CURATED_STATEMENT_CODES = ["TAS", "NAS", "IC"]
# Ig/TR V/D/J/C gene segments are not proteins with their own function.
IG_TR_SEGMENT_PATTERN = r"^(IG[HKL][VDJC]|TR[ABDG][VDJC])"

PROTEIN_BINDING = "GO:0005515"
# HPA immunofluorescence curated into GO. Removed from both snapshots because it overlaps
# with T2 and would leak into any model that uses HPA image features.
# HPA antibody-profiling papers cited by UniProt carry the same data under a PMID.
EXCLUDED_REFERENCES = [
    "GO_REF:0000052",  # HPA immunofluorescence
    "PMID:31429579",  # HPA testis antibody-based proteomics (Pineau et al. 2019)
    "PMID:22042635",  # HPA antibody-based profiling of chromosome 21 (2012)
]
ROOT_TERMS = {"GO:0003674": "MF", "GO:0008150": "BP", "GO:0005575": "CC"}
NAMESPACES = {
    "molecular_function": "MF",
    "biological_process": "BP",
    "cellular_component": "CC",
}
PROPAGATION_RELATIONS = ("is_a", "part_of")
# Removed after propagation too: children re-add them, and they are uninformative.
UNINFORMATIVE_TERMS = [PROTEIN_BINDING, "GO:0005488"]  # protein binding, binding
DROPPED_AFTER_PROPAGATION = set(ROOT_TERMS) | set(UNINFORMATIVE_TERMS)

# Large-scale screens link hundreds of genes per paper without adding real knowledge.
MAX_GENES_PER_PMID = 100
DARK_MAX_PAPERS = 10  # dark: fewer than this
WELL_STUDIED_MIN_PAPERS = 100  # well-studied: more than this
SPOT_CHECK_GENES = ["TP53", "BRCA1", "LYSET"]
SPOT_CHECK_PER_STRATUM = 5
RANDOM_SEED = 0
GO_NO_GO_MIN_DARK_NK_LK = 200


def evidence_codes() -> list[str]:
    return EVIDENCE_CODES + (HTP_EVIDENCE_CODES if INCLUDE_HTP else [])
