# Bundled tool licenses

PaleoRigor redistributes FastQC, MultiQC, SeqKit, SeqTk, Samtools, BWA, and
Bowtie2 under their respective open-source licenses. The build process copies
the complete license text supplied by each pinned package into this directory.
The bundled Java runtime is built from Azul Zulu OpenJDK 21 and its legal files
remain inside the generated runtime image.

Upstream projects and versions are recorded in `tool-sources.json` and in the
runtime `manifest.json`. PaleoRigor does not claim ownership of these tools.
