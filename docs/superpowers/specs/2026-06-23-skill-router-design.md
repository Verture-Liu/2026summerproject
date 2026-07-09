# Skill Router and Reviewed Package System Design

## 1. Goal

Replace the hard-coded Skill registry with a stable Skill Router that discovers,
validates, registers, and executes reviewed Skill packages.

The existing Peptide CSV and AMPLiT capabilities remain. They become the first
built-in packages and prove the same package protocol later used by downloaded
Skills.

Adding a compliant reviewed package must not require changing Agent core code.

## 2. Trust Boundary

The Agent never executes arbitrary Skills directly after download.

Skill packages have three trust states:

```text
skill-packages/
├── builtin/       maintained with the Agent
├── installed/     reviewed, converted, and explicitly enabled
└── quarantine/    downloaded but not trusted; never imported or executed
```

Only `builtin` and enabled `installed` packages enter the catalog sent to the
model API. `quarantine` is data storage only.

Moving a package from quarantine to installed is a separate review action. The
first version does not automate security review or approval.

## 3. Package Layout

Every executable package uses:

```text
package-id/
├── skill.yaml
├── SKILL.md
└── adapter.py
```

Optional package files:

```text
├── resources/
├── tests/
└── LICENSE
```

The Agent executes only the adapter declared by the manifest. Manifest paths
must be relative, remain inside the package directory, and contain no symlink
escape.

## 4. Manifest Protocol

`skill.yaml` contains:

```yaml
protocol_version: "1.0"
package_id: peptide-table
package_version: "1.0.0"
trust: builtin
source:
  type: local
  url: ""
  revision: ""
  license: project
skills:
  - name: peptide_csv_normalize
    description: Normalize peptide CSV or TSV tables.
    entrypoint: adapter.py:create_normalize_skill
    input_formats: [csv, tsv]
    output_formats: [csv]
    resource_class: light
    parameters:
      type: object
      properties: {}
      additionalProperties: false
    permissions:
      network: false
      filesystem: task_only
    dependencies:
      executables: []
      python_imports: [pandas]
      environment_variables: []
```

Required package fields:

- `protocol_version`;
- `package_id`;
- `package_version`;
- `trust`;
- `source`;
- non-empty `skills`.

Required Skill fields:

- `name`;
- `description`;
- `entrypoint`;
- input/output formats;
- resource class;
- parameter JSON Schema;
- permissions;
- dependencies.

Names use lowercase letters, digits, and underscores. Package IDs use lowercase
letters, digits, and hyphens.

## 5. Package Discovery

At application startup, the router:

1. scans built-in and installed roots;
2. ignores hidden files and quarantine;
3. loads and validates manifests without importing adapters;
4. rejects malformed, unsupported, disabled, or unsafe packages;
5. calculates package checksums;
6. detects duplicate package IDs and Skill names;
7. imports adapters only for accepted packages;
8. creates the runtime catalog.

Discovery order does not silently decide conflicts. Any duplicate active Skill
name disables every conflicting definition and reports the conflict.

One broken package does not prevent other valid packages from loading.

## 6. Adapter Contract

An entrypoint has the format:

```text
adapter.py:create_skill
```

The factory receives immutable manifest metadata and returns an object
implementing the existing Skill protocol:

```python
name: str
description: str
input_formats: set[str]
output_formats: set[str]
resource_class: str
parameter_schema: dict

run(context: SkillContext, parameters: dict) -> SkillResult
```

Runtime properties must exactly match the manifest. A mismatch disables the
package instead of trusting adapter code over reviewed metadata.

Factories may return one Skill per manifest definition. Packages can expose
multiple Skills through separate entrypoints.

## 7. Router Responsibilities

The Skill Router replaces direct dictionary construction and provides:

- `get(name)`;
- `catalog()`;
- `packages()`;
- `diagnostics()`;
- `reload()`;
- dependency checks when a Skill supports them.

The existing workflow planner, validator, and executor continue using
`get()`/`catalog()`. They do not need to know whether a Skill is built-in or
installed.

Catalog descriptors additionally record:

- package ID and version;
- trust state;
- source URL/revision;
- package checksum;
- permission declaration.

Only limited descriptors, not package source code or full documentation, are
sent to the external model API.

## 8. Permissions

The protocol declares:

- network: `false` or `true`;
- filesystem: initially only `task_only`;
- external_process: `false` or `true`.

First-version enforcement:

- inputs must resolve to task-controlled files;
- outputs must remain in the step work directory;
- entrypoints must remain inside the package;
- undeclared external-process use is prohibited by review and package tests;
- network-enabled packages are disabled by default unless explicitly enabled
  in local policy.

Python cannot provide a complete security sandbox inside the current process.
Therefore only reviewed packages are imported. Strong process/container
sandboxing is deferred.

## 9. Dependency Handling

Packages declare dependencies in the manifest.

Before execution, the router checks:

- required Python imports;
- executables;
- environment variables;
- package resources.

Missing dependencies stop the affected step and return:

- missing item;
- package and Skill name;
- source and version;
- package-provided installation instructions.

The Agent does not automatically install dependencies.

## 10. Package Lifecycle

First-version lifecycle:

```text
download to quarantine
→ human/security review
→ convert to protocol if needed
→ run package tests
→ copy to installed
→ restart/reload
→ router validates and registers
```

Removing or disabling a package removes it from future planning. Existing task
records keep package metadata and checksums for reproducibility.

Package downloading, marketplace search, signature infrastructure, and
automatic updates are separate future features.

## 11. Built-in Package Migration

Built-in packages:

1. `peptide-table`
   - all eight Peptide CSV Skills;
2. `amplit`
   - `amp_prediction`;
3. `legacy-core`
   - temporary package for any remaining existing local Skills during
     migration.

The Python implementation files may remain in their current modules initially.
Package adapters import and instantiate them. The Router, rather than
`build_default_registry()`, becomes the only registration path.

## 12. Diagnostics and UI

An API endpoint reports:

- loaded packages and Skills;
- disabled packages;
- manifest errors;
- conflicts;
- missing dependencies;
- trust/source/checksum metadata.

The web page shows a compact “Installed Skills” section. It does not allow
quarantine approval in the first version.

## 13. Failure Handling

- malformed YAML: disable package and report file/field;
- unsupported protocol: disable package;
- unsafe path or symlink escape: disable package;
- import/factory failure: disable only that package;
- metadata mismatch: disable package;
- duplicate Skill name: disable all conflicting definitions;
- missing dependency: keep Skill registered but block execution;
- invalid output path/format: fail the step;
- reload failure: retain the previous valid runtime registry.

## 14. Testing

Tests use temporary package roots and cover:

- valid single- and multi-Skill packages;
- malformed manifests;
- unsupported protocols;
- path traversal and symlink escape;
- quarantined package exclusion;
- disabled installed packages;
- duplicate names;
- adapter import/factory errors;
- manifest/runtime mismatch;
- package checksums;
- dependency diagnostics;
- reload rollback;
- planner catalog integration;
- workflow execution through discovered packages;
- migration of Peptide CSV and AMPLiT packages.

## 15. Acceptance Criteria

- Runtime registration is driven by package manifests, not a hard-coded Skill
  list.
- Existing Peptide CSV and AMPLiT capabilities still pass their tests.
- Adding a compliant reviewed package under `installed` requires no Agent code
  change.
- Quarantined packages are never imported.
- Broken or conflicting packages cannot silently replace trusted Skills.
- Tasks record package source, version, trust, and checksum.
- The full existing and new automated suite passes.

## 16. Deferred Scope

- automatic web search or downloading of Skills;
- automatic security approval;
- marketplace UI;
- cryptographic signing;
- container/process sandboxing;
- automatic dependency installation;
- automatic package updates.
