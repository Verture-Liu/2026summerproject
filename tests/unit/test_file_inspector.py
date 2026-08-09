from research_agent.files.inspector import inspect_file


def test_inspect_csv_returns_columns(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text("sample,value\nA,1\n", encoding="utf-8")
    summary = inspect_file(path)
    assert summary.format == "csv"
    assert summary.columns == ["sample", "value"]


def test_inspector_uses_fastq_content_when_extension_is_csv(tmp_path):
    path = tmp_path / "misnamed.csv"
    path.write_text("@read1\nACGT\n+\n!!!!\n", encoding="utf-8")

    summary = inspect_file(path)

    assert summary.format == "fastq"
    assert summary.record_count == 1


def test_inspector_rejects_malformed_fastq_content(tmp_path):
    path = tmp_path / "broken.fastq"
    path.write_text("not-a-header\nACGT\nnot-a-plus\n!!!\n", encoding="utf-8")

    summary = inspect_file(path)

    assert summary.format == "unknown"


def test_inspector_reads_gzipped_fastq_signature(tmp_path):
    import gzip

    path = tmp_path / "reads.fastq.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write("@read1\nACGT\n+\n!!!!\n")

    summary = inspect_file(path)

    assert summary.format == "fastq"
    assert summary.record_count == 1


def test_inspector_marks_empty_csv_as_unknown(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_bytes(b"")

    summary = inspect_file(path)

    assert summary.format == "unknown"


def test_inspector_rejects_fastq_with_malformed_record_after_first_hundred(tmp_path):
    path = tmp_path / "late_broken.fastq"
    valid = "".join(f"@r{i}\nACGT\n+\n!!!!\n" for i in range(100))
    path.write_text(valid + "broken\nACGT\n+\n!!!\n", encoding="utf-8")

    summary = inspect_file(path)

    assert summary.format == "unknown"
