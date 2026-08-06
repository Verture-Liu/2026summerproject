# PaleoRigor audience-focused manuscript revision design

## Objective

Strengthen the existing manuscript for paleobiologists without rebuilding its
figures, results, references, or overall structure. The revision should make the
practical scientific problem, the value of the system, and the boundary between
technical quality control and biological interpretation clear to a domain reader.

## Fixed decisions

- The system name is **PaleoRigor**.
- The current latest manuscript is the editing base.
- This is a targeted revision, not a complete rewrite.
- Existing quantitative results, tables, citations, and section order are retained
  unless a local correction is required for logic or accuracy.
- Existing figures are not redesigned. If the graphical abstract literally contains
  the misspelled or ambiguous label `Acient-data`, only that label may be corrected
  to `Archaeological sample`; no graphical composition or layout changes are in scope.
- The public website is a separate follow-up task and is not part of this manuscript
  revision.

## Audience and central argument

The primary audience is paleobiologists and paleomicrobiome researchers rather
than software engineers. The manuscript should follow this argument:

1. Ancient microbial evidence is scarce, contamination-sensitive, and vulnerable
   to early data-handling and provenance errors.
2. Standardized, intelligent assistance could reduce avoidable operational errors,
   but general workflow engines and unconstrained agents do not provide a suitable
   domain-facing, expert-reviewable control layer.
3. PaleoRigor converts research requests into constrained and reviewable local
   analyses while preserving human decisions at scientifically important boundaries.
4. The benchmark and case studies demonstrate operational reliability and
   traceability for supported tasks, not molecular authenticity or ecological truth.
5. The practical value is safer and more interpretable evidence preparation before
   paleobiologists make biological claims.

## Planned manuscript changes

### Naming and terminology

- Define PaleoRigor in full at first use and use the proper name consistently.
- Replace generic or abrupt first uses of `agent` with the named system.
- Prefer domain-facing terms such as sample provenance, ancient biomolecular
  evidence, quality-control evidence, expert review, and biological interpretation.
- Retain technical terms only when they are needed to reproduce the work, defining
  them at first use.

### Abstract

- Rebuild the opening logic around the paleobiological reliability problem.
- Introduce standardized intelligent assistance before introducing PaleoRigor.
- Translate implementation-heavy descriptions into consequences that a
  paleobiologist can understand.
- Retain the strongest quantitative evidence, but explain what the numbers mean for
  reliable use rather than listing computational operations.
- End with the system's scientific role and explicit limits.

### Main text

- Strengthen the problem-to-solution chain in the Introduction and Results lead-ins.
- Add local transitions that explain why each engineering or benchmark result matters
  to paleobiological practice.
- Preserve reproducibility details in Methods, while removing unnecessary emphasis on
  file-handling mechanics from audience-facing passages.

### Retraction-associated case

- Position the case as a boundary-stress demonstration: technically valid and
  quality-controlled files can still be embedded in scientifically compromised
  literature contexts.
- Explain that PaleoRigor separates `technically analysable` from `biologically
  supported` and records the latter as an expert boundary.
- Do not claim that PaleoRigor detected misconduct, authenticated molecules, or
  disproved the retracted conclusion.

### Discussion and Conclusion

- Discuss the value of an auditable entry point for paleobiologists, not merely a
  successful software pipeline.
- Explain how expert intervention protects interpretation at provenance,
  authentication, contamination, and biological-claim boundaries.
- Present future extensions—contamination-aware checks, ancient-DNA damage evidence,
  and community-maintained domain skills—as a research agenda rather than completed
  capabilities.
- Conclude at the level of safer paleobiological evidence building and transparent
  collaboration between domain experts and computational tools.

## Verification

- Confirm all occurrences of the old generic system naming are intentional.
- Check the Abstract, Introduction, Results, Discussion, and Conclusion for a clear
  paleobiologist-facing problem-to-value chain.
- Verify that no revised sentence overstates the benchmark, source audit, retraction
  case, ancient-DNA authentication, contamination detection, or biological inference.
- Preserve citation-to-claim correspondence and existing quantitative values.
- Render the revised DOCX, inspect every page, and correct any pagination, overlap,
  table, caption, or cross-reference defect before delivery.

