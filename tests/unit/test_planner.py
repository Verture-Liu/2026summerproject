import httpx
import pytest

from research_agent.agent.planner import Planner
from research_agent.agent.prompts import build_system_prompt
from research_agent.skills.registry import build_default_registry


@pytest.mark.asyncio
async def test_planner_parses_json_workflow():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"schema_version":"1.0","task_summary":"filter",'
                                '"steps":[{"id":"step_01","skill":"peptide_filter",'
                                '"inputs":[{"source":"uploaded","ref":"peptides"}],'
                                '"parameters":{"min_length":13,"max_length":26},'
                                '"outputs":[{"name":"filtered","format":"fasta"}],'
                                '"reason":"length filter"}]}'
                            )
                        }
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    planner = Planner(
        client=client,
        base_url="https://example.test/v1",
        api_key="x",
        model="m",
    )
    workflow = await planner.plan("filter peptides", [], [])
    assert workflow.steps[0].skill == "peptide_filter"
    await client.aclose()


def test_system_prompt_contains_exact_workflow_fields():
    prompt = build_system_prompt(
        [{"ref": "peptides", "format": "fasta", "name": "peptides.fasta"}],
        [],
    )
    assert '"schema_version"' in prompt
    assert '"task_summary"' in prompt
    assert '"parameters"' in prompt
    assert '"inputs"' in prompt
    assert '"outputs"' in prompt
    assert '"version"' not in prompt
    assert '"params"' not in prompt


def test_system_prompt_guides_peptide_csv_workflows():
    prompt = build_system_prompt(
        [{"ref": "validation", "format": "csv"}],
        build_default_registry().catalog(),
    )
    assert "normalize before peptide operations" in prompt
    assert "Do not invent peptide prediction" in prompt
    assert "Use the actual uploaded file formats in FILES" in prompt
    assert "Do not plan FASTQ-only Skills for CSV or TSV uploads" in prompt
    assert "Do not set label_column or sequence_column to observed row values" in prompt


def test_system_prompt_requires_qc_gate_before_downstream_analysis():
    prompt = build_system_prompt(
        [{"ref": "reads", "format": "fastq", "name": "minimal_reads.fastq.gz"}],
        build_default_registry().catalog(),
    )
    assert "Treat workflows as staged scientific pipelines" in prompt
    assert "raw QC before cleaning or downstream analysis" in prompt
    assert "cleaned-data quality gate before downstream application analysis" in prompt
    assert "Do not jump directly from raw data to application analysis" in prompt
    assert "Do not insert gzip_decompress before fastq_qc" in prompt
    assert "FastQC accepts .fastq.gz and .fq.gz directly" in prompt


def test_system_prompt_includes_staged_workflow_templates():
    prompt = build_system_prompt(
        [
            {"ref": "validation", "format": "csv", "name": "Validation.csv"},
            {"ref": "reads", "format": "fastq", "name": "minimal_reads.fastq.gz"},
        ],
        build_default_registry().catalog(),
    )
    assert "Peptide CSV staged template" in prompt
    assert "peptide_csv_normalize -> peptide_validate -> peptide_deduplicate -> data_quality_gate" in prompt
    assert "Do not set fail_on_error true before deduplication" in prompt
    assert "FASTQ staged template" in prompt
    assert "file_type_detect -> fastq_pair_match -> fastq_qc" in prompt
    assert "one separate fastq_qc step per mate" in prompt
    assert "cleaning/filtering/host-removal" in prompt


def test_system_prompt_exposes_skill_input_count_contracts():
    prompt = build_system_prompt(
        [{"ref": "reads", "format": "fastq"}],
        build_default_registry().catalog(),
    )

    assert '"name": "host_dna_removal"' in prompt
    assert '"min_inputs": 1' in prompt
    assert '"max_inputs": 2' in prompt


@pytest.mark.asyncio
async def test_planner_repairs_invalid_workflow_once():
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            content = (
                '{"version":"1.0","steps":[{"skill":"peptide_filter",'
                '"params":{"min_length":13,"max_length":26},'
                '"reason":"filter lengths"}]}'
            )
        else:
            content = (
                '{"schema_version":"1.0","task_summary":"filter",'
                '"steps":[{"id":"step_01","skill":"peptide_filter",'
                '"inputs":[{"source":"uploaded","ref":"peptides"}],'
                '"parameters":{"min_length":13,"max_length":26},'
                '"outputs":[{"name":"filtered","format":"fasta"}],'
                '"reason":"filter lengths"}]}'
            )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    planner = Planner(
        client=client,
        base_url="https://example.test/v1",
        api_key="secret-key",
        model="m",
    )
    workflow = await planner.plan(
        "filter peptides",
        [{"ref": "peptides", "format": "fasta"}],
        [],
    )
    assert workflow.steps[0].inputs[0].ref == "peptides"
    assert len(calls) == 2
    repair_body = calls[1].read().decode()
    assert "secret-key" not in repair_body
    await client.aclose()
