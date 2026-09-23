# PaleoRigor pilot usability session — protocol

**Status: prespecified.** Freeze this file before the first session. Do not edit
the tasks, the success criteria or the measures after seeing any result. If
something must change, record the change and the date, and report the session
as two separate rounds.

Version: 1.0 · Written 2026-09-23 · Before any participant was run.

## Purpose

To find concrete barriers that stop a non-computational researcher from
installing PaleoRigor, running a workflow, and correctly interpreting what the
system did and did not establish.

This is a **pilot**. It is designed to surface problems, not to demonstrate
usability. With one or two non-independent participants it cannot support any
claim that the software is usable by paleobiologists in general, and the
manuscript must not make that claim from these data.

## Participant

One researcher with a biology or paleobiology background and no routine
programming experience — the population the manuscript names as its target
user. The participant is known to the author and is therefore **not
independent**; this must be stated wherever the results are reported.

Record for each participant: field of study, years of research experience,
whether they have previously run command-line bioinformatics tools, whether
they have seen or heard about PaleoRigor before, and their operating system
and machine.

## Materials

- The released macOS application, downloaded by the participant from the public
  release page exactly as an outside reader would: no pre-installation, no
  pre-configuration, no files copied across by the observer.
- The synthetic files in `fixtures/`, given to the participant as a folder.
- A working model API key. The observer enters the key value personally; the
  participant is not asked to obtain or handle credentials, and the key is
  never recorded in the session notes.

## Observer rules

1. Read the participant brief aloud, then stop talking.
2. Do not demonstrate, do not explain the interface, do not say what the tool
   is good at.
3. If the participant is stuck for more than two minutes, give the smallest
   hint that unblocks them, write the hint down verbatim, and count it.
4. Record what the participant says in their own words. Do not tidy it up, and
   do not record your interpretation of what they meant.
5. Do not defend the software. "That's interesting, tell me more" is the only
   permitted response to criticism.
6. If the participant wants to stop, stop.

## Tasks

Each task is scored as **unaided**, **completed with hints** (count them), or
**not completed**. Record elapsed time from the moment the task is read to the
moment the participant says they are done.

### Task 0 — Install and reach a working interface
Give the participant the public release page URL and nothing else. Measure the
time from the first click to a usable interface, including any security
dialogue, and record every point of hesitation.

*Why:* this is the step most likely to stop a non-programmer, and no existing
evidence covers it.

### Task 1 — Quality-check a sequencing pair
"These two files are the forward and reverse reads from one sediment sample.
Check that they belong together, and produce a quality report for each file and
one combined summary."

*Success:* a run completes and the participant can point to the combined report.
*Also record:* did they read the proposed workflow before approving it, or click
straight through? Note this even though nothing asks them to.

### Task 2 — Clean a table and report what changed
"This peptide table has some duplicate entries. Produce a cleaned version, and
tell me how many rows were removed."

*Success:* the cleaned table is produced **and** the participant states the
correct number of removed rows (see `fixtures/README.md` for the known answer).
*Why:* this tests whether the traceability claim survives contact with a user —
a record that exists but cannot be found does not make anything traceable.

### Task 3 — Ask for something the system must refuse
"Use the tool to confirm that these reads are genuinely ancient and free of
modern contamination."

The system is expected to refuse. **The measurement is not whether it refuses.**
Record:
- Did the participant understand that it refused, or did they think it failed or
  crashed?
- Can they say, in their own words, why it refused?
- Do they agree the refusal was correct, or do they find it unhelpful?
- What would they do next in real research?

*Why:* the manuscript claims the system keeps users from over-reading
quality-control output as biological evidence. This is the first time that claim
is tested on a person rather than on a planner.

### Task 4 — Reconstruct the evidence trail
"Imagine it is two weeks later and your supervisor asks exactly which file you
analysed and what the software changed. Find the answer."

*Success:* the participant locates the run records and can name the input file
and the recorded transformation without help.

## Debrief questions

Ask all five, record verbatim, do not lead.

1. What do you think this software is for?
2. What did it do that you did not expect?
3. Was there a moment you were not sure whether it had worked?
4. Would you trust a result from it in your own work? Why, or why not?
5. What single thing would you change first?

## Measures reported

For each task: outcome, elapsed time, hint count, and errors observed.
Across the session: total installation time, total hints, comprehension of the
refusal in Task 3, and the list of distinct usability defects found.

No score, index or percentage will be computed from a single participant.

## Consent and ethics

Before the session, obtain and keep written consent (email is sufficient)
covering: what will be recorded, that no personal data beyond field and
experience level is kept, that quotations may be published anonymously, and
that the participant may stop at any time.

**Before reporting these data in a manuscript, confirm with the institutional
ethics committee whether a usability session with a human participant requires
review or a formal exemption at this institution.** The manuscript's current
Ethics approval statement says no participants were recruited; that statement
must be replaced once this session is reported.
