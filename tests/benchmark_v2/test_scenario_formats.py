from pathlib import Path

from analysis.benchmark_v2.scenarios import _format_for


def test_benchmark_format_detection_supports_common_fasta_suffixes():
    for name in ("reads.fasta", "reads.fa", "reads.fna", "reads.fasta.gz"):
        assert _format_for(Path(name)) == "fasta"
