from pathlib import Path

import pandas as pd


CANONICAL_COLUMNS = ["label", "sequence"]
CANONICAL_AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"


def read_canonical_table(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, keep_default_na=False)
    if not set(CANONICAL_COLUMNS).issubset(frame.columns):
        raise ValueError("Expected canonical peptide columns: label, sequence")
    return frame.copy()


def write_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def empty_filter_warning(frame: pd.DataFrame) -> list[str]:
    return ["No rows matched the filter."] if frame.empty else []


def describe_lengths(lengths: pd.Series) -> dict:
    if lengths.empty:
        return {"min": None, "median": None, "mean": None, "max": None}
    return {
        "min": int(lengths.min()),
        "median": float(lengths.median()),
        "mean": float(lengths.mean()),
        "max": int(lengths.max()),
    }
