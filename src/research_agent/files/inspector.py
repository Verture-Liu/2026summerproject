from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class FileSummary:
    name: str
    format: str
    size_bytes: int
    columns: list[str] = field(default_factory=list)
    record_count: int | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def inspect_file(path: Path) -> FileSummary:
    suffixes = "".join(path.suffixes).lower()
    common = {"name": path.name, "size_bytes": path.stat().st_size}
    if suffixes.endswith(".csv"):
        frame = pd.read_csv(path, nrows=100)
        return FileSummary(format="csv", columns=list(frame.columns), **common)
    if suffixes.endswith((".tsv", ".txt")):
        frame = pd.read_csv(path, sep="\t", nrows=100)
        return FileSummary(format="tsv", columns=list(frame.columns), **common)
    if suffixes.endswith((".xlsx", ".xls")):
        frame = pd.read_excel(path, nrows=100)
        return FileSummary(format="xlsx", columns=list(frame.columns), **common)
    if suffixes.endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz")):
        return FileSummary(format="fastq", **common)
    if suffixes.endswith((".fasta", ".fa", ".faa", ".fna")):
        return FileSummary(format="fasta", **common)
    if suffixes.endswith((".json",)):
        return FileSummary(format="json", **common)
    if suffixes.endswith((".nwk", ".newick", ".tree")):
        return FileSummary(format="newick", **common)
    return FileSummary(format="unknown", **common)
