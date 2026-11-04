import logging
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx
import obonet
import pandas as pd

from darkbench import config

log = logging.getLogger(__name__)


@dataclass
class Ontology:
    graph: nx.DiGraph  # edges point child -> parent
    namespace: dict[str, str]
    alt_ids: dict[str, str]
    replaced_by: dict[str, str]
    obsolete: set[str]
    data_version: str
    _ancestors: dict[str, frozenset[str]] = field(default_factory=dict, repr=False)

    def ancestors(self, term: str) -> frozenset[str]:
        if term not in self._ancestors:
            self._ancestors[term] = frozenset(nx.descendants(self.graph, term))
        return self._ancestors[term]

    def parents(self, term: str) -> set[str]:
        return set(self.graph.successors(term))


def load_ontology(path: Path) -> Ontology:
    raw = obonet.read_obo(path, ignore_obsolete=False)
    obsolete = {t for t, d in raw.nodes(data=True) if d.get("is_obsolete") == "true"}
    graph = nx.DiGraph()
    namespace: dict[str, str] = {}
    for term, data in raw.nodes(data=True):
        if term in obsolete or "namespace" not in data:
            continue
        graph.add_node(term)
        namespace[term] = config.NAMESPACES[data["namespace"]]
    for child, parent, relation in raw.edges(keys=True):
        # Only is_a and part_of are safe for transferring annotations to parents.
        if relation in config.PROPAGATION_RELATIONS and child in graph and parent in graph:
            graph.add_edge(child, parent)
    alt_ids = {alt: term for term, data in raw.nodes(data=True) for alt in data.get("alt_id", [])}
    replaced_by = {}
    for term in obsolete:
        targets = raw.nodes[term].get("replaced_by", [])
        # Several replacements would mean guessing which one the curator meant.
        if len(targets) == 1:
            replaced_by[term] = targets[0]
    data_version = raw.graph.get("data-version", "")
    return Ontology(graph, namespace, alt_ids, replaced_by, obsolete, data_version)


def map_term(term: str, onto: Ontology) -> tuple[str | None, str]:
    if term in onto.namespace:
        return term, "current"
    if term in onto.alt_ids and onto.alt_ids[term] in onto.namespace:
        return onto.alt_ids[term], "alt_id"
    if term in onto.replaced_by and onto.replaced_by[term] in onto.namespace:
        return onto.replaced_by[term], "obsolete_replaced"
    if term in onto.obsolete:
        return None, "obsolete_unmapped"
    return None, "absent"


def map_terms(annotations: pd.DataFrame, onto: Ontology) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Map GO IDs onto the T0 ontology and return the kept rows plus per-status counts."""
    mapping = {t: map_term(t, onto) for t in annotations["go_id"].unique()}
    status = annotations["go_id"].map(lambda t: mapping[t][1])
    mapped = annotations.assign(go_id=annotations["go_id"].map(lambda t: mapping[t][0]))
    counts = (
        pd.DataFrame({"status": status, "go_id": annotations["go_id"]})
        .groupby("status")
        .agg(rows=("go_id", "size"), terms=("go_id", "nunique"))
        .reset_index()
    )
    return mapped[mapped["go_id"].notna()].reset_index(drop=True), counts


def propagate(annotations: pd.DataFrame, onto: Ontology) -> pd.DataFrame:
    """Close each protein's terms under is_a/part_of parents; drop roots and uninformative terms."""
    pairs = annotations[["accession", "go_id"]].drop_duplicates()
    rows: list[tuple[str, str]] = []
    for accession, terms in pairs.groupby("accession")["go_id"]:
        closed: set[str] = set(terms)
        for term in terms:
            closed |= onto.ancestors(term)
        rows.extend((accession, t) for t in closed if t not in config.DROPPED_AFTER_PROPAGATION)
    out = pd.DataFrame(rows, columns=["accession", "go_id"])
    out.insert(1, "namespace", out["go_id"].map(onto.namespace))
    return out.sort_values(["accession", "namespace", "go_id"]).reset_index(drop=True)


def unclosed_terms(propagated: pd.DataFrame, onto: Ontology) -> int:
    """Count (protein, term) pairs whose non-root parents are missing from the protein's set."""
    missing = 0
    for _, terms in propagated.groupby("accession")["go_id"]:
        present = set(terms)
        for term in present:
            missing += len(onto.parents(term) - present - config.DROPPED_AFTER_PROPAGATION)
    return missing
