import gzip
import logging
import re
import zipfile
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from darkbench import config

log = logging.getLogger(__name__)


def parse_uniprot_flat(path: Path) -> pd.DataFrame:
    rows: list[dict] = []
    entry: dict = {}
    with gzip.open(path, "rt") as handle:
        for line in handle:
            tag = line[:2]
            if tag == "ID":
                entry = {"reviewed": "Reviewed;" in line, "accessions": [], "gene": None,
                         "entrez_ids": [], "sequence_version": None, "sequence_date": None,
                         "taxon": None}
            elif tag == "AC":
                entry["accessions"] += [a.strip() for a in line[5:].split(";") if a.strip()]
            elif tag == "GN" and entry["gene"] is None:
                match = re.search(r"Name=([^;{]+)", line)
                entry["gene"] = match.group(1).strip() if match else None
            elif tag == "DR" and line[5:12] == "GeneID;":
                gene_id = line[5:].split(";")[1].strip()
                if gene_id not in entry["entrez_ids"]:
                    entry["entrez_ids"].append(gene_id)
            elif tag == "DT" and "sequence version" in line:
                match = re.match(r"DT   (\S+), sequence version (\d+)\.", line)
                entry["sequence_date"] = datetime.strptime(match.group(1), "%d-%b-%Y").date()
                entry["sequence_version"] = int(match.group(2))
            elif tag == "OX":
                entry["taxon"] = int(re.search(r"NCBI_TaxID=(\d+)", line).group(1))
            elif tag == "//":
                rows.append({
                    "accession": entry["accessions"][0],
                    "secondary_accessions": entry["accessions"][1:],
                    "gene": entry["gene"],
                    "entrez_ids": entry["entrez_ids"],
                    "sequence_version": entry["sequence_version"],
                    "sequence_date": entry["sequence_date"],
                    "reviewed": entry["reviewed"],
                    "taxon": entry["taxon"],
                })
    return pd.DataFrame(rows)


def swissprot_universe(uniprot: pd.DataFrame) -> pd.DataFrame:
    keep = uniprot["reviewed"] & (uniprot["taxon"] == config.TAXON_ID)
    log.info("Swiss-Prot human universe: %d -> %d", len(uniprot), int(keep.sum()))
    return uniprot[keep].reset_index(drop=True)


def sequence_filter(universe: pd.DataFrame, t0: date) -> pd.DataFrame:
    # Methods must predict for the sequence they would have seen at T0.
    keep = universe["sequence_date"] <= t0
    log.info("sequence filter (last modified <= %s): %d -> %d", t0, len(universe), int(keep.sum()))
    return universe[keep].reset_index(drop=True)


def hpa_first_accessions(path: Path, secondary_to_primary: dict[str, str]) -> set[str]:
    """First UniProt accession of each HPA gene, mapped to current primary accessions."""
    with zipfile.ZipFile(path) as archive:
        hpa = pd.read_csv(archive.open("proteinatlas.tsv"), sep="\t", usecols=["Gene", "Uniprot"])
    # One protein per gene (user decision): HPA lists the gene's main product first, and
    # dropping further products removes same-gene duplicates missing from goa_human at T0.
    first = hpa["Uniprot"].dropna().map(lambda ids: ids.split(",")[0].strip())
    log.info("HPA v22 genes: %d, with UniProt: %d", len(hpa), len(first))
    return {secondary_to_primary.get(a, a) for a in first}


def hpa_filter(proteins: pd.DataFrame, hpa_ids: set[str]) -> pd.DataFrame:
    keep = proteins["accession"].isin(hpa_ids)
    log.info("HPA v22 first UniProt per gene: %d -> %d", len(proteins), int(keep.sum()))
    return proteins[keep].reset_index(drop=True)


def secondary_map(universe: pd.DataFrame) -> tuple[dict[str, str], set[str]]:
    """Return unique secondary -> primary mappings, plus secondaries that map to several entries."""
    targets: dict[str, set[str]] = {}
    for primary, secondaries in zip(universe["accession"], universe["secondary_accessions"]):
        for secondary in secondaries:
            targets.setdefault(secondary, set()).add(primary)
    unique = {s: next(iter(p)) for s, p in targets.items() if len(p) == 1}
    # Demerged entries: no way to tell which entry the old annotation describes.
    ambiguous = {s for s, p in targets.items() if len(p) > 1}
    return unique, ambiguous


def canonical_accession(raw_id: str) -> str:
    return re.sub(r"-\d+$", "", raw_id)
