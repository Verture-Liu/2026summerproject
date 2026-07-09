# AMPLiT External-Tool Skill Design

## 1. Goal

Replace the current `amp_prediction` placeholder with a real wrapper Skill for
the official AMPLiT implementation.

The Skill never installs software. It checks whether a compatible AMPLiT
environment is present, explains every missing dependency, and runs prediction
only after the user has prepared the environment.

## 2. User Flow

```text
Natural-language request
  -> Agent plans amp_prediction
  -> dependency preflight
  -> environment complete: run prediction
  -> environment incomplete: stop and show installation instructions
```

Missing dependencies do not cause the Agent to create a new Skill, run an
installer, or modify the system Python.

## 3. Configuration

The user configures two local paths:

- `AMPLIT_HOME`: official AMPLiT repository or release directory.
- `AMPLIT_PYTHON`: Python executable belonging to the user's compatible
  AMPLiT environment.

Configuration may come from environment variables initially. A later UI may
provide path selectors without changing the Skill contract.

## 4. Compatibility Manifest

The Agent ships a static AMPLiT compatibility manifest containing:

- official repository and archived release URLs;
- supported AMPLiT revision or release identifier;
- required Python version: Python 3.9;
- required Python import names;
- required official scripts, feature resources, and model-weight files;
- the wrapper protocol version;
- installation and verification commands.

The manifest is data, not executable code. Updating AMPLiT compatibility should
normally require changing the manifest and its tests rather than rewriting the
generic dependency checker.

## 5. Dependency Preflight

The preflight checks, without executing prediction:

1. `AMPLIT_HOME` is configured and is a readable directory.
2. `AMPLIT_PYTHON` is configured and is an executable file.
3. The configured Python reports a supported version.
4. Required packages can be imported in that Python environment.
5. Required AMPLiT scripts and resources exist below `AMPLIT_HOME`.
6. Required model files exist and are non-empty.
7. The task work directory is writable.

The result is a structured report:

```json
{
  "ready": false,
  "tool": "AMPLiT",
  "checks": [
    {
      "name": "python_version",
      "status": "failed",
      "found": "3.12.2",
      "required": "3.9"
    }
  ],
  "installation_instructions": [
    "Create a dedicated Python 3.9 environment.",
    "Install the packages listed by the official AMPLiT release.",
    "Download the official code and model resources.",
    "Set AMPLIT_HOME and AMPLIT_PYTHON.",
    "Run the dependency check again."
  ]
}
```

Paths, package versions, and commands are shown to the user, but no command is
executed automatically.

## 6. Prediction Input

The Skill accepts:

- canonical peptide CSV with a `sequence` column; or
- peptide FASTA.

For CSV input, `label` is optional because prediction may be performed on
unlabelled user sequences. Existing columns are retained in the result.

Input validation requires:

- at least one sequence;
- uppercase canonical amino-acid sequences after normalization;
- unique internal row identifiers;
- no silent removal of invalid rows.

Invalid input produces a separate rejected-row report and fails prediction
unless the workflow explicitly prepared valid input with earlier Skills.

## 7. Official Wrapper

The wrapper is a controlled Python entry point executed by `AMPLIT_PYTHON`.
It may import and call official AMPLiT code, but it does not reimplement or
retrain the model.

The local Agent invokes it with fixed arguments:

```text
AMPLIT_PYTHON wrapper.py
  --amplit-home <AMPLIT_HOME>
  --input <task input>
  --output <task output CSV>
  --threshold <validated threshold>
```

The command is constructed as an argument list, never a shell string. User
text cannot supply executable names, code, or arbitrary command-line flags.

## 8. Skill Contract

Skill name:

```text
amp_prediction
```

Parameters:

- `score_threshold`: number from `0.0` to `1.0`, default `0.5`;
- `batch_size`: integer from `1` to `4096`, default selected by the wrapper;
- `include_input_columns`: boolean, default `true`.

Outputs:

- `amplit_predictions.csv`;
- `amplit_run_metadata.json`.

Prediction CSV includes:

```text
sequence,amp_score,predicted_label
```

Metadata records:

- AMPLiT revision;
- model-file checksums;
- Python and package versions;
- parameters;
- input and output checksums;
- row counts;
- start time, end time, and duration.

## 9. Failure Handling

- Missing configuration: return `dependency_missing`.
- Unsupported Python or package versions: return `dependency_incompatible`.
- Missing official files or model weights: return `dependency_missing`.
- Invalid input: return `failed` with rejected-row details.
- Official process exits non-zero: return `failed`, preserve stdout/stderr logs.
- Output missing, malformed, or wrong row count: return `failed`.
- Prediction scores outside `0..1`: return `failed`.
- User cancellation: terminate only the wrapper process and preserve logs.

No fabricated result file is emitted on failure.

## 10. Web/API Behavior

Before execution, the task API exposes a dependency-check endpoint. The web
page presents:

- ready/not-ready status;
- each missing or incompatible item;
- complete installation commands;
- official source links;
- configured paths;
- a “Check again” action.

The existing execution endpoint also performs preflight so a stale browser
state cannot bypass the check.

## 11. Reusable External-Tool Framework

AMPLiT is the first user of a reusable framework containing:

- compatibility-manifest loader;
- executable and Python-environment checks;
- file/resource checks;
- safe subprocess runner;
- stdout/stderr capture;
- timeout and cancellation hooks;
- output validation;
- structured dependency reports.

Later Skills for Cutadapt, KneadData/Bowtie2, SPAdes, Prodigal, SeqKit, and
toxicity predictors reuse this framework with their own manifests and output
validators.

## 12. Verification

Automated tests use a fake AMPLiT environment and fake prediction process; they
do not download TensorFlow or official model weights.

Tests cover:

- every dependency failure separately;
- a complete ready environment;
- safe command construction;
- CSV and FASTA inputs;
- threshold validation;
- subprocess failure and timeout;
- malformed and mismatched outputs;
- version and checksum metadata;
- registry replacement of the placeholder;
- API dependency report;
- complete execution through the existing workflow executor.

A manual smoke test with the official AMPLiT environment is required before
claiming scientific reproduction.

## 13. Acceptance Criteria

- `amp_prediction` is no longer a `not_configured` placeholder.
- Missing environments receive actionable instructions and official links.
- The Agent never installs or modifies dependencies.
- A configured official environment can produce validated prediction CSV.
- All commands and outputs are auditable.
- The framework can support subsequent external-tool Skills without copying
  AMPLiT-specific process code.
