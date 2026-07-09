from research_agent.skills.router import SkillRouter
from research_agent.skills.registry import builtin_skill_root


def test_builtin_packages_expose_existing_capabilities():
    router = SkillRouter([builtin_skill_root()])
    names = {item.name for item in router.catalog()}
    assert {
        "table_filter",
        "peptide_filter",
        "peptide_csv_normalize",
        "peptide_validate",
        "peptide_label_filter",
        "peptide_length_filter",
        "peptide_deduplicate",
        "peptide_statistics",
        "peptide_chart",
        "peptide_csv_export",
        "amp_prediction",
        "fastq_quality_filter",
        "host_dna_removal",
        "metagenome_assembly",
        "multiqc_summary",
        "file_type_detect",
        "fastq_pair_match",
        "tool_environment_check",
        "data_quality_gate",
        "sample_sheet_validate",
        "seqkit_stats",
        "seqkit_length_filter",
        "seqkit_deduplicate",
        "seqtk_sample",
        "gzip_decompress",
        "gzip_compress",
        "bwa_align",
        "bowtie2_align",
        "samtools_sort_index",
        "samtools_stats",
        "picard_markduplicates",
        "damageprofiler_profile",
        "qualimap_bamqc",
        "mosdepth_coverage",
        "bracken_abundance",
        "humann_profile",
        "diamond_blastx",
        "blastn_search",
        "peptide_properties",
        "peptide_candidate_rank",
        "amplify_prediction",
        "amp_scanner_prediction",
        "modlamp_descriptor",
    }.issubset(names)
    assert {item["package_id"] for item in router.packages()} == {
        "peptide-table",
        "amplit",
        "legacy-core",
        "ancient-dna-core",
        "ancient-metagenome-tools",
        "workflow-utilities",
        "sequence-utilities",
    }
    assert router.diagnostics() == []
