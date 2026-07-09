from __future__ import annotations

import csv
import json
import re
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "Final data"
RAW = ROOT / "data" / "raw" / "reproducibility_cases"
OUT = FINAL / "comparison_figures"


ENA = {
    "ERR15682270": {
        "paper": "Sarhan et al. 2026 Microbiome / PRJEB94382",
        "layout": "PAIRED",
        "scientific_name": "metagenome",
        "fastq_bytes": [3644307, 5363244],
        "read_count": 56122,
        "base_count": 16892722,
        "groups": ["2", "3"],
    },
    "ERR10114877": {
        "paper": "Klapper et al. 2023 Science / PRJEB55583",
        "layout": "PAIRED",
        "scientific_name": "blank sample",
        "fastq_bytes": [7701833, 7169255],
        "read_count": 526070,
        "base_count": 33836230,
        "groups": ["4", "5"],
    },
    "ERR3250149": {
        "paper": "Jensen et al. 2019 Nature Communications / PRJEB30280",
        "layout": "SINGLE",
        "scientific_name": "Betula pendula",
        "fastq_bytes": [172890455],
        "read_count": 4380359,
        "base_count": 354809079,
        "groups": ["6"],
    },
    "ERR10114867": {
        "paper": "Klapper et al. 2023 Science / PRJEB55583",
        "layout": "PAIRED",
        "scientific_name": "blank sample",
        "fastq_bytes": [14798699, 15848835],
        "read_count": 847520,
        "base_count": 49281990,
        "groups": ["7"],
    },
    "ERR10114861": {
        "paper": "Klapper et al. 2023 Science / PRJEB55583",
        "layout": "PAIRED",
        "scientific_name": "Homo sapiens neanderthalensis",
        "fastq_bytes": [35365445, 36069916],
        "read_count": 4068862,
        "base_count": 78016958,
        "groups": ["8"],
    },
    "ERR15682267": {
        "paper": "Sarhan et al. 2026 Microbiome / PRJEB94382",
        "layout": "PAIRED",
        "scientific_name": "metagenome",
        "fastq_bytes": [4102323, 5787702],
        "read_count": 59258,
        "base_count": 17836658,
        "groups": ["9"],
    },
}


def ensure_out() -> None:
    OUT.mkdir(parents=True, exist_ok=True)


def read_agent_peptide() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(RAW / "case1_amplit_validation" / "Validation.csv", header=None, names=["label", "sequence"])
    cleaned = pd.read_csv(FINAL / "1" / "final_outputs" / "cleaned_Validation.csv")
    return raw, cleaned


def plot_group1() -> list[Path]:
    raw, cleaned = read_agent_peptide()
    paths = []
    counts = pd.DataFrame(
        {
            "Published raw Validation.csv": raw["label"].value_counts().sort_index(),
            "Agent cleaned output": cleaned["label"].value_counts().sort_index(),
        }
    ).fillna(0)
    ax = counts.plot(kind="bar", figsize=(7, 4), color=["#9aa6b2", "#207a5c"])
    ax.set_title("Group 1: peptide label counts")
    ax.set_xlabel("Label")
    ax.set_ylabel("Rows")
    ax.legend(frameon=False)
    plt.tight_layout()
    path = OUT / "group1_peptide_label_counts_published_vs_agent.png"
    plt.savefig(path, dpi=200)
    plt.close()
    paths.append(path)

    raw_lengths = raw["sequence"].astype(str).str.len()
    agent_lengths = cleaned["sequence"].astype(str).str.len()
    bins = range(min(raw_lengths.min(), agent_lengths.min()), max(raw_lengths.max(), agent_lengths.max()) + 2)
    plt.figure(figsize=(7, 4))
    plt.hist(raw_lengths, bins=bins, alpha=0.55, label="Published raw Validation.csv", color="#9aa6b2")
    plt.hist(agent_lengths, bins=bins, alpha=0.55, label="Agent cleaned output", color="#207a5c")
    plt.title("Group 1: peptide length distribution")
    plt.xlabel("Peptide length")
    plt.ylabel("Count")
    plt.legend(frameon=False)
    plt.tight_layout()
    path = OUT / "group1_peptide_length_distribution_published_vs_agent.png"
    plt.savefig(path, dpi=200)
    plt.close()
    paths.append(path)
    return paths


def parse_fastqc_zip(path: Path) -> dict[str, float | str]:
    with zipfile.ZipFile(path) as zf:
        data_name = next(name for name in zf.namelist() if name.endswith("fastqc_data.txt"))
        text = zf.read(data_name).decode("utf-8", errors="replace")
    metrics: dict[str, float | str] = {}
    for line in text.splitlines():
        if "\t" not in line:
            continue
        key, value = line.split("\t", 1)
        if key in {"Filename", "File type", "Encoding"}:
            metrics[key] = value
        elif key in {"Total Sequences", "Sequences flagged as poor quality", "Sequence length", "%GC"}:
            metrics[key] = value
    total = str(metrics.get("Total Sequences", "0"))
    gc = str(metrics.get("%GC", "0"))
    poor = str(metrics.get("Sequences flagged as poor quality", "0"))
    length = str(metrics.get("Sequence length", ""))
    metrics["total_sequences_num"] = int(float(total))
    metrics["gc_percent_num"] = float(gc)
    metrics["poor_quality_num"] = int(float(poor))
    length_values = [int(x) for x in re.findall(r"\d+", length)]
    metrics["sequence_length_mean"] = sum(length_values) / len(length_values) if length_values else 0
    return metrics


def fastqc_zips_for_run(run: str, groups: list[str]) -> list[Path]:
    zips: list[Path] = []
    for group in groups:
        zips.extend(sorted((FINAL / group / "final_outputs").glob(f"{run}*_fastqc.zip")))
    return zips


def local_fastq_for_run(run: str) -> list[Path]:
    paired = sorted(RAW.glob(f"case*/{run}_*.fastq.gz"))
    if paired:
        return paired
    return sorted(RAW.glob(f"case*/{run}.fastq.gz"))


def plot_fastq_run(run: str, info: dict) -> tuple[list[Path], list[dict]]:
    paths = []
    zips = fastqc_zips_for_run(run, info["groups"])
    local_fastqs = local_fastq_for_run(run)
    agent_metrics = [parse_fastqc_zip(path) | {"zip": str(path)} for path in zips]
    rows = []
    for i, (zip_path, metrics) in enumerate(zip(zips, agent_metrics), start=1):
        ena_bytes = info["fastq_bytes"][i - 1] if i <= len(info["fastq_bytes"]) else None
        local_fastq_bytes = local_fastqs[i - 1].stat().st_size if i <= len(local_fastqs) else None
        rows.append(
            {
                "run": run,
                "mate": f"R{i}" if len(zips) > 1 else "single",
                "paper": info["paper"],
                "layout": info["layout"],
                "scientific_name": info["scientific_name"],
                "ena_fastq_bytes": ena_bytes,
                "local_fastq_bytes": local_fastq_bytes,
                "agent_total_sequences": metrics["total_sequences_num"],
                "agent_gc_percent": metrics["gc_percent_num"],
                "agent_poor_quality": metrics["poor_quality_num"],
                "agent_sequence_length_mean": metrics["sequence_length_mean"],
                "ena_run_read_count": info["read_count"],
                "ena_run_base_count": info["base_count"],
            }
        )

    labels = [row["mate"] for row in rows]
    agent_total = sum(row["agent_total_sequences"] for row in rows)
    ena_total = info["read_count"]
    plt.figure(figsize=(7, 4))
    plt.bar(["Published ENA read_count", "Agent FastQC total"], [ena_total, agent_total], color=["#9aa6b2", "#207a5c"])
    plt.title(f"{run}: read count comparison")
    plt.ylabel("Reads / sequences")
    plt.tight_layout()
    path = OUT / f"{run}_read_count_published_vs_agent.png"
    plt.savefig(path, dpi=200)
    plt.close()
    paths.append(path)

    fig, ax1 = plt.subplots(figsize=(7, 4))
    x = range(len(rows))
    width = 0.35
    ax1.bar([i - width / 2 for i in x], [row["ena_fastq_bytes"] / 1_000_000 for row in rows], width=width, label="Published ENA FASTQ MB", color="#9aa6b2")
    ax1.bar([i + width / 2 for i in x], [row["local_fastq_bytes"] / 1_000_000 for row in rows], width=width, label="Local FASTQ used by agent MB", color="#207a5c")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels)
    ax1.set_ylabel("File size (MB)")
    ax1.set_title(f"{run}: source file size and agent GC%")
    ax2 = ax1.twinx()
    ax2.plot(list(x), [row["agent_gc_percent"] for row in rows], color="#a64b2a", marker="o", label="Agent GC%")
    ax2.set_ylabel("Agent GC%")
    lines, names = ax1.get_legend_handles_labels()
    lines2, names2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, names + names2, frameon=False, loc="upper left")
    plt.tight_layout()
    path = OUT / f"{run}_file_size_and_gc_published_vs_agent.png"
    plt.savefig(path, dpi=200)
    plt.close()
    paths.append(path)
    return paths, rows


def write_summary(rows: list[dict]) -> Path:
    summary = OUT / "comparison_summary.csv"
    with summary.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "group",
            "run",
            "mate",
            "paper",
            "layout",
            "scientific_name",
            "ena_fastq_bytes",
            "local_fastq_bytes",
            "agent_total_sequences",
            "agent_gc_percent",
            "agent_poor_quality",
            "agent_sequence_length_mean",
            "ena_run_read_count",
            "ena_run_base_count",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return summary


def main() -> None:
    ensure_out()
    made = plot_group1()
    all_rows = []
    run_to_group = {
        "ERR15682270": "2_3",
        "ERR10114877": "4_5",
        "ERR3250149": "6",
        "ERR10114867": "7",
        "ERR10114861": "8",
        "ERR15682267": "9",
    }
    for run, info in ENA.items():
        paths, rows = plot_fastq_run(run, info)
        made.extend(paths)
        for row in rows:
            row["group"] = run_to_group[run]
        all_rows.extend(rows)
    summary = write_summary(all_rows)
    print(json.dumps({"figures": [str(path) for path in made], "summary": str(summary)}, indent=2))


if __name__ == "__main__":
    main()
