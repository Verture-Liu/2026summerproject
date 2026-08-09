# PaleoRigor public website design

Date: 2026-08-06
Status: approved design

## Purpose

Create an English-language public entry point for PaleoRigor that can be hosted free of charge with GitHub Pages. The website will explain the scientific problem, show how expert review is retained, summarize the validation evidence, and direct visitors to the GitHub repository for full local execution.

The public site is a presentation and documentation layer. It is not a cloud bioinformatics service and will not execute local Skills, accept research data, store API keys, or imply that the browser demonstration performs ancient-DNA authentication.

## Audience

The primary audience is paleobiologists, archaeologists, ancient-DNA researchers, supervisors, reviewers, and readers of the associated manuscript. The language should explain scientific value before implementation details.

## Architecture

The project will retain two distinct interfaces:

1. **Public GitHub Pages website** — static HTML, CSS, and minimal JavaScript for project explanation, evidence, documentation, and GitHub navigation.
2. **Local PaleoRigor application** — the existing Python-backed browser interface that performs real workflow planning and executes local Skills after expert approval.

The public site will be stored under `docs/` and will not replace or modify `src/research_agent/web/`.

## Page structure

### 1. Navigation and hero

- PaleoRigor wordmark and concise scientific tagline.
- Primary actions:
  - `View on GitHub`
  - `Run locally`
  - `Explore the workflow`
- A visible statement that public exploration and local execution are different modes.

### 2. Scientific problem

Explain the early-stage risks in paleomicrobiome data analysis:

- wrong or ambiguous source files;
- invisible transformations;
- incompatible analytical operations;
- technical quality-control success being mistaken for biological validity.

### 3. How PaleoRigor works

Present the sequence:

`Research question → structured plan → expert review → bounded local Skills → auditable outputs`

Explain that experts review provenance and task compatibility before execution and retain authority over interpretation afterward.

### 4. Capabilities

Group current functionality by scientific purpose rather than by internal module name:

- biological table and peptide curation;
- FASTQ organization and quality control;
- public source-record verification;
- ancient-DNA preparation and authentication-ready extensions;
- metagenomic preprocessing, taxonomy, assembly, and functional-analysis wrappers;
- reproducibility records and separated final/intermediate outputs.

Missing local tools must be described as environment requirements, not as online capabilities.

### 5. Evidence

Summarize only measured results already reported in the manuscript:

- 12 of 12 supported benchmark runs passed;
- only 1 of 4 incompatible or inference-boundary requests was correctly constrained;
- six public sequencing records matched repository read counts and compressed-file sizes exactly;
- 114 duplicate peptide records were removed, yielding 5,696 non-redundant records;
- the retraction-associated example demonstrated source-level reproducibility without treating it as biological validation.

The site must preserve the same claim boundaries as the manuscript.

### 6. Expert checkpoints

Show three explicit intervention points:

- scientific and provenance review at intake;
- workflow and parameter approval before execution;
- interpretation review after outputs are generated.

### 7. Local installation

Provide copyable commands for cloning the repository and starting the local application. Link to the repository and existing English documentation. Explain that real analyses, local Conda environments, external bioinformatics tools, and API credentials remain on the user's computer.

### 8. Footer

Include links to GitHub, documentation, validation materials, and the project license if present. Do not invent a paper DOI, release DOI, institutional affiliation, or hosted application endpoint.

## Visual direction

- English only.
- Restrained scientific styling with off-white backgrounds, deep blue-green text, muted blue and warm amber accents.
- Rounded but not decorative cards; generous whitespace; high contrast.
- Reuse author-created or programmatically generated project figures where useful.
- No AI-generated decorative imagery and no unverified stock assets.
- Responsive layout for desktop and mobile.

## Interaction

JavaScript is limited to navigation behavior, small reveal effects, and copying the local-start command. No upload control, API key input, fake execution button, or simulated scientific result will be included in this first version.

## Repository and hosting

- GitHub repository: `https://github.com/Verture-Liu/2026summerproject`
- GitHub Pages source: repository `docs/` directory.
- Main entry point: `docs/index.html`.
- Site assets: `docs/assets/`.
- Existing `docs/Chinese_version.html`, `docs/eng_version.html`, research documents, and Superpowers specifications remain intact.

Publishing GitHub Pages is a separate repository-setting action after the site files have been implemented and tested.

## Testing and acceptance criteria

- All internal asset paths work from a GitHub Pages project subpath.
- GitHub and documentation links resolve correctly.
- No browser console errors during local static preview.
- Layout remains readable at desktop and mobile viewport widths.
- Text does not claim cloud execution or autonomous biological interpretation.
- Quantitative statements match the verified manuscript.
- The existing local application and its tests remain unchanged.
- The site can be served as static files without Python, Node.js, or a rented server.

## Out of scope

- Running FastQC, MultiQC, Bowtie2, mapDamage, or other Skills in the cloud.
- Uploading or storing user datasets.
- Managing user accounts or API keys.
- A hosted planning-model backend.
- Website analytics, authentication, billing, or database services.
- Redesigning the existing local Agent interface.

