import json
import logging
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

from darkbench import config
from darkbench.report import StepLog

log = logging.getLogger(__name__)
EUTILS_PAUSE_SECONDS = 0.4  # NCBI allows 3 requests per second without an API key
BOUNDARY_SEARCH_DAYS = 7
EUTILS_RETMAX = 10000
ESUMMARY_BATCH = 200


def eutils_get(endpoint: str, params: dict) -> dict:
    time.sleep(EUTILS_PAUSE_SECONDS)
    response = requests.get(
        f"{config.URLS['eutils']}/{endpoint}",
        params={**params, "db": "pubmed", "retmode": "json"},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def pmids_entered_on(day: date) -> list[int]:
    term = f'"{day:%Y/%m/%d}"[EDAT]'
    result = eutils_get("esearch.fcgi", {"term": term, "retmax": EUTILS_RETMAX})["esearchresult"]
    if int(result["count"]) > EUTILS_RETMAX:
        raise RuntimeError(f"More than {EUTILS_RETMAX} PMIDs entered on {day}; narrow the query")
    return [int(p) for p in result["idlist"]]


def entrez_dates(pmids: list[int]) -> dict[int, str]:
    result = eutils_get("esummary.fcgi", {"id": ",".join(map(str, pmids))})["result"]
    out = {}
    for pmid in pmids:
        history = result.get(str(pmid), {}).get("history", [])
        dates = [h["date"] for h in history if h["pubstatus"] == "entrez"]
        out[pmid] = dates[0] if dates else ""
    return out


def is_on_or_before(entrez: str, cutoff: date) -> bool:
    return bool(entrez) and entrez[:10].replace("/", "-") <= cutoff.isoformat()


def find_pmid_boundary(cutoff: date) -> dict:
    """Largest PMID entered on or before the cutoff, cached because it is a raw download."""
    path = config.RAW_DIR / config.RAW_FILES["pmid_boundary"]
    if path.exists():
        return json.loads(path.read_text())
    # PMIDs are assigned in entry order, so the last week before the cutoff holds the maximum.
    candidates: list[int] = []
    for offset in range(BOUNDARY_SEARCH_DAYS):
        candidates += pmids_entered_on(cutoff - timedelta(days=offset))
    # Records added years later can carry a back-dated [EDAT] index value, so the largest
    # PMID whose recorded Entrez date is on or before the cutoff is the boundary.
    ordered = sorted(set(candidates), reverse=True)
    skipped: list[int] = []
    boundary, boundary_date = None, ""
    for start in range(0, len(ordered), ESUMMARY_BATCH):
        batch = ordered[start:start + ESUMMARY_BATCH]
        dates = entrez_dates(batch)
        hit = next((p for p in batch if is_on_or_before(dates[p], cutoff)), None)
        if hit is not None:
            boundary, boundary_date = hit, dates[hit]
            skipped += [p for p in batch if p > hit]
            break
        skipped += batch
    if boundary is None:
        raise RuntimeError("No PMID with an Entrez date on or before the cutoff was found")
    result = {
        "cutoff_date": cutoff.isoformat(),
        "pmid_boundary": boundary,
        "boundary_entrez_date": boundary_date,
        "pmids_scanned": len(candidates),
        "backdated_pmids_skipped": skipped,
        "query": f"[EDAT] per day, {cutoff - timedelta(days=BOUNDARY_SEARCH_DAYS - 1)}..{cutoff}",
        "download_date": date.today().isoformat(),
    }
    path.write_text(json.dumps(result, indent=2))
    return result


def read_gene2pubmed(path: Path) -> pd.DataFrame:
    chunks = pd.read_csv(path, sep="\t", usecols=[0, 1, 2], chunksize=5_000_000,
                         names=["tax_id", "gene_id", "pmid"], header=0, dtype="int64")
    return pd.concat(chunk[chunk["tax_id"] == config.TAXON_ID] for chunk in chunks)


def read_gene2ensembl(path: Path) -> dict[str, list[str]]:
    table = pd.read_csv(path, sep="\t", usecols=[0, 1, 2], header=0,
                        names=["tax_id", "gene_id", "ensembl_gene"], dtype=str)
    table = table[table["tax_id"] == str(config.TAXON_ID)].drop_duplicates(["gene_id", "ensembl_gene"])
    return table.groupby("ensembl_gene")["gene_id"].apply(list).to_dict()


def fill_entrez_from_ensembl(proteins: pd.DataFrame, accession_to_ensembl: dict[str, str],
                             ensembl_to_entrez: dict[str, list[str]]) -> tuple[pd.Series, list[str]]:
    """UniProt lacks a GeneID xref for some real genes; recover it via HPA's Ensembl ID."""
    filled = proteins["entrez_ids"].copy()
    recovered: list[str] = []
    for i, (accession, ids) in enumerate(zip(proteins["accession"], proteins["entrez_ids"])):
        fallback = ensembl_to_entrez.get(accession_to_ensembl.get(accession, ""), [])
        if not ids and fallback:
            filled.iat[i] = fallback
            recovered.append(accession)
    return filled, recovered


def paper_counts(gene2pubmed: pd.DataFrame, boundary: int, steps: StepLog) -> pd.Series:
    """Distinct pre-T0 PMIDs per human GeneID, excluding large-scale screens."""
    links = gene2pubmed[["gene_id", "pmid"]].drop_duplicates()
    steps.add("gene2pubmed", "taxon 9606, distinct links", len(gene2pubmed), len(links))
    genes_per_pmid = links.groupby("pmid")["gene_id"].transform("size")
    links = steps.filter(links, "gene2pubmed",
                         f"PMIDs with <= {config.MAX_GENES_PER_PMID} human genes",
                         genes_per_pmid <= config.MAX_GENES_PER_PMID)
    links = steps.filter(links, "gene2pubmed", f"PMID <= {boundary}", links["pmid"] <= boundary)
    return links.groupby("gene_id")["pmid"].nunique()


def protein_paper_counts(proteins: pd.DataFrame, gene_counts: pd.Series) -> pd.Series:
    # Max over GeneIDs (user decision): gene copies such as histone clusters share papers,
    # so the best-studied copy represents the protein.
    def count(entrez_ids: list[str]) -> float:
        if not entrez_ids:
            return float("nan")
        return float(max(gene_counts.get(int(g), 0) for g in entrez_ids))

    return proteins["entrez_ids"].map(count)


def stratum(papers: float) -> str | None:
    if pd.isna(papers):
        return None  # unmapped proteins are not assumed to be dark
    if papers < config.DARK_MAX_PAPERS:
        return "dark"
    if papers <= config.WELL_STUDIED_MIN_PAPERS:
        return "intermediate"
    return "well-studied"
