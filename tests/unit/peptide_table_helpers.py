from pathlib import Path

import pandas as pd


def write_table(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "peptides.csv"
    pd.DataFrame(rows, columns=["label", "sequence"]).to_csv(path, index=False)
    return path
