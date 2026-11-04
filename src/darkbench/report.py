import logging
from dataclasses import dataclass, field

import pandas as pd

log = logging.getLogger(__name__)


@dataclass
class StepLog:
    rows: list[dict] = field(default_factory=list)

    def add(self, table: str, step: str, before: int, after: int) -> None:
        log.info("[%s] %s: %d -> %d", table, step, before, after)
        self.rows.append({"table": table, "step": step, "before": before, "after": after,
                          "removed": before - after})

    def filter(self, df: pd.DataFrame, table: str, step: str, keep: pd.Series) -> pd.DataFrame:
        out = df[keep].reset_index(drop=True)
        self.add(table, step, len(df), len(out))
        return out

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)


@dataclass
class Checks:
    rows: list[dict] = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: str, accepted: bool = False) -> None:
        status = "PASS" if passed else ("ACCEPTED" if accepted else "FAIL")
        log.info("CHECK %s: %s (%s)", status, name, detail)
        self.rows.append({"check": name, "result": status, "detail": detail})

    def failed(self) -> list[str]:
        return [r["check"] for r in self.rows if r["result"] == "FAIL"]

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)


def markdown_table(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |")
    return "\n".join(lines)


def render_report(
    go_no_go: str,
    sources: pd.DataFrame,
    steps: pd.DataFrame,
    term_mapping: pd.DataFrame,
    summary: pd.DataFrame,
    checks: pd.DataFrame,
    spot_check: pd.DataFrame,
    notes: list[str],
) -> str:
    sections = [
        "# T1 GO label sets: build report",
        go_no_go,
        "## Source versions and dates\n\n" + markdown_table(sources),
        "## Notes and deviations\n\n" + "\n".join(f"- {n}" for n in notes),
        "## Row counts per filter step\n\n" + markdown_table(steps),
        "## GO term mapping onto the T0 ontology\n\n" + markdown_table(term_mapping),
        "## Test set summary (proteins per namespace x knowledge type x stratum)\n\n"
        + markdown_table(summary),
        "## Checks\n\n" + markdown_table(checks),
        "## Spot check for manual review\n\n" + markdown_table(spot_check),
    ]
    return "\n\n".join(sections) + "\n"
