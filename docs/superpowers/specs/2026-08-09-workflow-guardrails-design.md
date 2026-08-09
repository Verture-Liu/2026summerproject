# Workflow Guardrails Design

## Goal

Prevent malformed or scientifically incompatible model-generated workflows from reaching local execution, while returning errors that a non-computational researcher can act on.

## Architecture

PaleoRigor will keep the planner probabilistic and make acceptance deterministic. A candidate workflow passes through a central validator before user approval and execution. Each registered skill remains the source of truth for its accepted input formats, declared outputs, parameter schema, resource class, and dependency readiness. Runtime skills retain content-level checks that cannot be inferred from filename or workflow structure.

## Validation layers

1. **Request binding:** uploaded references must resolve to real staged files and their detected formats, rather than merely matching names guessed by the model.
2. **Workflow contract validation:** step identifiers, step-output references, input/output formats, parameter values, output names, and skill availability are checked before execution.
3. **Execution readiness:** registered skills may expose a dependency readiness report. Missing tools stop execution with an installation hint; PaleoRigor does not install software automatically.
4. **Skill-semantic checks:** individual skills continue checking domain details such as peptide alphabets, FASTQ structure, paired-end relationships, reference indexes, and empty outputs.

## Error contract

Validation errors use stable codes and structured fields in addition to a readable message. Each issue records the affected step, skill, offending reference or parameter, expected value, observed value, and a suggested correction where available. Existing `valid`, `errors`, and `warnings` fields remain compatible with the current web interface and API.

## Scope

This change strengthens deterministic checks around existing skills. It does not add autonomous repair, silently rewrite scientific intent, install dependencies, or claim that syntactically valid workflows are biologically appropriate. Safe reference-syntax normalization may be accepted, but incompatible inputs and unsupported claims must be rejected rather than guessed around.

## Testing

Tests cover missing uploads, incompatible formats, malformed or ambiguous step references, duplicate output aliases, invalid parameters, missing dependencies, actionable issue fields, compatibility with existing valid workflows, and end-to-end API rejection before execution. Repeated test cycles include focused validator tests and the full project suite.
