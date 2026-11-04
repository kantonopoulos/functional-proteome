from pathlib import Path

import pandas as pd
import pytest

from darkbench import ground_truth, ontology

TOY_OBO = Path(__file__).parent / "toy.obo"

# P1 is PK in MF, P2 is LK in BP (known in CC), P3 is NK in CC.
T0_ROWS = [("P1", "GO:0000001"), ("P2", "GO:0000020")]
T1_ROWS = [
    ("P1", "GO:0000001"),
    ("P1", "GO:0000099"),  # alt_id of GO:0000002
    ("P2", "GO:0000020"),
    ("P2", "GO:0000098"),  # obsolete, replaced_by GO:0000011
    ("P2", "GO:0000097"),  # obsolete, no replacement
    ("P2", "GO:9999999"),  # not in the T0 ontology
    ("P3", "GO:0000020"),
    ("P3", "GO:0005575"),  # root
]


@pytest.fixture(scope="module")
def onto() -> ontology.Ontology:
    return ontology.load_ontology(TOY_OBO)


def frame(rows: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["accession", "go_id"])


def terms(df: pd.DataFrame, accession: str, namespace: str) -> set[str]:
    sel = df[(df["accession"] == accession) & (df["namespace"] == namespace)]
    return set(sel["go_id"])


def test_alt_id_and_obsolete_mapping(onto: ontology.Ontology) -> None:
    assert ontology.map_term("GO:0000099", onto) == ("GO:0000002", "alt_id")
    assert ontology.map_term("GO:0000098", onto) == ("GO:0000011", "obsolete_replaced")
    assert ontology.map_term("GO:0000097", onto) == (None, "obsolete_unmapped")
    assert ontology.map_term("GO:9999999", onto) == (None, "absent")
    mapped, _ = ontology.map_terms(frame(T1_ROWS), onto)
    assert set(mapped["go_id"]) == {"GO:0000001", "GO:0000002", "GO:0000020", "GO:0000011", "GO:0005575"}


def test_propagation_uses_is_a_and_part_of_only(onto: ontology.Ontology) -> None:
    prop = ontology.propagate(frame([("P9", "GO:0000012"), ("P9", "GO:0000002")]), onto)
    assert terms(prop, "P9", "BP") == {"GO:0000012", "GO:0000010"}
    assert terms(prop, "P9", "MF") == {"GO:0000002", "GO:0000001"}
    regulator = ontology.propagate(frame([("P8", "GO:0000013")]), onto)
    assert terms(regulator, "P8", "BP") == {"GO:0000013"}
    assert ontology.unclosed_terms(prop, onto) == 0


def test_roots_removed(onto: ontology.Ontology) -> None:
    prop = ontology.propagate(frame([("P3", "GO:0000020"), ("P3", "GO:0005575")]), onto)
    assert set(prop["go_id"]) == {"GO:0000020"}


def build(onto: ontology.Ontology) -> tuple[pd.DataFrame, pd.DataFrame]:
    t0 = ontology.propagate(ontology.map_terms(frame(T0_ROWS), onto)[0], onto)
    t1 = ontology.propagate(ontology.map_terms(frame(T1_ROWS), onto)[0], onto)
    return t0, ground_truth.build_ground_truth(t0, t1)


def test_delta_contains_only_new_terms(onto: ontology.Ontology) -> None:
    t0, gt = build(onto)
    assert terms(gt, "P1", "MF") == {"GO:0000002"}
    assert terms(gt, "P2", "BP") == {"GO:0000011", "GO:0000010"}
    assert terms(gt, "P3", "CC") == {"GO:0000020"}
    assert terms(gt, "P2", "CC") == set()
    assert ground_truth.check_no_t0_terms(gt, t0) == 0
    assert ground_truth.check_no_roots(gt) == 0
    assert ground_truth.check_no_empty_sets(gt) == 0


def test_knowledge_types(onto: ontology.Ontology) -> None:
    _, gt = build(onto)
    types = gt.groupby(["accession", "namespace"])["knowledge_type"].unique().map(list).to_dict()
    assert types == {("P1", "MF"): ["PK"], ("P2", "BP"): ["LK"], ("P3", "CC"): ["NK"]}
    assert ground_truth.check_exclusive_types(gt) == 0
