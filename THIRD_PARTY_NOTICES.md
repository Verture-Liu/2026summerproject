# Third-party notices

PaleoRigor's own source code is released under the MIT License (see `LICENSE`).

The packaged desktop applications additionally redistribute independently
licensed third-party analysis tools and a Java runtime. Those components are
**not** covered by the MIT License; each keeps its own license, and several are
GPL-3.0.

PaleoRigor invokes every bundled tool as a separate executable process. It does
not link against them, embed their source, or alter their behaviour. The bundles
are therefore aggregations of independent programs, and PaleoRigor's
MIT-licensed code is not a derivative work of the GPL-licensed tools. The GPL
terms still govern redistribution of those tools themselves, including the
obligation to make their corresponding source available.

## macOS bundle (Apple Silicon, `PaleoRigor-dev-arm64.dmg`)

| Component | Version | License | Upstream |
| --- | --- | --- | --- |
| FastQC | 0.12.1 | GPL-3.0-or-later | https://www.bioinformatics.babraham.ac.uk/projects/fastqc/ |
| MultiQC | 1.35 | GPL-3.0-or-later | https://github.com/MultiQC/MultiQC |
| Bowtie2 | 2.5.5 | GPL-3.0-or-later | https://github.com/BenLangmead/bowtie2 |
| BWA | 0.7.19-r1273 | GPL-3.0-or-later | https://github.com/lh3/bwa |
| Samtools | 1.23.1 | MIT/Expat | https://github.com/samtools/samtools |
| SeqKit | 2.13.0 | MIT | https://github.com/shenwei356/seqkit |
| SeqTk | 1.5-r133 | MIT | https://github.com/lh3/seqtk |
| Azul Zulu OpenJDK | 21.0.8 | GPL-2.0 with Classpath Exception | https://www.azul.com/downloads/ |

Tools are staged unmodified from the pinned sources recorded in
`packaging/macos/tool-sources.json`. Upstream license texts are mirrored in
`packaging/macos/licenses/` and copied into the generated bundle at build time.

## Windows bundle (x64, `PaleoRigor-Setup.exe`)

| Component | Version | License | Upstream |
| --- | --- | --- | --- |
| FastQC | 0.12.1 | GPL-3.0-or-later | https://www.bioinformatics.babraham.ac.uk/projects/fastqc/ |
| MultiQC | 1.35 | GPL-3.0-or-later | https://github.com/MultiQC/MultiQC |
| Bowtie2 | 2.5.5 | GPL-3.0-or-later | https://github.com/BenLangmead/bowtie2 |
| BWA | 0.7.19-r1273 | GPL-3.0-or-later | https://github.com/lh3/bwa |
| Samtools | 1.24 | MIT/Expat | https://github.com/samtools/samtools |
| SeqKit | 2.13.0 | MIT | https://github.com/shenwei356/seqkit |
| SeqTk | 1.5-r133 | MIT | https://github.com/lh3/seqtk |
| Eclipse Temurin JRE | 21.0.8+9 | GPL-2.0 with Classpath Exception | https://adoptium.net/ |

Pinned source URLs and SHA-256 checksums for every Windows component are
recorded in `packaging/windows/tool-sources.json`. SeqTk and BWA are compiled
from upstream source under MSYS2/UCRT64; Samtools is taken from the official
MSYS2 package. The MinGW compatibility shims applied during those builds are
held in `packaging/windows/` and are distributed under each tool's own license.

Upstream license texts for the Windows bundle are copied into
`packaging/windows/licenses/` by the native staging step and are included in the
installer. They are not committed to this repository.

## Classpath Exception

The GPL-2.0 Classpath Exception carried by both bundled Java runtimes permits
them to be distributed alongside independently licensed applications without
those applications becoming subject to the GPL.

## Python dependencies

Runtime and development Python dependencies, with the exact versions used to
produce the reported results, are pinned in `requirements.lock`. Each dependency
retains its own license; none is redistributed in modified form.
