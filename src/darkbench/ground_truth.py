import pandas as pd

from darkbench import config

NAMESPACE_ORDER = ["MF", "BP", "CC"]


def build_ground_truth(t0: pd.DataFrame, t1: pd.DataFrame) -> pd.DataFrame:
    """Terms new at T1 per protein and namespace, labelled NK, LK or PK.

    Both inputs are propagated, root-free (accession, namespace, go_id) tables.
    """
    known = t0[["accession", "namespace", "go_id"]].drop_duplicates()
    merged = t1[["accession", "namespace", "go_id"]].drop_duplicates().merge(
        known, how="left", indicator=True
    )
    new = merged[merged["_merge"] == "left_only"].drop(columns="_merge")
    # Snapshot difference, not the GAF date column, which does not record first assertion.
    t0_any = set(known["accession"])
    t0_namespace = set(zip(known["accession"], known["namespace"]))
    new = new.assign(
        knowledge_type=[
            "NK" if acc not in t0_any else ("PK" if (acc, ns) in t0_namespace else "LK")
            for acc, ns in zip(new["accession"], new["namespace"])
        ]
    )
    return new.sort_values(["accession", "namespace", "go_id"]).reset_index(drop=True)


def check_no_t0_terms(ground_truth: pd.DataFrame, t0: pd.DataFrame) -> int:
    overlap = ground_truth.merge(t0, on=["accession", "namespace", "go_id"])
    return len(overlap)


def check_exclusive_types(ground_truth: pd.DataFrame) -> int:
    types = ground_truth.groupby(["accession", "namespace"])["knowledge_type"].nunique()
    return int((types > 1).sum())


def check_no_roots(ground_truth: pd.DataFrame) -> int:
    return int(ground_truth["go_id"].isin(config.ROOT_TERMS).sum())


def check_no_empty_sets(ground_truth: pd.DataFrame) -> int:
    # A protein/namespace only appears if it has rows, so an empty set shows up as a
    # missing or blank GO ID.
    return int(ground_truth["go_id"].isna().sum() + (ground_truth["go_id"] == "").sum())


def has_exp_t0(t0: pd.DataFrame, accessions: pd.Series) -> pd.DataFrame:
    present = set(zip(t0["accession"], t0["namespace"]))
    return pd.DataFrame({
        f"has_exp_t0_{ns.lower()}": [(acc, ns) in present for acc in accessions]
        for ns in NAMESPACE_ORDER
    })
