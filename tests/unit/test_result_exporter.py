from pathlib import Path
import json

from research_agent.execution.exporter import export_task_results


def test_export_places_final_fasta_in_final_outputs_and_records_in_subdirectory(tmp_path):
    task_dir = tmp_path / "task"
    destination = tmp_path / "chosen"
    (task_dir / "logs").mkdir(parents=True)
    destination.mkdir()
    final_fasta = task_dir / "steps" / "step_01" / "filtered.fasta"
    final_fasta.parent.mkdir(parents=True)
    final_fasta.write_text(">a\nAAAA\n", encoding="utf-8")
    (task_dir / "report.html").write_text("<p>report</p>", encoding="utf-8")
    (task_dir / "manifest.json").write_text("{}", encoding="utf-8")
    (task_dir / "logs" / "run.log").write_text("ok", encoding="utf-8")

    summary = export_task_results(
        outputs=[final_fasta],
        task_dir=task_dir,
        destination=destination,
        task_id="12345678abcdef",
    )

    assert (summary.final_outputs_dir / "filtered.fasta").exists()
    records = summary.result_dir / "ResearchAgent Records"
    assert (records / "report.html").exists()
    assert (records / "manifest.json").exists()
    assert (records / "logs" / "run.log").exists()
    assert summary.final_files[0].path == summary.final_outputs_dir / "filtered.fasta"


def test_export_copies_supported_final_outputs_and_never_overwrites(tmp_path):
    task_dir = tmp_path / "task"
    destination = tmp_path / "chosen"
    task_dir.mkdir()
    destination.mkdir()
    fasta = task_dir / "result.fasta"
    csv = task_dir / "result.csv"
    fasta.write_text(">new\nAAAA\n", encoding="utf-8")
    csv.write_text("a,b\n1,2\n", encoding="utf-8")
    (destination / "result.fasta").write_text(">old\nTTTT\n", encoding="utf-8")

    summary = export_task_results(
        outputs=[fasta, csv],
        task_dir=task_dir,
        destination=destination,
        task_id="12345678abcdef",
    )

    assert (destination / "result.fasta").read_text(encoding="utf-8") == ">old\nTTTT\n"
    assert (summary.final_outputs_dir / "result.fasta").read_text(encoding="utf-8") == ">new\nAAAA\n"
    assert (summary.final_outputs_dir / "result.csv").read_text(encoding="utf-8") == "a,b\n1,2\n"
    assert [item.path for item in summary.final_files] == [
        summary.final_outputs_dir / "result.fasta",
        summary.final_outputs_dir / "result.csv",
    ]


def test_export_copies_fastqc_html_and_zip_reports(tmp_path):
    task_dir = tmp_path / "task"
    destination = tmp_path / "chosen"
    task_dir.mkdir()
    destination.mkdir()
    html = task_dir / "minimal_reads_fastqc.html"
    zip_report = task_dir / "minimal_reads_fastqc.zip"
    html.write_text("<html>FastQC</html>", encoding="utf-8")
    zip_report.write_bytes(b"fake zip")

    summary = export_task_results(
        outputs=[html, zip_report],
        task_dir=task_dir,
        destination=destination,
        task_id="12345678abcdef",
    )

    assert (summary.final_outputs_dir / "minimal_reads_fastqc.html").read_text(
        encoding="utf-8"
    ) == "<html>FastQC</html>"
    assert (summary.final_outputs_dir / "minimal_reads_fastqc.zip").read_bytes() == b"fake zip"
    assert [item.path for item in summary.final_files] == [
        summary.final_outputs_dir / "minimal_reads_fastqc.html",
        summary.final_outputs_dir / "minimal_reads_fastqc.zip",
    ]


def test_export_copies_sequence_fastq_and_gzip_outputs(tmp_path):
    task_dir = tmp_path / "task"
    destination = tmp_path / "chosen"
    task_dir.mkdir()
    destination.mkdir()
    fastq = task_dir / "sampled.fastq"
    gzipped = task_dir / "reads.fastq.gz"
    fastq.write_text("@r1\nACGT\n+\n!!!!\n", encoding="utf-8")
    gzipped.write_bytes(b"fake gzip")

    summary = export_task_results(
        outputs=[fastq, gzipped],
        task_dir=task_dir,
        destination=destination,
        task_id="12345678abcdef",
    )

    assert (summary.final_outputs_dir / "sampled.fastq").exists()
    assert (summary.final_outputs_dir / "reads.fastq.gz").exists()
    assert [item.path for item in summary.final_files] == [
        summary.final_outputs_dir / "sampled.fastq",
        summary.final_outputs_dir / "reads.fastq.gz",
    ]


def test_export_copies_alignment_and_metagenome_outputs(tmp_path):
    task_dir = tmp_path / "task"
    destination = tmp_path / "chosen"
    task_dir.mkdir()
    destination.mkdir()
    outputs = [
        task_dir / "aligned.sam",
        task_dir / "sorted.bam",
        task_dir / "sorted.bam.bai",
        task_dir / "stats.txt",
        task_dir / "malt_output.rma6",
        task_dir / "metaphlan.bowtie2.bz2",
        task_dir / "coverage.bed",
    ]
    for path in outputs:
        path.write_text("ok", encoding="utf-8")

    summary = export_task_results(
        outputs=outputs,
        task_dir=task_dir,
        destination=destination,
        task_id="12345678abcdef",
    )

    assert [item.path.name for item in summary.final_files] == [
        "aligned.sam",
        "sorted.bam",
        "sorted.bam.bai",
        "stats.txt",
        "malt_output.rma6",
        "metaphlan.bowtie2.bz2",
        "coverage.bed",
    ]


def test_export_uses_manifest_to_copy_intermediate_deliverables(tmp_path):
    task_dir = tmp_path / "task"
    destination = tmp_path / "chosen"
    stats_dir = task_dir / "steps" / "step_05"
    chart_dir = task_dir / "steps" / "step_06"
    export_dir = task_dir / "steps" / "step_07"
    stats_dir.mkdir(parents=True)
    chart_dir.mkdir(parents=True)
    export_dir.mkdir(parents=True)
    statistics = stats_dir / "peptide_statistics.json"
    lengths = stats_dir / "length_distribution.csv"
    chart = chart_dir / "length_histogram.png"
    final_csv = export_dir / "cleaned_peptides.csv"
    statistics.write_text("{}", encoding="utf-8")
    lengths.write_text("length,count\n13,2\n", encoding="utf-8")
    chart.write_bytes(b"png")
    final_csv.write_text("label,sequence\n1,AAAA\n", encoding="utf-8")
    (task_dir / "manifest.json").write_text(
        json.dumps(
            {
                "steps": [
                    {
                        "id": "step_05",
                        "skill": "peptide_statistics",
                        "outputs": [{"path": str(statistics)}, {"path": str(lengths)}],
                    },
                    {
                        "id": "step_06",
                        "skill": "peptide_chart",
                        "outputs": [{"path": str(chart)}],
                    },
                    {
                        "id": "step_07",
                        "skill": "peptide_csv_export",
                        "outputs": [{"path": str(final_csv)}],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    summary = export_task_results(
        outputs=[final_csv],
        task_dir=task_dir,
        destination=destination,
        task_id="12345678abcdef",
    )

    assert sorted(item.path.name for item in summary.final_files) == [
        "cleaned_peptides.csv",
        "length_distribution.csv",
        "length_histogram.png",
        "peptide_statistics.json",
    ]


def test_export_creates_run_folder_with_final_and_step_outputs(tmp_path):
    task_dir = tmp_path / "task"
    destination = tmp_path / "chosen"
    normalize_dir = task_dir / "steps" / "step_01"
    stats_dir = task_dir / "steps" / "step_05"
    export_dir = task_dir / "steps" / "step_07"
    normalize_dir.mkdir(parents=True)
    stats_dir.mkdir(parents=True)
    export_dir.mkdir(parents=True)
    destination.mkdir()
    normalized = normalize_dir / "normalized_peptides.csv"
    statistics = stats_dir / "peptide_statistics.json"
    final_csv = export_dir / "cleaned_peptides.csv"
    normalized.write_text("label,sequence\n1,AAAA\n", encoding="utf-8")
    statistics.write_text("{}", encoding="utf-8")
    final_csv.write_text("label,sequence\n1,AAAA\n", encoding="utf-8")
    (task_dir / "report.html").write_text("<p>report</p>", encoding="utf-8")
    (task_dir / "manifest.json").write_text(
        json.dumps(
            {
                "steps": [
                    {
                        "id": "step_01",
                        "skill": "peptide_csv_normalize",
                        "outputs": [{"path": str(normalized)}],
                    },
                    {
                        "id": "step_05",
                        "skill": "peptide_statistics",
                        "outputs": [{"path": str(statistics)}],
                    },
                    {
                        "id": "step_07",
                        "skill": "peptide_csv_export",
                        "outputs": [{"path": str(final_csv)}],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    summary = export_task_results(
        outputs=[statistics, final_csv],
        task_dir=task_dir,
        destination=destination,
        task_id="12345678abcdef",
    )

    assert summary.result_dir.parent == destination
    assert summary.final_outputs_dir == summary.result_dir / "final_outputs"
    assert summary.step_outputs_dir == summary.result_dir / "step_outputs"
    assert summary.records_dir == summary.result_dir / "ResearchAgent Records"
    assert sorted(path.name for path in summary.result_dir.iterdir()) == [
        "ResearchAgent Records",
        "final_outputs",
        "step_outputs",
    ]
    assert (summary.final_outputs_dir / "cleaned_peptides.csv").exists()
    assert (summary.final_outputs_dir / "peptide_statistics.json").exists()
    assert not (summary.final_outputs_dir / "normalized_peptides.csv").exists()
    assert (
        summary.step_outputs_dir
        / "step_01_peptide_csv_normalize"
        / "normalized_peptides.csv"
    ).exists()
    assert (
        summary.step_outputs_dir / "step_05_peptide_statistics" / "peptide_statistics.json"
    ).exists()
    assert (
        summary.step_outputs_dir / "step_07_peptide_csv_export" / "cleaned_peptides.csv"
    ).exists()
