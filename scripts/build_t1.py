"""Build the T0 snapshot, T1 ground truth and study-level strata end to end."""
import json
import logging
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from darkbench import annotations, config, download, ground_truth, literature, ontology, proteins  # noqa: E402
from darkbench.report import Checks, StepLog, markdown_table, render_report  # noqa: E402

log = logging.getLogger("build_t1")


def check_sources(manifest: dict, checks: Checks) -> tuple[dict, dict]:
    for name, entry in manifest.items():
        path = config.RAW_DIR / entry["file"]
        if path.suffix == ".gz":
            checks.add(f"gzip opens: {entry['file']}", download.gzip_opens(path), f"md5 {entry['md5']}")
    t0_header = annotations.read_gaf_header(config.RAW_DIR / config.RAW_FILES["gaf_t0"])
    t1_header = annotations.read_gaf_header(config.RAW_DIR / config.RAW_FILES["gaf_t1"])
    for label, header in [("T0", t0_header), ("T1", t1_header)]:
        print(f"{label} GAF: gaf-version {header['gaf_version']}, GOA date-generated "
              f"{header['goa_date_generated']}, all date-generated {header['all_date_generated']}")
    t0_goa = date.fromisoformat(t0_header["goa_date_generated"][:10])
    lag = (config.T0_DATE - t0_goa).days
    checks.add("T0 GOA release on or before 2023-01-01", t0_goa <= config.T0_DATE, f"{t0_goa}")
    checks.add(f"T0 GOA release within {config.MAX_T0_GOA_LAG_DAYS} days of T0",
               0 <= lag <= config.MAX_T0_GOA_LAG_DAYS,
               f"{t0_goa} is {lag} days before T0; accepted by user (EBI unreachable)",
               accepted=config.T0_GOA_LAG_ACCEPTED)
    t1_goa = date.fromisoformat(t1_header["goa_date_generated"][:10])
    checks.add("T1 GOA release after T0", t1_goa > config.T0_DATE, f"{t1_goa}")
    return t0_header, t1_header


def check_ontology(onto: ontology.Ontology, checks: Checks) -> None:
    print(f"GO ontology data-version: {onto.data_version}")
    checks.add("GO ontology is the 2023-01-01 release",
               onto.data_version == f"releases/{config.GO_RELEASE_T0}", onto.data_version)


def load_gaf(key: str, version: str, label: str, checks: Checks) -> pd.DataFrame:
    gaf, bad = annotations.read_gaf(config.RAW_DIR / config.RAW_FILES[key], version)
    checks.add(f"{label} GAF {version} rows have {annotations.GAF_COLUMN_COUNTS[version]} columns",
               bad == 0, f"{len(gaf)} rows read, {bad} malformed")
    return gaf


def raw_t0_accessions(gaf: pd.DataFrame, sec_map: dict[str, str]) -> set[str]:
    ids = gaf.loc[gaf["db"] == "UniProtKB", "db_object_id"].map(proteins.canonical_accession)
    return {sec_map.get(i, i) for i in ids}


def map_and_propagate(df: pd.DataFrame, label: str, onto: ontology.Ontology,
                      steps: StepLog) -> tuple[pd.DataFrame, pd.DataFrame]:
    mapped, counts = ontology.map_terms(df, onto)
    steps.add(label, "GO term in T0 ontology (after alt_id/obsolete mapping)", len(df), len(mapped))
    propagated = ontology.propagate(mapped, onto)
    steps.add(label, "propagated (protein, term) pairs, roots removed",
              len(mapped[["accession", "go_id"]].drop_duplicates()), len(propagated))
    return propagated, counts.assign(snapshot=label)


def summarise(gt: pd.DataFrame, strata: pd.DataFrame) -> pd.DataFrame:
    per_protein = gt[["accession", "namespace", "knowledge_type"]].drop_duplicates()
    per_protein = per_protein.merge(strata, on="accession", how="left")
    per_protein["stratum"] = per_protein["stratum"].fillna("unassigned")
    summary = (per_protein.groupby(["namespace", "knowledge_type", "stratum"]).size()
               .rename("proteins").reset_index())
    order = {"MF": 0, "BP": 1, "CC": 2}
    return summary.sort_values(["namespace", "knowledge_type", "stratum"],
                               key=lambda s: s.map(order) if s.name == "namespace" else s)


def spot_check(table: pd.DataFrame) -> pd.DataFrame:
    named = table[table["gene"].isin(config.SPOT_CHECK_GENES)].assign(selection="named")
    random_rows = [
        group.sample(min(config.SPOT_CHECK_PER_STRATUM, len(group)), random_state=config.RANDOM_SEED)
        .assign(selection=f"random {stratum}")
        for stratum, group in table.dropna(subset=["stratum"]).groupby("stratum")
    ]
    cols = ["selection", "accession", "gene", "entrez_id", "pmid_count_t0", "stratum", "tdl"]
    return pd.concat([named, *random_rows])[cols]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    steps, checks = StepLog(), Checks()

    # 1. Download and source checks
    manifest = download.download_all()
    t0_header, t1_header = check_sources(manifest, checks)
    onto = ontology.load_ontology(config.RAW_DIR / config.RAW_FILES["go_obo_t0"])
    check_ontology(onto, checks)

    # Protein universe
    uniprot = proteins.parse_uniprot_flat(config.RAW_DIR / config.RAW_FILES["uniprot_sprot_human"])
    universe = proteins.swissprot_universe(uniprot)
    steps.add("proteins", "Swiss-Prot human at T1", len(uniprot), len(universe))
    kept = proteins.sequence_filter(universe, config.T0_DATE)
    steps.add("proteins", "sequence last modified <= 2023-01-01", len(universe), len(kept))
    sec_map, ambiguous = proteins.secondary_map(universe)
    universe_ids, kept_ids = set(universe["accession"]), set(kept["accession"])

    # 2. Parse and filter annotations
    t0_raw = load_gaf("gaf_t0", t0_header["gaf_version"], "T0", checks)
    t1_raw = load_gaf("gaf_t1", t1_header["gaf_version"], "T1", checks)
    filtered, mapping_stats = {}, {}
    for label, raw in [("T0", t0_raw), ("T1", t1_raw)]:
        filtered[label], mapping_stats[label] = annotations.filter_annotations(
            raw, label, steps, sec_map, ambiguous, universe_ids, kept_ids)
        df = filtered[label]
        checks.add(f"{label} retained rows are taxon 9606 and UniProtKB",
                   bool((df["db"] == "UniProtKB").all()
                        and (df["taxon"].map(annotations.primary_taxon) == "taxon:9606").all()),
                   f"{len(df)} rows")
        print(f"{label} accession mapping: {mapping_stats[label]}")

    # 3. Ontology mapping and propagation
    t0_prop, t0_terms = map_and_propagate(filtered["T0"], "T0", onto, steps)
    t1_prop, t1_terms = map_and_propagate(filtered["T1"], "T1", onto, steps)
    term_mapping = pd.concat([t0_terms, t1_terms])[["snapshot", "status", "rows", "terms"]]
    print(term_mapping.to_string(index=False))
    for label, prop in [("T0", t0_prop), ("T1", t1_prop)]:
        missing = ontology.unclosed_terms(prop, onto)
        checks.add(f"{label} propagated sets closed under parents (all {prop['accession'].nunique()} proteins)",
                   missing == 0, f"{missing} missing parent links")
    dropped = t1_terms[t1_terms["status"].isin(["absent", "obsolete_unmapped"])]
    checks.add("Report mapped obsolete / alt_id / dropped T1 terms", True,
               "; ".join(f"{r.snapshot} {r.status}: {r.rows} rows, {r.terms} terms"
                         for r in term_mapping.itertuples() if r.status != "current"))
    log.info("T1 terms dropped (not in T0 ontology): %d rows, %d terms",
             int(dropped["rows"].sum()), int(dropped["terms"].sum()))

    # 4. Ground truth
    gt = ground_truth.build_ground_truth(t0_prop, t1_prop)
    steps.add("ground truth", "T1 propagated pairs -> new at T1", len(t1_prop), len(gt))
    n = ground_truth.check_no_t0_terms(gt, t0_prop)
    checks.add("No ground-truth term existed at T0 (after propagation)", n == 0, f"{n} overlapping")
    n = ground_truth.check_exclusive_types(gt)
    checks.add("NK/LK/PK mutually exclusive per protein and namespace", n == 0, f"{n} conflicts")
    n = ground_truth.check_no_roots(gt)
    checks.add("No root terms in ground truth", n == 0, f"{n} root rows")
    n = ground_truth.check_no_empty_sets(gt)
    checks.add("No empty ground-truth sets", n == 0, f"{n} empty")
    # The T0 file covers the reference proteome only; a protein missing from it entirely
    # would look NK because of file scope rather than knowledge.
    nk = set(gt.loc[gt["knowledge_type"] == "NK", "accession"])
    absent = sorted(nk - raw_t0_accessions(t0_raw, sec_map))
    checks.add("NK proteins present in the T0 GAF with any evidence (scope check)",
               len(absent) == 0, f"{len(absent)} of {len(nk)} NK proteins absent from T0 file: "
               + ", ".join(absent[:30]))

    # 5. Literature strata
    boundary = literature.find_pmid_boundary(config.PMID_CUTOFF_DATE)
    print(f"PMID boundary: {boundary['pmid_boundary']} (Entrez date {boundary['boundary_entrez_date']})")
    checks.add("PMID boundary entry date on or before 2022-12-31",
               boundary["boundary_entrez_date"][:10].replace("/", "-") <= config.PMID_CUTOFF_DATE.isoformat(),
               f"PMID {boundary['pmid_boundary']}, Entrez date {boundary['boundary_entrez_date']}")
    g2p = literature.read_gene2pubmed(config.RAW_DIR / config.RAW_FILES["gene2pubmed"])
    gene_counts = literature.paper_counts(g2p, boundary["pmid_boundary"], steps)

    table = kept[["accession", "gene"]].copy()
    table["entrez_id"] = kept["entrez_ids"].map(";".join)
    table["pmid_count_t0"] = literature.protein_paper_counts(kept, gene_counts).astype("Int64")
    table["stratum"] = table["pmid_count_t0"].map(literature.stratum)
    unmapped = table[table["entrez_id"] == ""]
    share = len(unmapped) / len(table)
    print(f"Proteins without GeneID: {len(unmapped)} / {len(table)} ({share:.1%})")
    checks.add("Proteins without GeneID get no stratum",
               bool(unmapped["stratum"].isna().all()),
               f"{len(unmapped)} of {len(table)} ({share:.1%}) unmapped")

    pharos = pd.read_csv(config.RAW_DIR / config.RAW_FILES["pharos_tdl"], sep="\t")
    pharos["accession"] = pharos["uniprot"].map(lambda a: sec_map.get(a, a))
    tdl = pharos.drop_duplicates("accession").set_index("accession")["tdl"]
    table["tdl"] = table["accession"].map(tdl)
    table["tdl_source"] = manifest["pharos_tdl"]["release"]
    table = pd.concat([table, ground_truth.has_exp_t0(t0_prop, table["accession"])], axis=1)

    spot = spot_check(table)
    print(spot.to_string(index=False))
    checks.add("Spot-check genes found", set(config.SPOT_CHECK_GENES) <= set(spot["gene"]),
               ", ".join(config.SPOT_CHECK_GENES))

    # Outputs
    gt.to_csv(config.PROCESSED_DIR / "ground_truth_t1.tsv", sep="\t", index=False)
    t0_prop.to_csv(config.PROCESSED_DIR / "annotations_t0.tsv", sep="\t", index=False)
    table.to_csv(config.PROCESSED_DIR / "proteins.tsv", sep="\t", index=False)
    summary = summarise(gt, table[["accession", "stratum"]])
    summary.to_csv(config.PROCESSED_DIR / "test_set_summary.tsv", sep="\t", index=False)

    dark_nk_lk = int(summary[(summary["stratum"] == "dark")
                             & summary["knowledge_type"].isin(["NK", "LK"])]["proteins"].sum())
    if dark_nk_lk < config.GO_NO_GO_MIN_DARK_NK_LK:
        go_no_go = (f"> **NO-GO FLAG: only {dark_nk_lk} dark proteins in NK+LK across all namespaces "
                    f"(threshold {config.GO_NO_GO_MIN_DARK_NK_LK}).**")
    else:
        go_no_go = (f"> **GO: {dark_nk_lk} dark proteins in NK+LK summed across namespaces "
                    f"(threshold {config.GO_NO_GO_MIN_DARK_NK_LK}).**")

    provenance = {
        "sources": manifest,
        "gaf_headers": {"T0": t0_header, "T1": t1_header},
        "go_ontology_data_version": onto.data_version,
        "pmid_boundary": boundary,
        "accession_mapping": mapping_stats,
        "config": {k: (v.isoformat() if isinstance(v, date) else v)
                   for k, v in vars(config).items()
                   if k.isupper() and not isinstance(v, Path)},
        "build_date": date.today().isoformat(),
    }
    (config.PROCESSED_DIR / "provenance.json").write_text(json.dumps(provenance, indent=2, default=str))

    sources = pd.DataFrame([
        {"source": k, "file": v["file"], "release/date": v.get("release", ""),
         "md5": v["md5"], "downloaded": v["download_date"], "url": v["url"]}
        for k, v in manifest.items()
    ])
    sources.loc[sources["source"] == "gaf_t0", "release/date"] = (
        f"GO release {config.GO_RELEASE_T0}; GOA date-generated {t0_header['goa_date_generated']}")
    sources.loc[sources["source"] == "gaf_t1", "release/date"] = (
        f"GO release {config.GO_RELEASE_T1}; GOA date-generated {t1_header['goa_date_generated']}")
    sources.loc[sources["source"] == "go_obo_t0", "release/date"] = onto.data_version
    notes = [
        "EBI's GOA FTP was unreachable, so both GAFs come from the GO Consortium release archive "
        "(user decision). The T0 file is GOA human 2022-11-17 plus PAINT IBA rows; IBA is not "
        "an allowed evidence code, so those rows are filtered out.",
        f"T0 GOA release is {(config.T0_DATE - date.fromisoformat(t0_header['goa_date_generated'][:10])).days} "
        "days before T0, over the 6-week limit; accepted by the user.",
        "T0 file covers the UniProt reference proteome (goa_human); T1 file covers all UniProt "
        "human entries. Both are restricted to the same Swiss-Prot universe; see the scope check.",
        "Proteins with several GeneIDs take the max paper count over their GeneIDs (user decision).",
        "Secondary accessions that map to several current entries are dropped (user decision): "
        f"T0 {mapping_stats['T0']['ambiguous_accessions_dropped']}, "
        f"T1 {mapping_stats['T1']['ambiguous_accessions_dropped']}.",
        "The pre-T0 TCRD download host was unreachable, so TDL is the current Pharos value "
        f"({manifest['pharos_tdl']['release']}) and reflects knowledge gained after T0.",
        f"PMID boundary: {boundary['pmid_boundary']} (Entrez date {boundary['boundary_entrez_date']}).",
        f"Proteins without a GeneID: {len(unmapped)} of {len(table)} ({share:.1%}); listed at the end.",
    ]
    report = render_report(go_no_go, sources, steps.frame(), term_mapping, summary,
                           checks.frame(), spot, notes)
    report += ("\n## Proteins without a GeneID mapping (no stratum)\n\n<details><summary>"
               f"{len(unmapped)} proteins</summary>\n\n"
               + ", ".join(f"{a} ({g})" for a, g in zip(unmapped["accession"], unmapped["gene"].fillna("-")))
               + "\n\n</details>\n")
    (config.REPORTS_DIR / "t1_report.md").write_text(report)

    print(go_no_go)
    print(markdown_table(checks.frame()))
    if checks.failed():
        print("FAILED CHECKS:", checks.failed())
        sys.exit(1)


if __name__ == "__main__":
    main()
