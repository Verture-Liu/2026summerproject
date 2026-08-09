import gzip
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


def _open_maybe_gzip(path: Path):
    with path.open("rb") as handle:
        gzip_encoded = handle.read(2) == b"\x1f\x8b"
    if gzip_encoded:
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def _inspect_fastq_content(path: Path) -> tuple[bool, int | None]:
    records = 0
    try:
        with _open_maybe_gzip(path) as handle:
            while True:
                header = handle.readline()
                if not header:
                    return records > 0, records if records else None
                sequence = handle.readline().rstrip("\r\n")
                plus = handle.readline()
                quality = handle.readline().rstrip("\r\n")
                if (
                    not header.startswith("@")
                    or not sequence
                    or not plus.startswith("+")
                    or len(sequence) != len(quality)
                ):
                    return False, None
                records += 1
    except (OSError, UnicodeError):
        return False, None


def inspect_file(path: Path) -> FileSummary:
    suffixes = "".join(path.suffixes).lower()
    common = {"name": path.name, "size_bytes": path.stat().st_size}
    looks_like_fastq, fastq_records = _inspect_fastq_content(path)
    if looks_like_fastq:
        return FileSummary(format="fastq", record_count=fastq_records, **common)
    if suffixes.endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz")):
        return FileSummary(format="unknown", **common)
    if suffixes.endswith(".csv"):
        try:
            frame = pd.read_csv(path, nrows=100)
        except (
            OSError,
            UnicodeError,
            pd.errors.ParserError,
            pd.errors.EmptyDataError,
        ):
            return FileSummary(format="unknown", **common)
        return FileSummary(format="csv", columns=list(frame.columns), **common)
    if suffixes.endswith((".tsv", ".txt")):
        frame = pd.read_csv(path, sep="\t", nrows=100)
        return FileSummary(format="tsv", columns=list(frame.columns), **common)
    if suffixes.endswith((".xlsx", ".xls")):
        frame = pd.read_excel(path, nrows=100)
        return FileSummary(format="xlsx", columns=list(frame.columns), **common)
    if suffixes.endswith((".fasta", ".fa", ".faa", ".fna")):
        return FileSummary(format="fasta", **common)
    if suffixes.endswith((".json",)):
        return FileSummary(format="json", **common)
    if suffixes.endswith((".nwk", ".newick", ".tree")):
        return FileSummary(format="newick", **common)
    return FileSummary(format="unknown", **common)
