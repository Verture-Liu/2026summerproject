from research_agent.skills.metagenome_tools.base import LocalCliSkill, object_schema


THREADS = {"type": "integer", "minimum": 1, "maximum": 128}
PATH_TEXT = {"type": "string", "minLength": 1}


class Metabat2BinningSkill(LocalCliSkill):
    name = "metabat2_binning"
    description = "Bin assembled metagenomic contigs with MetaBAT2."
    executable_candidates = ("metabat2",)
    official_url = "https://bitbucket.org/berkeleylab/metabat"
    installation_hint = "Install MetaBAT2 from Bioconda and prepare a contig depth file."
    input_formats = {"fasta"}
    output_formats = {"fasta"}
    parameter_schema = object_schema(
        {"depth_file": PATH_TEXT, "min_contig": {"type": "integer", "minimum": 1500}},
        ["depth_file"],
    )

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "-i", str(context.inputs[0]),
            "-a", parameters["depth_file"],
            "-o", str(context.work_dir / "bins" / "bin"),
            "-m", str(parameters.get("min_contig", 2500)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "bins"]

    def prepare_directories(self, context, parameters):
        return [context.work_dir / "bins"]


class Maxbin2BinningSkill(LocalCliSkill):
    name = "maxbin2_binning"
    description = "Bin assembled metagenomic contigs with MaxBin2."
    executable_candidates = ("run_MaxBin.pl",)
    official_url = "https://sourceforge.net/projects/maxbin2/"
    installation_hint = "Install MaxBin2 from Bioconda and prepare an abundance file."
    input_formats = {"fasta"}
    output_formats = {"fasta", "txt"}
    parameter_schema = object_schema(
        {"abundance_file": PATH_TEXT, "threads": THREADS}, ["abundance_file"]
    )

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "-contig", str(context.inputs[0]),
            "-abund", parameters["abundance_file"],
            "-out", str(context.work_dir / "maxbin" / "bin"),
            "-thread", str(parameters.get("threads", 4)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "maxbin"]

    def prepare_directories(self, context, parameters):
        return [context.work_dir / "maxbin"]


class ConcoctBinningSkill(LocalCliSkill):
    name = "concoct_binning"
    description = "Bin metagenomic contigs using composition and coverage with CONCOCT."
    executable_candidates = ("concoct",)
    official_url = "https://github.com/BinPro/CONCOCT"
    installation_hint = "Install CONCOCT from Bioconda and prepare a coverage table."
    input_formats = {"fasta"}
    output_formats = {"csv"}
    parameter_schema = object_schema(
        {"coverage_file": PATH_TEXT, "threads": THREADS}, ["coverage_file"]
    )

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "--composition_file", str(context.inputs[0]),
            "--coverage_file", parameters["coverage_file"],
            "--basename", str(context.work_dir / "concoct") + "/",
            "--threads", str(parameters.get("threads", 4)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "concoct"]

    def prepare_directories(self, context, parameters):
        return [context.work_dir / "concoct"]


class DasToolRefineSkill(LocalCliSkill):
    min_inputs = 2
    max_inputs = None
    name = "dastool_refine"
    description = "Integrate multiple binning results into a consensus MAG set with DAS Tool."
    executable_candidates = ("DAS_Tool",)
    official_url = "https://github.com/cmks/DAS_Tool"
    installation_hint = "Install DAS Tool and prepare contig-to-bin tables for each binner."
    input_formats = {"fasta", "tsv"}
    output_formats = {"fasta", "tsv"}
    parameter_schema = object_schema(
        {"labels": {"type": "array", "items": {"type": "string"}, "minItems": 1}, "threads": THREADS},
        ["labels"],
    )

    def build_command(self, context, parameters, executable):
        if len(context.inputs) < 2:
            raise ValueError("DAS Tool requires contigs followed by bin mapping tables")
        tables = context.inputs[1:]
        labels = parameters["labels"]
        if len(labels) != len(tables):
            raise ValueError("DAS Tool labels must match the number of bin tables")
        return [
            executable,
            "-i", ",".join(str(path) for path in tables),
            "-l", ",".join(labels),
            "-c", str(context.inputs[0]),
            "-o", str(context.work_dir / "dastool" / "refined"),
            "-t", str(parameters.get("threads", 4)),
            "--write_bins",
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "dastool"]

    def prepare_directories(self, context, parameters):
        return [context.work_dir / "dastool"]


class Checkm2QualitySkill(LocalCliSkill):
    name = "checkm2_quality"
    description = "Estimate MAG completeness and contamination with CheckM2."
    executable_candidates = ("checkm2",)
    official_url = "https://github.com/chklovski/CheckM2"
    installation_hint = "Install CheckM2 and download its model database separately."
    input_formats = {"directory"}
    output_formats = {"tsv", "txt"}
    parameter_schema = object_schema(
        {"database": PATH_TEXT, "threads": THREADS}, ["database"]
    )

    def build_command(self, context, parameters, executable):
        return [
            executable, "predict",
            "--input", str(context.inputs[0]),
            "--output-directory", str(context.work_dir / "checkm2"),
            "--database_path", parameters["database"],
            "--threads", str(parameters.get("threads", 4)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "checkm2"]


class DrepDereplicateSkill(LocalCliSkill):
    max_inputs = None
    name = "drep_dereplicate"
    description = "Dereplicate related metagenome-assembled genomes with dRep."
    executable_candidates = ("dRep",)
    official_url = "https://github.com/MrOlm/drep"
    installation_hint = "Install dRep with its ANI dependencies in a dedicated environment."
    input_formats = {"fasta", "directory"}
    output_formats = {"fasta", "csv"}
    parameter_schema = object_schema(
        {
            "threads": THREADS,
            "completeness": {"type": "number", "minimum": 0, "maximum": 100},
            "contamination": {"type": "number", "minimum": 0, "maximum": 100},
            "secondary_ani": {"type": "number", "minimum": 0, "maximum": 1},
        }
    )

    def build_command(self, context, parameters, executable):
        return [
            executable, "dereplicate", str(context.work_dir / "drep"),
            "-g", *[str(path) for path in context.inputs],
            "-p", str(parameters.get("threads", 4)),
            "-comp", str(parameters.get("completeness", 50)),
            "-con", str(parameters.get("contamination", 10)),
            "-sa", str(parameters.get("secondary_ani", 0.95)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "drep"]


class GtdbtkClassifySkill(LocalCliSkill):
    name = "gtdbtk_classify"
    description = "Assign taxonomy to bacterial and archaeal MAGs with GTDB-Tk."
    executable_candidates = ("gtdbtk",)
    official_url = "https://github.com/Ecogenomics/GTDBTk"
    installation_hint = "Install GTDB-Tk and configure the matching GTDB reference database."
    input_formats = {"directory"}
    output_formats = {"tsv", "tree"}
    parameter_schema = object_schema(
        {"extension": {"type": "string"}, "threads": THREADS}
    )

    def build_command(self, context, parameters, executable):
        return [
            executable, "classify_wf",
            "--genome_dir", str(context.inputs[0]),
            "--out_dir", str(context.work_dir / "gtdbtk"),
            "--extension", parameters.get("extension", "fa"),
            "--cpus", str(parameters.get("threads", 4)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "gtdbtk"]
