from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.peptide_table.common import CANONICAL_AMINO_ACIDS


OFFICIAL_REPOSITORY = "https://github.com/ChenSizhe13893461199/AMPLiT"
REQUIRED_FILES = (
    "utils1.py",
    "word2vec11.bin",
    "Model/G1.h5",
    "Model/G2.h5",
    "Model/G3.h5",
)
REQUIRED_IMPORTS = (
    "keras", "pandas", "numpy", "sklearn", "propy",
    "gensim", "scipy", "tensorflow", "torch",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _instructions() -> list[str]:
    return [
        f"Download the official AMPLiT repository: {OFFICIAL_REPOSITORY}",
        "Create a dedicated Python 3.9.7 environment.",
        (
            "Install keras==2.10.0 pandas==1.5.2 numpy==1.23.5 "
            "scikit-learn==1.2.0 propy3==1.1.0 gensim==4.2.0 "
            "scipy==1.9.3 tensorflow==2.10.0 and torch."
        ),
        "Set AMPLIT_HOME to the official repository directory.",
        "Set AMPLIT_PYTHON to that environment's Python executable.",
    ]


def _read_sequences(source: Path) -> pd.DataFrame:
    if source.suffix.lower() == ".csv":
        frame = pd.read_csv(source, keep_default_na=False)
        if "sequence" not in frame.columns:
            raise ValueError("CSV input must contain a sequence column")
        return frame.copy()
    if source.suffix.lower() in {".fasta", ".fa", ".faa"}:
        records, chunks = [], []
        name = None
        for line in source.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(">"):
                if name is not None:
                    records.append({"name": name, "sequence": "".join(chunks)})
                name, chunks = line[1:].strip(), []
            elif line:
                chunks.append(line)
        if name is not None:
            records.append({"name": name, "sequence": "".join(chunks)})
        return pd.DataFrame(records, columns=["name", "sequence"])
    raise ValueError("AMPLiT accepts CSV or FASTA peptide inputs")


class AmplitPredictionSkill:
    name = "amp_prediction"
    description = "Predict antimicrobial-peptide probability with an official local AMPLiT environment."
    input_formats = {"csv", "fasta"}
    output_formats = {"csv", "json"}
    resource_class = "heavy"
    parameter_schema = {
        "type": "object",
        "properties": {
            "score_threshold": {
                "type": "number", "minimum": 0.0, "maximum": 1.0
            },
            "batch_size": {
                "type": "integer", "minimum": 1, "maximum": 4096
            },
            "include_input_columns": {"type": "boolean"},
        },
        "additionalProperties": False,
    }

    def __init__(self, env: Mapping[str, str] | None = None):
        self._env = os.environ if env is None else env

    def check_dependencies(self, work_dir: Path) -> dict[str, Any]:
        missing, incompatible = [], []
        home_text = self._env.get("AMPLIT_HOME", "").strip()
        python_text = self._env.get("AMPLIT_PYTHON", "").strip()
        home = Path(home_text).expanduser() if home_text else None
        python_executable = Path(python_text).expanduser() if python_text else None
        if home is None:
            missing.append("AMPLIT_HOME is not configured")
        elif not home.is_dir():
            missing.append(f"AMPLIT_HOME is not a directory: {home}")
        else:
            for relative in REQUIRED_FILES:
                path = home / relative
                if not path.is_file() or path.stat().st_size == 0:
                    missing.append(f"Missing AMPLiT resource: {relative}")
        if python_executable is None:
            missing.append("AMPLIT_PYTHON is not configured")
        elif not python_executable.is_file() or not os.access(
            python_executable, os.X_OK
        ):
            missing.append(
                f"AMPLIT_PYTHON is not executable: {python_executable}"
            )
        if not missing:
            probe = (
                "import importlib.util,json,sys;"
                f"names={list(REQUIRED_IMPORTS)!r};"
                "print(json.dumps({'python_version':'.'.join(map(str,sys.version_info[:3])),"
                "'imports':{n:(importlib.util.find_spec(n) is not None) for n in names}}))"
            )
            try:
                completed = subprocess.run(
                    [str(python_executable), "-c", probe],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
                if completed.returncode:
                    incompatible.append(
                        "AMPLiT Python probe failed: " + completed.stderr.strip()
                    )
                else:
                    details = json.loads(completed.stdout.strip())
                    version = details["python_version"]
                    if tuple(map(int, version.split(".")[:2])) != (3, 9):
                        incompatible.append(
                            f"AMPLiT requires Python 3.9; found {version}"
                        )
                    for package, available in details["imports"].items():
                        if not available:
                            missing.append(f"Missing Python package: {package}")
            except (subprocess.TimeoutExpired, ValueError, KeyError, json.JSONDecodeError) as exc:
                incompatible.append(f"Could not inspect AMPLiT Python: {exc}")
        return {
            "ready": not missing and not incompatible,
            "tool": "AMPLiT",
            "home": str(home) if home else "",
            "python": str(python_executable) if python_executable else "",
            "missing": missing,
            "incompatible": incompatible,
            "installation_instructions": _instructions(),
            "official_url": OFFICIAL_REPOSITORY,
        }

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        threshold = float(parameters.get("score_threshold", 0.5))
        batch_size = int(parameters.get("batch_size", 512))
        if not 0 <= threshold <= 1:
            raise ValueError("score_threshold must be between 0 and 1")
        if not 1 <= batch_size <= 4096:
            raise ValueError("batch_size must be between 1 and 4096")
        context.work_dir.mkdir(parents=True, exist_ok=True)
        report = self.check_dependencies(context.work_dir)
        if not report["ready"]:
            status = (
                "dependency_incompatible"
                if report["incompatible"] else "dependency_missing"
            )
            error = "\n".join(
                report["missing"]
                + report["incompatible"]
                + ["Installation:"]
                + report["installation_instructions"]
            )
            return SkillResult(status, [], {"dependency_report": report}, [], error)
        try:
            frame = _read_sequences(context.inputs[0])
            if frame.empty:
                raise ValueError("Input contains no peptide sequences")
            sequences = frame["sequence"].astype(str).str.strip().str.upper()
            invalid = [
                sequence for sequence in sequences
                if not 11 <= len(sequence) <= 50
                or any(amino_acid not in CANONICAL_AMINO_ACIDS for amino_acid in sequence)
            ]
            if invalid:
                raise ValueError(
                    f"{len(invalid)} sequence(s) are invalid or outside 11 and 50 residues"
                )
            frame["sequence"] = sequences
            wrapper_input = context.work_dir / "amplit_input.csv"
            pd.DataFrame(
                {"row_id": range(len(frame)), "sequence": sequences}
            ).to_csv(wrapper_input, index=False)
            feature_input = context.work_dir / "amplit_feature_input.csv"
            pd.DataFrame(
                {"label": [0] * len(frame), "sequence": sequences}
            ).to_csv(feature_input, index=False, header=False)
            raw_output = context.work_dir / "amplit_raw_predictions.csv"
            home = Path(report["home"])
            started = time.monotonic()
            completed = subprocess.run(
                [
                    report["python"],
                    str(Path(__file__).with_name("wrapper.py")),
                    "--amplit-home", str(home),
                    "--input", str(wrapper_input),
                    "--feature-input", str(feature_input),
                    "--output", str(raw_output),
                    "--batch-size", str(batch_size),
                ],
                cwd=context.work_dir,
                capture_output=True,
                text=True,
                timeout=3600,
                check=False,
            )
            duration = time.monotonic() - started
            (context.work_dir / "stdout.log").write_text(
                completed.stdout, encoding="utf-8"
            )
            (context.work_dir / "stderr.log").write_text(
                completed.stderr, encoding="utf-8"
            )
            if completed.returncode:
                raise RuntimeError(
                    f"AMPLiT exited with code {completed.returncode}: "
                    f"{completed.stderr.strip()}"
                )
            predictions = pd.read_csv(raw_output)
            if not {"row_id", "sequence", "amp_score"}.issubset(predictions):
                raise ValueError("AMPLiT output is missing required columns")
            if len(predictions) != len(frame):
                raise ValueError("AMPLiT output row count does not match input")
            predictions["amp_score"] = pd.to_numeric(
                predictions["amp_score"], errors="raise"
            )
            if not predictions["amp_score"].between(0, 1).all():
                raise ValueError("AMPLiT scores must be between 0 and 1")
            predictions = predictions.sort_values("row_id")
            if predictions["row_id"].tolist() != list(range(len(frame))):
                raise ValueError("AMPLiT output row IDs do not match input")
            if predictions["sequence"].astype(str).tolist() != sequences.tolist():
                raise ValueError("AMPLiT output sequences do not match input")
            output = frame.reset_index(drop=True).copy()
            output["amp_score"] = predictions["amp_score"].to_numpy()
            output["predicted_label"] = (
                output["amp_score"] >= threshold
            ).astype(int)
            if not parameters.get("include_input_columns", True):
                output = output[["sequence", "amp_score", "predicted_label"]]
            predictions_path = context.work_dir / "amplit_predictions.csv"
            output.to_csv(predictions_path, index=False)
            metadata = {
                "tool": "AMPLiT",
                "official_url": OFFICIAL_REPOSITORY,
                "input_rows": len(frame),
                "score_threshold": threshold,
                "batch_size": batch_size,
                "duration_seconds": duration,
                "model_files": ["G1.h5", "G2.h5", "G3.h5"],
                "model_sha256": {
                    name: _sha256(home / "Model" / name)
                    for name in ("G1.h5", "G2.h5", "G3.h5")
                },
                "input_sha256": _sha256(context.inputs[0]),
                "output_sha256": _sha256(predictions_path),
            }
            metadata_path = context.work_dir / "amplit_run_metadata.json"
            metadata_path.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return SkillResult(
                "succeeded",
                [str(predictions_path), str(metadata_path)],
                {
                    "input_rows": len(frame),
                    "predicted_positive": int(output["predicted_label"].sum()),
                },
                [],
            )
        except subprocess.TimeoutExpired:
            return SkillResult("failed", [], {}, [], "AMPLiT prediction timed out")
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))
