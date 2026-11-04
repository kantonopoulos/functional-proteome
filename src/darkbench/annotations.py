import gzip
import logging
from pathlib import Path

import pandas as pd

from darkbench import config
from darkbench.proteins import canonical_accession
from darkbench.report import StepLog

log = logging.getLogger(__name__)

GAF_COLUMNS = [
    "db", "db_object_id", "db_object_symbol", "qualifier", "go_id", "reference",
    "evidence", "with_from", "aspect", "db_object_name", "db_object_synonym",
    "db_object_type", "taxon", "date", "assigned_by", "annotation_extension",
    "gene_product_form_id",
]
# GAF 2.1 and 2.2 both have 17 columns; they differ in the qualifier vocabulary.
GAF_COLUMN_COUNTS = {"2.1": 17, "2.2": 17}


def read_gaf_header(path: Path) -> dict:
    header: list[str] = []
    with gzip.open(path, "rt") as handle:
        for line in handle:
            if not line.startswith("!"):
                break
            header.append(line.rstrip("\n"))
    gaf_version = next(l.split(":", 1)[1].strip() for l in header if l.startswith("!gaf-version"))
    # GO Consortium copies nest the upstream headers in blocks separated by "!====" lines;
    # the GOA release date is the one in the block written by UniProt.
    blocks: list[list[str]] = [[]]
    for line in header:
        if line.startswith("!===="):
            blocks.append([])
        else:
            blocks[-1].append(line)
    goa_dates = [
        l.split(":", 1)[1].strip()
        for block in blocks if any("generated-by: UniProt" in l for l in block)
        for l in block if l.startswith("!date-generated")
    ]
    all_dates = [l.split(":", 1)[1].strip() for l in header if l.startswith("!date-generated")]
    go_versions = [l.split(":", 1)[1].strip() for l in header if l.startswith("!go-version")]
    return {
        "gaf_version": gaf_version,
        "goa_date_generated": goa_dates[0] if goa_dates else None,
        "all_date_generated": all_dates,
        "go_version": go_versions,
    }


def read_gaf(path: Path, gaf_version: str) -> tuple[pd.DataFrame, int]:
    """Return the annotation rows and the number of rows with an unexpected column count."""
    expected = GAF_COLUMN_COUNTS[gaf_version]
    rows: list[list[str]] = []
    bad = 0
    with gzip.open(path, "rt") as handle:
        for line in handle:
            if line.startswith("!"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != expected:
                bad += 1
                continue
            rows.append(fields)
    return pd.DataFrame(rows, columns=GAF_COLUMNS), bad


def is_negated(qualifier: str) -> bool:
    # 2.1: "NOT" or "NOT|contributes_to"; 2.2: "NOT|enables". Both pipe-separated.
    return "NOT" in qualifier.split("|")


def primary_taxon(taxon: str) -> str:
    # The second taxon, if present, is the interacting organism, not the annotated protein.
    return taxon.split("|")[0]


def map_accessions(
    gaf: pd.DataFrame,
    secondary_to_primary: dict[str, str],
    ambiguous: set[str],
    primaries: set[str],
) -> tuple[pd.DataFrame, dict]:
    canonical = gaf["db_object_id"].map(canonical_accession)
    is_secondary = ~canonical.isin(primaries) & canonical.isin(secondary_to_primary.keys())
    is_ambiguous = ~canonical.isin(primaries) & canonical.isin(ambiguous)
    stats = {
        "isoform_rows_collapsed": int((canonical != gaf["db_object_id"]).sum()),
        "secondary_rows_mapped": int(is_secondary.sum()),
        "secondary_accessions_mapped": int(canonical[is_secondary].nunique()),
        "ambiguous_rows_dropped": int(is_ambiguous.sum()),
        "ambiguous_accessions_dropped": sorted(canonical[is_ambiguous].unique()),
    }
    out = gaf.assign(accession=canonical.where(~is_secondary, canonical.map(secondary_to_primary)))
    return out[~is_ambiguous].reset_index(drop=True), stats


def curated_statements(gaf: pd.DataFrame, secondary_to_primary: dict[str, str],
                       accessions: set[str]) -> pd.DataFrame:
    """T0 rows asserted by authors or curators (TAS/NAS/IC), not negated, on kept proteins."""
    df = gaf[(gaf["db"] == "UniProtKB")
             & gaf["evidence"].isin(config.CURATED_STATEMENT_CODES)
             & ~gaf["qualifier"].map(is_negated)]
    canonical = df["db_object_id"].map(canonical_accession)
    df = df.assign(accession=canonical.map(lambda a: secondary_to_primary.get(a, a)))
    return df[df["accession"].isin(accessions)].reset_index(drop=True)


def filter_annotations(
    gaf: pd.DataFrame,
    label: str,
    steps: StepLog,
    secondary_to_primary: dict[str, str],
    ambiguous: set[str],
    universe: set[str],
    sequence_ok: set[str],
    final_ok: set[str],
) -> tuple[pd.DataFrame, dict]:
    df = steps.filter(gaf, label, "UniProtKB, taxon 9606",
                      (gaf["db"] == "UniProtKB")
                      & (gaf["taxon"].map(primary_taxon) == f"taxon:{config.TAXON_ID}"))
    df = steps.filter(df, label, "evidence codes", df["evidence"].isin(config.evidence_codes()))
    df = steps.filter(df, label, "NOT qualifier", ~df["qualifier"].map(is_negated))
    df = steps.filter(df, label, "protein binding", df["go_id"] != config.PROTEIN_BINDING)
    df = steps.filter(df, label, "HPA-derived references",
                      ~df["reference"].map(lambda r: bool(set(r.split("|")) & set(config.EXCLUDED_REFERENCES))))
    before = len(df)
    df, mapping_stats = map_accessions(df, secondary_to_primary, ambiguous, universe)
    steps.add(label, "accession mapping", before, len(df))
    df = steps.filter(df, label, "Swiss-Prot universe", df["accession"].isin(universe))
    df = steps.filter(df, label, "sequence filter", df["accession"].isin(sequence_ok))
    df = steps.filter(df, label, "protein universe (HPA v22, in T0 GAF, not Ig/TR)",
                      df["accession"].isin(final_ok))
    return df, mapping_stats
