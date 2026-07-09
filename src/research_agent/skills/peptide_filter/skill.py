from research_agent.skills.base import SkillContext, SkillResult


def _read_fasta(path):
    records = []
    header = ""
    sequence = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(">"):
            if header:
                records.append((header, "".join(sequence)))
            header, sequence = line, []
        elif line.strip():
            sequence.append(line.strip())
    if header:
        records.append((header, "".join(sequence)))
    return records


class PeptideFilterSkill:
    name = "peptide_filter"
    description = "Filter peptide FASTA records by amino-acid length."
    input_formats = {"fasta"}
    output_formats = {"fasta"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "required": ["min_length", "max_length"],
        "properties": {
            "min_length": {"type": "integer", "minimum": 1},
            "max_length": {"type": "integer", "minimum": 1},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        minimum = int(parameters["min_length"])
        maximum = int(parameters["max_length"])
        if minimum > maximum:
            raise ValueError("min_length cannot exceed max_length")
        records = _read_fasta(context.inputs[0])
        kept = [(header, sequence) for header, sequence in records if minimum <= len(sequence) <= maximum]
        context.work_dir.mkdir(parents=True, exist_ok=True)
        output = context.work_dir / "filtered_peptides.fasta"
        output.write_text("".join(f"{header}\n{sequence}\n" for header, sequence in kept), encoding="utf-8")
        return SkillResult(
            "succeeded",
            [str(output)],
            {"input": len(records), "kept": len(kept)},
            [],
        )
