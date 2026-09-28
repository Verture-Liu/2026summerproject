/* PaleoRigor — How it works: language switch, step-through walkthrough, module shelf and sequence field. */
(() => {
  "use strict";

  const ZH = {
    skip: "跳到正文",
    navRun: "运行原理", navUse: "使用方法", navInstall: "安装", navExplorer: "基准测试浏览",
    heroEyebrow: "PALEORIGOR 如何工作",
    heroTitle: "一个会亮出计划、守住边界、留下证据的科研智能体。",
    heroLead: "你用自然语言描述想做的分析。语言模型起草 workflow，应用检查它，你批准它，然后由你电脑上的技能执行。每次运行都会留下一个之后可以审计的文件夹。",
    heroTry: "逐步看一个例子", heroInstall: "安装应用",
    coreAgent: "智能体", coreAgentText: "模型把你的请求变成一个明确、有序的 workflow。它只负责规划，从不接触你的文件。",
    coreConstraint: "约束", coreConstraintText: "校验器检查每个文件引用、格式和步骤依赖。只有已注册的技能可以运行；越过既定边界的请求会被拒绝，并给出原因代码。",
    coreRepro: "可复现", coreReproText: "最终结果、中间文件、运行报告和 SHA-256 校验值保存在一起，不用再次调用模型就能核对每一次运行。",
    benchIndex: "运行原理",
    benchTitle: "跟着一个请求，从问题走到记录。",
    benchLead: "选一个示例请求，然后逐步走过六个阶段。受支持的请求会一直走到结果文件夹；越过边界的请求会提前停下，什么都不会运行。",
    prev: "上一步", next: "下一阶段",
    benchNote: "示例仅作演示：文件名、参数和规划器的说明是为本页编写的；技能名称、schema 字段、原因代码、校验信息和文件夹名称与应用中完全一致。",
    useIndex: "使用方法", useTitle: "桌面应用里的五个步骤。",
    useLead: "这五步对应应用顶部的进度条，按钮名称与界面上显示的一致。",
    u1Title: "模型 API",
    u1Text: "填写兼容 OpenAI 接口的服务商的 Base URL、Model 和 API Key，然后点 <b>保存配置</b> 和 <b>测试连接</b>。密钥保存在 macOS 钥匙串（Windows 上为凭据管理器）中，之后不会再显示。",
    u2Title: "上传文件",
    u2Text: "用一两句话描述任务并添加文件（FASTQ、FASTA、CSV、TSV 等），然后点 <b>创建任务并上传</b>。应用在本地检查每个文件，并记录它的格式和 SHA-256 校验值。",
    u3Title: "生成 workflow",
    u3Text: "点 <b>生成 Workflow</b>。模型收到的是你的请求和每个文件的摘要（文件名、格式、大小、列名、记录数），而不是文件内容。你会得到一张通过校验的数据流图，或者一张带原因代码的拒绝卡片。",
    u4Title: "选择结果文件夹",
    u4Text: "逐条阅读每个步骤及其理由，然后点 <b>选择结果文件夹</b>，并勾选 <i>我已检查 workflow，并同意在本地运行这些 Skills。</i> 你勾选之前，什么都不会运行。",
    u5Title: "本地运行",
    u5Text: "点 <b>运行 Workflow</b>。应用会再校验一次计划，然后在你的电脑上逐个运行技能，并显示逐步日志。结束后，<b>打开运行报告</b> 会列出运行了什么、生成了哪些文件。",
    tipsTitle: "怎样写出容易规划的请求",
    tip1: "说清楚文件和想要的输出：“对两个配对文件运行 FastQC，并给我一份 MultiQC 报告。”",
    tip2: "写明你在意的参数，比如长度范围或参考基因组。比对和去宿主需要指定参考基因组或索引，规划器不会替你选一个。",
    tip3: "请求证据，而不是结论。“汇总 reads 质量”是一个任务；“证明这些 reads 是古老的”是一个会被拒绝的断言。",
    recIndex: "你会得到什么",
    recTitle: "每次运行一个文件夹，结果和它的来历分开存放。",
    recLead: "你要的文件放在 final_outputs 里。解释这些文件如何产生的全部内容放在旁边，同事或审稿人不需要应用和模型也能核对这次运行。",
    treeFinal: "# 你要的文件", treeStep: "# 每一步的全部中间文件", treeReport: "# 按顺序记录运行了什么",
    treeManifest: "# workflow 与每个文件的 SHA-256", treeLogs: "# 工具输出和警告",
    treeNote: "文件夹名称与应用一致；这里的时间戳和任务 ID 只是示例。被拒绝的请求不会生成结果文件夹，而是在任务文件夹里写入 planning_decision.json（你的请求和原因代码）。",
    insIndex: "安装", insTitle: "运行 PaleoRigor 的三种方式。",
    macKicker: "推荐 · APPLE SILICON", macTitle: "macOS 应用",
    mac1: "从 GitHub 的 paleorigor 文件夹下载 PaleoRigor-dev-arm64.dmg（需要 macOS 13 或更高版本）。",
    mac2: "把 PaleoRigor.app 拖进“应用程序”文件夹。",
    mac3: "第一次打开时，按住 Control 点按应用并选择“打开”，因为这个开发版使用的是临时签名，没有经过公证。",
    macBundled: "内置 FastQC 0.12.1、MultiQC 1.35、SeqKit 2.13.0、SeqTk 1.5-r133、Samtools 1.23.1、BWA 0.7.19-r1273 和 Bowtie2 2.5.5 及其运行环境。不需要安装 Python、Conda、Java 或 Homebrew。",
    macLink: "打开下载文件夹 →",
    winKicker: "WINDOWS 10/11 X64", winTitle: "Windows 安装程序",
    winText: "从 GitHub 的 paleorigor/windows 文件夹下载 PaleoRigor-Setup.exe 并运行。它和 macOS 版来自同一份源码，内置同样的七个工具（Windows 上 Samtools 为 1.24）。凭据保存在 Windows 凭据管理器中。安装程序没有代码签名，Windows SmartScreen 可能提示“未知发布者”。",
    winCheck: "安装、工具、后台和卸载的原生检查结果记录在 verification.json 中，SHA256SUMS.txt 里是它的校验值。",
    winLink: "打开下载文件夹 →",
    winBuild: "安装程序是怎么构建的 →",
    srcKicker: "从源码运行", srcTitle: "Python 包",
    copy: "复制命令",
    srcNote: "工具来自你已配置的环境；缺少的工具只会报告，不会自动安装。",
    verify: "用 SHA256SUMS.txt 核对下载的镜像：",
    limIndex: "边界", limTitle: "智能体会拒绝什么，永远不会做什么。",
    limLead: "这些边界在调用模型之前就写进了规划契约。拒绝是一种结果而不是错误：应用会显示原因，并且什么都不运行。",
    never1: "它不做古 DNA 真实性鉴定，也不判断污染来源。这些判断留给古生物学家。",
    never2: "它不能编写或运行已安装技能模块之外的代码。",
    never3: "它不会安装缺失的软件，也不会替换参考基因组。",
    never4: "未经你批准，它不会运行任何东西。",
    rc1: "质控结果无法证明 reads 是古老的或没有污染。",
    rc2: "缺少必需的输入，例如比对后的数据或指定的参考基因组或索引。",
    rc3: "请求的操作与上传文件的格式不符。",
    rc4: "请求提到的双端测序配对文件没有上传。",
    modIndex: "技能模块", modTitle: "7 个模块中的 67 个技能，计划只能用这些。",
    modLead: "模块清单在调用模型之前就已固定。应用没有内置的工具，需要先装进你的环境，相应技能才能运行。",
    thModule: "模块", thSkills: "技能数", thExamples: "示例",
    evIndex: "测试", evTitle: "在冻结的、预留数据的评估中检验过。",
    evLead: "对照组是在同一个模型上去掉规划契约，其余条件完全相同。每组 24 次运行时，配对差异没有达到统计学显著。",
    evLink: "在基准测试浏览页查看全部 48 次运行 →",
    ev1: "次运行在有规划契约时通过（deepseek-v4-flash），没有契约时为 19 / 24",
    ev2: "为预先注册的 deepseek-v4-pro 重复实验结果，对照组为 19 / 24",
    ev3: "个运行标签从保存的记录中重新计算，全部一致",
    ev4: "条公开测序记录的读数和压缩文件大小与数据库记录一致",
    footTag: "为古微生物组研究准备可审核的证据。",
    footHome: "项目主页", footRepo: "GitHub 仓库", footExplorer: "基准测试浏览",
    footNote: "本页不运行任何分析，也不接收任何数据。真实分析在你批准后由本地应用运行。"
  };

  Object.assign(ZH, {
    seqKey: "背景里，靠近片段断点的碱基会从 C 变成 T、从 G 变成 A，这是古 DNA 的损伤特征。",
    winLocal: "本地科研智能体",
    mac3: "第一次打开时，按住 Control 点按应用并选择“打开”，因为这个开发版是临时签名，没有经过公证。",
    macBundled: "七个工具及其运行环境全部内置，不需要安装 Python、Conda、Java 或 Homebrew。",
    mSave: "保存配置", mUpload: "创建任务并上传", mValid: "✓ 校验通过",
    mApprove: "我已检查 workflow，并同意在本地运行这些 Skills。", mReport: "打开运行报告",
    fdFinal: "答案", fdStep: "过程", fdRec: "凭据",
    evFrozen: "冻结的 v5 轮", evRepeat: "预先注册的重复实验", evWith: "有规划契约", evWithout: "去掉规划契约"
  });

  const T = {
    en: {
      stages: [["Request & files", "You"], ["Plan", "Agent"], ["Validate", "Constraint"], ["Review & approve", "You"], ["Run locally", "Constraint"], ["Record", "Reproducibility"]],
      stageOf: (i, n) => `stage ${i} / ${n}`,
      next: "Next stage", done: "Start again",
      reqH: "The request", reqP: "You describe the task in plain language and upload files. The app inspects each file locally; the model will only see a summary.",
      planH: "The model drafts a workflow", planP: "Each step names one registered skill, its inputs, parameters, declared outputs and a reason. The graph shows how outputs feed later steps.",
      json: "View the workflow JSON",
      blockH: "The model refuses", blockP: "The request crosses a limit written into the planning contract, so the planner returns a blocked decision instead of a workflow.",
      nothingRan: "Nothing was run.", nothingRanP: "Change the request or the uploaded files, then generate the workflow again. The decision is saved as planning_decision.json.",
      valH: "The validator checks the plan", valP: "Before anything can run, the app checks the plan against the uploaded files and the skill registry.",
      valOkMsg: "Validation passed. Every input resolved, no unknown skills.",
      valBadMsg: "Validation needs review.",
      valStop: "Run Workflow stays disabled.", valStopP: "The error is shown with the step it belongs to. Generate the workflow again, or edit the request, and the new plan is checked from the start.",
      checks: ["Every step uses a registered skill", "Every input is an uploaded file or an output declared by an earlier step", "Input formats match what each skill accepts", "Input counts are within each skill's limits"],
      metrics: ["Steps", "Inputs resolved", "Unknown skills", "Warnings"],
      apprH: "You review and approve", apprP: "Read each step and its reason. Choose a results folder and give explicit approval; the run button stays disabled until you do.",
      approval: "I reviewed the workflow and approve running these Skills locally.",
      folder: "Results folder:", runBtn: "Run Workflow",
      runH: "Skills run on your computer", runP: "The app validates the plan once more, then runs each registered skill in order and records inputs, parameters, outputs, warnings and errors for every step.",
      builtIn: "built-in",
      recH: "Everything is kept", recP: "Requested files go to final_outputs; every intermediate file, the report and the checksum manifest are kept beside them.",
      awaiting: "awaiting your approval", approvedG: "approved · ready to run", waitingPlan: "waiting for a plan",
      nothing: "nothing ran", recNote: "report · manifest · logs",
      st: { wait: "waiting", run: "running", done: "done" }
    },
    zh: {
      stages: [["请求与文件", "你"], ["规划", "智能体"], ["校验", "约束"], ["审核与批准", "你"], ["本地运行", "约束"], ["记录", "可复现"]],
      stageOf: (i, n) => `第 ${i} / ${n} 阶段`,
      next: "下一阶段", done: "重新开始",
      reqH: "请求", reqP: "你用自然语言描述任务并上传文件。应用在本地检查每个文件；模型只能看到文件摘要。",
      planH: "模型起草 workflow", planP: "每一步指定一个已注册的技能，以及它的输入、参数、声明的输出和理由。右侧的图显示输出如何流向后面的步骤。",
      json: "查看 workflow JSON",
      blockH: "模型拒绝了请求", blockP: "这个请求越过了写进规划契约的边界，所以规划器返回的是拒绝决定，而不是 workflow。",
      nothingRan: "没有运行任何步骤。", nothingRanP: "修改请求或上传的文件，然后重新生成 workflow。这个决定会保存为 planning_decision.json。",
      valH: "校验器检查计划", valP: "在任何步骤运行之前，应用会拿计划去对照上传的文件和技能注册表。",
      valOkMsg: "校验通过。输入全部解析，无未知技能。",
      valBadMsg: "校验需要复核。",
      valStop: "“运行 Workflow”按钮保持不可用。", valStopP: "错误会和它所属的步骤一起显示。重新生成 workflow 或修改请求后，新计划会从头再校验一次。",
      checks: ["每一步都使用已注册的技能", "每个输入都是上传的文件，或前面步骤声明过的输出", "输入格式符合每个技能接受的格式", "输入数量在每个技能允许的范围内"],
      metrics: ["步骤", "已解析输入", "未知技能", "警告"],
      apprH: "你审核并批准", apprP: "逐条阅读每个步骤及其理由。选择结果文件夹并明确批准；在你批准之前，运行按钮不可用。",
      approval: "我已检查 workflow，并同意在本地运行这些 Skills。",
      folder: "结果文件夹：", runBtn: "运行 Workflow",
      runH: "技能在你的电脑上运行", runP: "应用会再校验一次计划，然后按顺序运行每个已注册的技能，并记录每一步的输入、参数、输出、警告和错误。",
      builtIn: "内置",
      recH: "全部保留", recP: "你要的文件放进 final_outputs；每个中间文件、运行报告和校验值清单都保存在旁边。",
      awaiting: "等待你的批准", approvedG: "已批准 · 可以运行", waitingPlan: "等待规划",
      nothing: "没有运行", recNote: "报告 · 清单 · 日志",
      st: { wait: "等待", run: "运行中", done: "完成" }
    }
  };

  /* ------------------------------------------------------ data */
  const MODULES = [
    ["workflow-utilities", ["file_type_detect", "fastq_pair_match", "tool_environment_check", "data_quality_gate", "sample_sheet_validate", "multiqc_summary"]],
    ["ancient-dna-core", ["sample_sheet_prepare", "fastq_qc", "host_dna_removal", "ancient_dna_authentication"]],
    ["sequence-utilities", ["seqkit_stats", "seqkit_length_filter", "seqkit_deduplicate", "seqtk_sample", "gzip_decompress", "gzip_compress"]],
    ["peptide-table", ["peptide_csv_normalize", "peptide_validate", "peptide_label_filter", "peptide_length_filter", "peptide_deduplicate", "peptide_statistics", "peptide_chart", "peptide_csv_export", "peptide_properties", "peptide_candidate_rank"]],
    ["ancient-metagenome-tools", ["fastp_preprocess", "adapterremoval_preprocess", "cutadapt_preprocess", "metaphlan_profile", "kraken2_profile", "malt_profile", "megahit_assembly", "metaspades_assembly", "metabat2_binning", "maxbin2_binning", "concoct_binning", "dastool_refine", "checkm2_quality", "drep_dereplicate", "gtdbtk_classify", "bwa_align", "bowtie2_align", "samtools_sort_index", "samtools_stats", "picard_markduplicates", "dedup_pcr_duplicates", "damageprofiler_profile", "qualimap_bamqc", "mosdepth_coverage", "bracken_abundance", "humann_profile", "diamond_blastx", "blastn_search"]],
    ["legacy-core", ["table_filter", "peptide_filter", "environmental_decontamination", "fastq_quality_filter", "metagenome_assembly", "orf_extraction", "cross_sample_presence_filter", "sequence_deduplicate", "cytotoxicity_prediction"]],
    ["amplit", ["amp_prediction", "amplify_prediction", "amp_scanner_prediction", "modlamp_descriptor"]]
  ];
  const SKILL_MODULE = {};
  MODULES.forEach(([m, list]) => list.forEach((s) => { SKILL_MODULE[s] = m; }));
  const mcol = (skill) => `var(--m-${SKILL_MODULE[skill] || "legacy-core"})`;
  const USER_FACING = new Set(["peptide_statistics", "peptide_chart", "peptide_csv_export", "fastq_qc", "multiqc_summary", "file_type_detect"]);

  const R1 = { source: "uploaded", ref: "lib01_R1.fastq" };
  const R2 = { source: "uploaded", ref: "lib01_R2.fastq" };
  const fastqSteps = (ref3) => [
    { id: "step_01", skill: "file_type_detect", inputs: [R1, R2], parameters: {}, outputs: [{ name: "file_types", format: "json" }], reason: "Confirm both uploads are FASTQ before planning QC." },
    { id: "step_02", skill: "fastq_pair_match", inputs: [R1, R2], parameters: {}, outputs: [{ name: "pairs", format: "csv" }], reason: "Check that R1 and R2 form one paired-end sample." },
    { id: "step_03", skill: "fastq_qc", inputs: [R1], parameters: {}, outputs: [{ name: "r1_fastqc", format: "zip" }], reason: "Raw QC for mate 1." },
    { id: "step_04", skill: "fastq_qc", inputs: [R2], parameters: {}, outputs: [{ name: "r2_fastqc", format: "zip" }], reason: "Raw QC for mate 2, as a separate step." },
    { id: "step_05", skill: "multiqc_summary", inputs: [{ source: "step", ref: ref3 }, { source: "step", ref: "step_04.r2_fastqc" }], parameters: {}, outputs: [{ name: "multiqc_report", format: "html" }], reason: "Combine both FastQC reports into one report." }
  ];
  const fastqFiles = [["lib01_R1.fastq.gz", "fastq", "lib01_R1.fastq"], ["lib01_R2.fastq.gz", "fastq", "lib01_R2.fastq"]];
  const TOOLS = { fastq_qc: "FastQC 0.12.1", multiqc_summary: "MultiQC 1.35" };
  const P = { source: "uploaded", ref: "peptides" };
  const peptideSteps = [
    { id: "step_01", skill: "peptide_csv_normalize", inputs: [P], parameters: {}, outputs: [{ name: "normalized", format: "csv" }], reason: "Bring the table to canonical label and sequence columns." },
    { id: "step_02", skill: "peptide_validate", inputs: [{ source: "step", ref: "step_01.normalized" }], parameters: {}, outputs: [{ name: "validated_csv", format: "csv" }, { name: "rejected_csv", format: "csv" }], reason: "Check labels and amino-acid syntax; keep rejected rows for audit." },
    { id: "step_03", skill: "peptide_deduplicate", inputs: [{ source: "step", ref: "step_02.validated_csv" }], parameters: {}, outputs: [{ name: "deduplicated", format: "csv" }], reason: "Remove duplicate sequences and flag label conflicts." },
    { id: "step_04", skill: "data_quality_gate", inputs: [{ source: "step", ref: "step_03.deduplicated" }], parameters: {}, outputs: [{ name: "quality_gate", format: "json" }], reason: "Check the cleaned table before filtering." },
    { id: "step_05", skill: "peptide_length_filter", inputs: [{ source: "step", ref: "step_03.deduplicated" }], parameters: { min_length: 13, max_length: 26 }, outputs: [{ name: "length_filtered", format: "csv" }], reason: "Keep peptides of 13 to 26 residues, as requested." },
    { id: "step_06", skill: "peptide_statistics", inputs: [{ source: "step", ref: "step_05.length_filtered" }], parameters: {}, outputs: [{ name: "statistics_json", format: "json" }, { name: "statistics_csv", format: "csv" }], reason: "Summarise counts, lengths and labels." },
    { id: "step_07", skill: "peptide_csv_export", inputs: [{ source: "step", ref: "step_05.length_filtered" }], parameters: {}, outputs: [{ name: "export", format: "csv" }], reason: "Export the filtered table." }
  ];

  const SCN = [
    { id: "fastq", kind: "ok", title: { en: "Paired FASTQ quality control", zh: "双端 FASTQ 质控" }, sub: { en: "Supported · runs to the end", zh: "受支持 · 走完全程" },
      request: { en: "Run quality control on both mates of this paired-end library and summarise the reports on one page.", zh: "对这组双端测序数据的两个配对文件做质控，并把报告汇总成一页。" },
      files: fastqFiles, plan: { schema_version: "1.0", task_summary: "Paired-end raw QC with one combined MultiQC report.", steps: fastqSteps("step_03.r1_fastqc") } },
    { id: "peptide", kind: "ok", title: { en: "Peptide table curation", zh: "肽序列表整理" }, sub: { en: "Supported · runs to the end", zh: "受支持 · 走完全程" },
      request: { en: "Clean this peptide table, remove duplicate sequences, keep peptides of 13 to 26 amino acids and export the result with summary statistics.", zh: "整理这份肽序列表：去掉重复序列，保留 13 到 26 个氨基酸的肽，并导出结果和统计摘要。" },
      files: [["peptides.csv", "csv", "peptides"]], plan: { schema_version: "1.0", task_summary: "Normalise, validate, deduplicate and length-filter a peptide table, then export it with statistics.", steps: peptideSteps } },
    { id: "catch", kind: "catch", title: { en: "A planning error the validator catches", zh: "被校验器拦下的规划错误" }, sub: { en: "Stops at validation", zh: "在校验阶段停下" },
      request: { en: "Run quality control on both mates of this paired-end library and summarise the reports on one page.", zh: "对这组双端测序数据的两个配对文件做质控，并把报告汇总成一页。" },
      files: fastqFiles, plan: { schema_version: "1.0", task_summary: "Paired-end raw QC with one combined MultiQC report.", steps: fastqSteps("step_03.fastqc_report") },
      issue: "step_05: missing earlier step output step_03.fastqc_report", badRef: "step_03.fastqc_report", stopAt: 2 },
    { id: "claim", kind: "refuse", title: { en: "An unsupported scientific claim", zh: "无法支持的科学断言" }, sub: { en: "Refused at planning", zh: "在规划阶段被拒绝" },
      request: { en: "Use FastQC to prove that these reads are ancient and free of contamination.", zh: "用 FastQC 证明这些 reads 是古老的，而且没有污染。" },
      files: fastqFiles, blocked: { status: "blocked", reason_code: "unsupported_scientific_claim", message: "FastQC reports read quality. It cannot establish ancient origin or the absence of contamination; that needs authentication evidence reviewed by a specialist." }, stopAt: 1 },
    { id: "mate", kind: "refuse", title: { en: "A missing paired-end mate", zh: "缺少配对文件" }, sub: { en: "Refused at planning", zh: "在规划阶段被拒绝" },
      request: { en: "Run FastQC on R1 and R2 of lib01 and compare the two mates.", zh: "对 lib01 的 R1 和 R2 运行 FastQC，并比较两个配对文件。" },
      files: [["lib01_R1.fastq.gz", "fastq", "lib01_R1.fastq"]], missingFile: "lib01_R2 ?",
      blocked: { status: "blocked", reason_code: "missing_mate", message: "Only lib01_R1 was uploaded. The R2 mate named in the request is not available, so it cannot be compared." }, stopAt: 1 }
  ];
  const BADGE = { ok: { en: "Supported", zh: "受支持" }, catch: { en: "Validator catch", zh: "校验拦截" }, refuse: { en: "Refused", zh: "拒绝" } };
  const CORE = ["you", "agent", "constraint", "you", "constraint", "repro"];

  /* ------------------------------------------------------ state */
  let lang = "en", scn = SCN[0], stage = 0, approved = false, runTimer = 0, runIndex = -1, selectedModule = "workflow-utilities";
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const lastStage = () => (scn.stopAt !== undefined ? scn.stopAt : 5);

  const highlight = (obj) => {
    const json = JSON.stringify(obj, null, 2);
    const re = /("(?:\\.|[^"\\])*")(\s*:)?/g;
    let out = "", last = 0, prevKey = "", m;
    while ((m = re.exec(json))) {
      out += esc(json.slice(last, m.index));
      if (m[2]) { prevKey = JSON.parse(m[1]); out += `<span class="k">${esc(m[1])}</span>${m[2]}`; }
      else out += `<span class="${prevKey === "skill" ? "sk" : prevKey === "reason_code" ? "rc" : "s"}">${esc(m[1])}</span>`;
      last = re.lastIndex;
    }
    return out + esc(json.slice(last));
  };

  /* ------------------------------------------------------ graph */
  const W = 580, NH = 40, ROWH = 74, TOP = 14;
  function layout() {
    const rows = [];
    const pos = {};
    const files = scn.files.map(([name, fmt, ref]) => ({ kind: "file", id: `up:${ref}`, label: name, sub: fmt }));
    if (scn.missingFile) files.push({ kind: "file", id: "up:missing", label: scn.missingFile, sub: "missing", missing: true });
    rows[0] = files;
    const depth = {};
    const steps = scn.plan ? scn.plan.steps : [];
    steps.forEach((s) => {
      let d = 1;
      s.inputs.forEach((i) => { if (i.source === "step") { const src = i.ref.split(".")[0]; if (depth[src]) d = Math.max(d, depth[src] + 1); } });
      depth[s.id] = d;
      (rows[d] = rows[d] || []).push({ kind: "step", id: s.id, label: s.skill, sub: s.id, step: s });
    });
    const nSteps = rows.length;
    if (!scn.plan) rows[1] = [{ kind: "block", id: "block", label: scn.blocked.reason_code }];
    const folderRow = rows.length;
    rows[folderRow] = [
      { kind: "folder", id: "f:final", label: "final_outputs", c: "var(--repro)" },
      { kind: "folder", id: "f:step", label: "step_outputs", c: "var(--agent)" },
      { kind: "folder", id: "f:rec", label: "ResearchAgent Records", c: "var(--constraint)" }
    ];
    rows.forEach((row, r) => {
      if (!row) return;
      const widths = row.map((n) => n.kind === "block" ? 300 : Math.max(118, n.label.length * 7 + 26));
      const gap = 12;
      let total = widths.reduce((a, b) => a + b, 0) + gap * (row.length - 1);
      const scale = total > W - 8 ? (W - 8 - gap * (row.length - 1)) / (total - gap * (row.length - 1)) : 1;
      const ws = widths.map((w) => w * scale);
      total = ws.reduce((a, b) => a + b, 0) + gap * (row.length - 1);
      let x = (W - total) / 2;
      row.forEach((n, i) => { pos[n.id] = { x, y: TOP + r * ROWH, w: ws[i], h: n.kind === "block" ? 54 : NH, n }; x += ws[i] + gap; });
    });
    const edges = [];
    steps.forEach((s) => s.inputs.forEach((i) => {
      if (i.source === "uploaded") edges.push({ from: `up:${i.ref}`, to: s.id });
      else {
        const src = i.ref.split(".")[0];
        edges.push({ from: src, to: s.id, bad: scn.badRef === i.ref, ref: i.ref });
      }
    }));
    return { pos, edges, height: TOP + (folderRow + 1) * ROWH - 14, folderRow, nSteps };
  }
  const curve = (a, b) => {
    const x1 = a.x + a.w / 2, y1 = a.y + a.h, x2 = b.x + b.w / 2, y2 = b.y;
    const my = (y1 + y2) / 2;
    return `M${x1.toFixed(1)} ${y1} C${x1.toFixed(1)} ${my} ${x2.toFixed(1)} ${my} ${x2.toFixed(1)} ${y2}`;
  };

  function graphSVG() {
    const t = T[lang];
    const L = layout();
    const showFolders = stage >= 5;
    const height = showFolders ? L.height : L.height - ROWH;
    const planned = stage >= 1 && scn.plan;
    let edges = "", nodes = "", extra = "";
    if (planned) {
      L.edges.forEach((e, i) => {
        const a = L.pos[e.from], b = L.pos[e.to];
        if (!a || !b) return;
        let cls = "g-edge";
        if (stage === 1) cls += " drawn";
        if (stage >= 2) cls += e.bad ? " bad" : " ok";
        if (stage >= 4) cls += " live";
        edges += `<path class="${cls}" id="e-${i}" d="${curve(a, b)}" style="animation-delay:${(i * 0.06).toFixed(2)}s"/>`;
        if (e.bad && stage >= 2) {
          const mx = (a.x + a.w / 2 + b.x + b.w / 2) / 2 + 8, my = (a.y + a.h + b.y) / 2;
          extra += `<text class="g-lbl" x="${mx.toFixed(0)}" y="${my.toFixed(0)}">✕ ${esc(e.ref)}</text>`;
        }
      });
    }
    Object.values(L.pos).forEach((p, idx) => {
      const n = p.n;
      if (n.kind === "file") {
        nodes += `<g class="g-file${n.missing ? " missing" : ""}"><rect x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}" rx="20"/>
          <text x="${p.x + p.w / 2}" y="${p.y + 24}" text-anchor="middle">${esc(n.label)}</text></g>`;
      } else if (n.kind === "step") {
        let cls = "g-node";
        if (stage === 0) cls += " ghost";
        if (stage === 1) cls += " appear";
        if (scn.badRef && stage >= 2 && n.step.inputs.some((i) => i.ref === scn.badRef)) cls += " bad";
        const si = scn.plan.steps.indexOf(n.step);
        if (stage === 4) cls += si < runIndex ? " done" : si === runIndex ? " running" : "";
        if (stage >= 5) cls += " done";
        const tick = (stage >= 2 && !cls.includes("bad") && !cls.includes("ghost") && (stage !== 4 || si < runIndex)) || stage >= 5;
        nodes += `<g class="${cls}" style="--c:${mcol(n.label)};animation-delay:${(si * 0.08).toFixed(2)}s" data-si="${si}">
          <rect class="body" x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}" rx="9"/>
          <rect class="stripe" x="${p.x}" y="${p.y + 6}" width="4" height="${p.h - 12}" rx="2"/>
          <text class="t1" x="${p.x + 13}" y="${p.y + 17}">${esc(n.label)}</text>
          <text class="t2" x="${p.x + 13}" y="${p.y + 31}">${esc(n.sub)}</text>
          ${tick ? `<circle class="tick" cx="${p.x + p.w - 8}" cy="${p.y}" r="7"/><text x="${p.x + p.w - 8}" y="${p.y + 3.5}" text-anchor="middle" font-size="9" fill="white" font-weight="700">✓</text>` : ""}</g>`;
      } else if (n.kind === "block" && stage >= 1) {
        nodes += `<g class="g-block"><rect x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}" rx="12"/>
          <text x="${p.x + p.w / 2}" y="${p.y + 22}" text-anchor="middle" font-size="10.5" letter-spacing="1.5">BLOCKED · ${esc(t.nothing.toUpperCase())}</text>
          <text x="${p.x + p.w / 2}" y="${p.y + 40}" text-anchor="middle" font-size="12" font-weight="700">${esc(n.label)}</text></g>`;
        scn.files.forEach(([, , ref]) => { const a = L.pos[`up:${ref}`]; if (a) edges += `<path class="g-edge bad" d="${curve(a, p)}"/>`; });
        if (scn.missingFile) { const a = L.pos["up:missing"]; edges += `<path class="g-edge bad" d="${curve(a, p)}"/>`; }
      } else if (n.kind === "folder" && showFolders) {
        nodes += `<g class="g-folder g-node appear" style="animation-delay:${(0.1 + idx * 0.02).toFixed(2)}s">
          <path d="M${p.x} ${p.y + 6} q0 -6 6 -6 h${p.w * 0.35} l6 6 h${p.w * 0.65 - 18} q6 0 6 6 v${p.h - 6} q0 6 -6 6 h${-(p.w - 12)} q-6 0 -6 -6z" fill="color-mix(in srgb, ${n.c} 14%, white)" stroke="${n.c}" stroke-width="1.4"/>
          <text x="${p.x + p.w / 2}" y="${p.y + 26}" text-anchor="middle" fill="${n.c}" font-weight="600">${esc(n.label)}</text></g>`;
      }
    });
    if (showFolders && planned) {
      const F = L.pos["f:final"], S = L.pos["f:step"], R = L.pos["f:rec"];
      const feeds = new Set(scn.plan.steps.flatMap((s) => s.inputs.filter((i) => i.source === "step").map((i) => i.ref.split(".")[0])));
      scn.plan.steps.forEach((s) => {
        const a = L.pos[s.id];
        if (!feeds.has(s.id)) edges += `<path class="g-edge drawn" d="${curve(a, S)}" style="stroke:color-mix(in srgb, var(--agent) 40%, white)"/>`;
        if (USER_FACING.has(s.skill)) edges += `<path class="g-edge drawn" d="${curve(a, F)}" style="stroke:var(--repro)"/>`;
      });
      extra += `<text class="g-lbl" style="fill:var(--constraint)" x="${R.x + R.w / 2}" y="${R.y - 8}" text-anchor="middle">${esc(t.recNote)}</text>`;
    }
    if (planned && (stage === 3 || stage === 0)) {
      const y = TOP + (L.nSteps) * ROWH - 30;
      extra += `<g class="g-lock"><text x="${W / 2}" y="${y}" text-anchor="middle">${approved ? "— " + esc(t.approvedG) + " —" : "— " + esc(t.awaiting) + " —"}</text></g>`;
    }
    if (stage === 0 && scn.plan) {
      extra += `<g class="g-lock"><text x="${W / 2}" y="${TOP + ROWH - 18}" text-anchor="middle">… ${esc(t.waitingPlan)}</text></g>`;
    }
    const h = scn.plan ? height : TOP + 2 * ROWH + 10;
    return `<svg viewBox="-4 -12 ${W + 8} ${h + 16}" role="img" aria-label="Workflow graph">${edges}${nodes}${extra}<g id="pulses"></g></svg>`;
  }

  function legendHTML() {
    if (!scn.plan) return "";
    const used = [...new Set(scn.plan.steps.map((s) => SKILL_MODULE[s.skill]))];
    return used.map((m) => `<span><i style="--c: var(--m-${m})"></i>${esc(m)}</span>`).join("");
  }

  /* ------------------------------------------------------ panel */
  function panelHTML() {
    const t = T[lang];
    const tag = (i) => `<span class="hw-core-tag ${CORE[i]}">${esc(t.stages[i][1])}</span>`;
    const files = `<div class="hw-files">${scn.files.map(([n, f]) => `<span class="hw-file">${esc(n)} <em>${esc(f)}</em></span>`).join("")}</div>`;
    switch (stage) {
      case 0:
        return `${tag(0)}<h3>${esc(t.reqH)}</h3><p>${esc(t.reqP)}</p><div class="hw-request">${esc(scn.request[lang])}</div>${files}`;
      case 1:
        if (scn.blocked) return `${tag(1)}<h3>${esc(t.blockH)}</h3><p>${esc(t.blockP)}</p><pre class="hw-json">${highlight(scn.blocked)}</pre>
          <div class="hw-stop"><strong>${esc(t.nothingRan)}</strong><p>${esc(t.nothingRanP)}</p></div>`;
        return `${tag(1)}<h3>${esc(t.planH)}</h3><p>${esc(t.planP)}</p>
          <ol class="hw-steps-mini">${scn.plan.steps.map((s) => `<li><code style="color:${mcol(s.skill)}">${esc(s.id)}</code><span><code>${esc(s.skill)}</code> — ${esc(s.reason)}</span></li>`).join("")}</ol>
          <details class="hw-json-toggle"><summary>${esc(t.json)}</summary><pre class="hw-json">${highlight(scn.plan)}</pre></details>`;
      case 2: {
        const bad = !!scn.issue, n = scn.plan.steps.reduce((k, s) => k + s.inputs.length, 0);
        const checks = t.checks.map((c, i) => { const f = bad && i === 1; return `<li class="${f ? "bad" : "ok"}"><span class="ic">${f ? "✕" : "✓"}</span><span>${esc(c)}${f ? `<br><code>${esc(scn.issue)}</code>` : ""}</span></li>`; }).join("");
        const m = [scn.plan.steps.length, `${bad ? n - 1 : n}/${n}`, 0, 0];
        return `${tag(2)}<h3>${esc(t.valH)}</h3><p>${esc(t.valP)}</p><ul class="hw-checks">${checks}</ul>
          <div class="hw-metrics">${t.metrics.map((l, i) => `<div><b>${m[i]}</b><span>${esc(l)}</span></div>`).join("")}</div>
          ${bad ? `<div class="hw-stop"><strong>${esc(t.valBadMsg)} ${esc(t.valStop)}</strong><p>${esc(t.valStopP)}</p></div>` : `<p class="hw-okline">✓ ${esc(t.valOkMsg)}</p>`}`;
      }
      case 3:
        return `${tag(3)}<h3>${esc(t.apprH)}</h3><p>${esc(t.apprP)}</p>
          <div class="hw-approve"><span class="hw-folder">${esc(t.folder)} ~/Documents/PaleoRigor results</span>
            <label for="approve-box"><input type="checkbox" id="approve-box" ${approved ? "checked" : ""}><span>${esc(t.approval)}</span></label>
            <button type="button" class="hw-run-btn" id="run-btn" ${approved ? "" : "disabled"}>${esc(t.runBtn)}</button></div>`;
      case 4:
        return `${tag(4)}<h3>${esc(t.runH)}</h3><p>${esc(t.runP)}</p>
          <ol class="hw-log" id="run-log">${scn.plan.steps.map((s) => `<li><span class="st">${esc(t.st.wait)}</span><span><code>${esc(s.skill)}</code></span><span class="tool">${esc(TOOLS[s.skill] || t.builtIn)}</span></li>`).join("")}</ol>`;
      case 5:
        return `${tag(5)}<h3>${esc(t.recH)}</h3><p>${esc(t.recP)}</p>
          <div class="hw-folders" style="grid-template-columns:1fr">
            <div class="fd" style="--c: var(--repro)"><b>final_outputs/</b><span>${scn.plan.steps.filter((s) => USER_FACING.has(s.skill)).map((s) => esc(s.outputs.map((o) => o.name).join(", "))).join(" · ")}</span></div>
            <div class="fd" style="--c: var(--agent)"><b>step_outputs/</b><span>${scn.plan.steps.map((s) => `${esc(s.id)}_${esc(s.skill)}/`).join(" ")}</span></div>
            <div class="fd" style="--c: var(--constraint)"><b>ResearchAgent Records/</b><span>report.html · manifest.json · logs/</span></div>
          </div>`;
      default: return "";
    }
  }

  /* ------------------------------------------------------ render */
  function renderScenarios() {
    $("scenario-list").innerHTML = SCN.map((s) => `<button type="button" class="hw-scn ${s.kind}" role="tab" id="scn-${s.id}" data-scn="${s.id}" aria-selected="${s === scn}">
        <span class="hw-badge">${esc(BADGE[s.kind][lang])}</span><strong>${esc(s.title[lang])}</strong><small>${esc(s.sub[lang])}</small></button>`).join("");
  }
  function renderRail() {
    const t = T[lang];
    const pct = (Math.min(stage, lastStage()) / 5) * 100;
    $("stage-rail").innerHTML = `<span class="prog" style="width:calc((100% - 36px - 100% / 6 + 12px) * ${pct / 100})"></span>` + t.stages.map(([name, core], i) => {
      let cls = i < stage ? "done" : i === stage ? "current" : "";
      if (i > lastStage()) cls = "skipped";
      if (scn.stopAt !== undefined && i === scn.stopAt && stage >= i) cls += " stopped";
      return `<li class="${cls}" data-core="${CORE[i]}"><button type="button" data-stage="${i}" ${i > lastStage() ? "disabled" : ""} aria-current="${i === stage ? "step" : "false"}">
        <span class="n">${i + 1}</span><span class="lbl"><small>${esc(core)}</small><b>${esc(name)}</b></span></button></li>`;
    }).join("");
  }
  function renderGraph() { $("stage-graph").innerHTML = graphSVG(); $("graph-legend").innerHTML = legendHTML(); }

  function pulse(si) {
    const g = document.getElementById("pulses");
    if (!g || reduce) return;
    const L = layout();
    const s = scn.plan.steps[si];
    L.edges.forEach((e, i) => {
      if (e.to !== s.id) return;
      const path = document.getElementById(`e-${i}`);
      if (!path) return;
      const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      c.setAttribute("r", "4"); c.setAttribute("class", "g-pulse");
      const am = document.createElementNS("http://www.w3.org/2000/svg", "animateMotion");
      am.setAttribute("dur", "0.55s"); am.setAttribute("fill", "freeze"); am.setAttribute("path", path.getAttribute("d"));
      c.appendChild(am); g.appendChild(c); am.beginElement && am.beginElement();
      window.setTimeout(() => c.remove(), 700);
    });
  }
  function animateRun() {
    window.clearTimeout(runTimer);
    const t = T[lang];
    const items = Array.from(document.querySelectorAll("#run-log li"));
    const setItem = (li, st) => { li.className = st; li.querySelector(".st").textContent = t.st[st === "done" ? "done" : st === "running" ? "run" : "wait"]; };
    const n = scn.plan.steps.length;
    if (reduce) { runIndex = n; items.forEach((li) => setItem(li, "done")); renderGraph(); return; }
    runIndex = 0;
    const tick = () => {
      items.forEach((li, i) => setItem(li, i < runIndex ? "done" : i === runIndex ? "running" : "wait"));
      renderGraph();
      if (runIndex < n) { pulse(runIndex); runIndex += 1; runTimer = window.setTimeout(tick, 650); }
    };
    tick();
  }

  function render() {
    const t = T[lang];
    renderScenarios(); renderRail();
    $("stage-panel").innerHTML = panelHTML();
    if (stage !== 4) renderGraph();
    $("stage-count").textContent = t.stageOf(stage + 1, 6);
    $("prev-stage").disabled = stage === 0;
    const next = $("next-stage");
    next.textContent = stage >= lastStage() ? t.done : t.next;
    next.disabled = stage === 3 && !approved;
    if (stage === 4) animateRun();
    const box = $("approve-box");
    if (box) box.addEventListener("change", () => { approved = box.checked; $("run-btn").disabled = !approved; $("next-stage").disabled = !approved; renderGraph(); });
    const run = $("run-btn");
    if (run) run.addEventListener("click", () => go(4));
  }
  function go(i) {
    window.clearTimeout(runTimer);
    stage = Math.max(0, Math.min(i, lastStage()));
    if (stage < 3) approved = false;
    if (stage >= 4) approved = true;
    render();
  }

  /* ------------------------------------------------------ modules */
  const CUBE = '<svg viewBox="0 0 60 60" aria-hidden="true"><path class="f-top" d="M30 6 54 18 30 30 6 18z"/><path class="f-left" d="M6 18 30 30v26L6 44z"/><path class="f-right" d="M30 30 54 18v26L30 56z"/><path class="f-edge" d="M30 6 54 18 30 30 6 18z M30 30v26"/></svg>';
  function renderModules() {
    $("module-cubes").innerHTML = MODULES.map(([m, list]) => `<button type="button" class="hw-cube" style="--c: var(--m-${m})" data-module="${m}" aria-pressed="${m === selectedModule}">
      ${CUBE}<span class="nm">${esc(m)}</span><span class="ct">${list.length}</span></button>`).join("");
    const [m, list] = MODULES.find(([x]) => x === selectedModule);
    $("module-detail").innerHTML = `<h3 style="--mc: var(--m-${m})">${esc(m)} · ${list.length}</h3><div class="chips" style="--mc: var(--m-${m})">${list.map((s) => `<code>${esc(s)}</code>`).join("")}</div>`;
  }

  /* ------------------------------------------------------ sequence field */
  function sequenceField() {
    const canvas = $("seqField");
    const ctx = canvas && canvas.getContext ? canvas.getContext("2d") : null;
    if (!ctx) return;
    const COLUMN = 17, LINE = 18, LENGTH = 240;
    let width = 0, height = 0, columns = [], frame = 0;
    const rnd = (seed) => { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); };
    const seed = () => {
      const next = rnd(7); columns = [];
      for (let x = 8; x < width; x += COLUMN) {
        const bases = [];
        for (let i = 0; i < LENGTH; i += 1) bases.push(next() < 0.05 ? " " : "ACGT"[(next() * 4) | 0]);
        columns.push({ x, bases, speed: 0.01 + next() * 0.02, offset: next() * 1000, alpha: 0.08 + next() * 0.12 });
      }
    };
    const resize = () => {
      const ratio = Math.min(2, window.devicePixelRatio || 1);
      width = canvas.clientWidth; height = canvas.clientHeight;
      canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0); seed();
    };
    const draw = (time) => {
      ctx.clearRect(0, 0, width, height);
      ctx.font = '500 12px "Fira Code", Menlo, monospace'; ctx.textAlign = "center";
      for (const col of columns) {
        const shift = col.offset + time * col.speed, first = Math.floor(shift / LINE);
        for (let row = 0; row < height / LINE + 2; row += 1) {
          const k = (first + row) % LENGTH, base = col.bases[k];
          if (base === " ") continue;
          const y = row * LINE - (shift % LINE);
          const atBreak = col.bases[(k + 1) % LENGTH] === " " || col.bases[(k - 1 + LENGTH) % LENGTH] === " ";
          if (atBreak) { ctx.globalAlpha = 0.75; ctx.fillStyle = "#f1b476"; ctx.fillText(base === "C" ? "T" : base === "G" ? "A" : base, col.x, y); }
          else { ctx.globalAlpha = col.alpha; ctx.fillStyle = "#bfe9e1"; ctx.fillText(base, col.x, y); }
        }
      }
      ctx.globalAlpha = 1;
    };
    const loop = (tm) => { draw(tm); frame = window.requestAnimationFrame(loop); };
    const start = () => { window.cancelAnimationFrame(frame); if (reduce) draw(0); else frame = window.requestAnimationFrame(loop); };
    resize(); start();
    window.addEventListener("resize", () => { resize(); if (reduce) draw(0); });
    document.addEventListener("visibilitychange", () => { if (document.hidden) window.cancelAnimationFrame(frame); else start(); });
  }

  /* ------------------------------------------------------ language */
  const EN = {};
  function applyLang(next) {
    lang = next;
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!(key in EN)) EN[key] = el.innerHTML;
      el.innerHTML = lang === "zh" && ZH[key] ? ZH[key] : EN[key];
    });
    document.querySelectorAll(".hw-lang-btn").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
    try { localStorage.setItem("paleorigor-lang", lang); } catch (_) { /* storage unavailable */ }
    render();
  }

  /* ------------------------------------------------------ wiring */
  document.addEventListener("click", (e) => {
    const s = e.target.closest("[data-scn]");
    if (s) { scn = SCN.find((x) => x.id === s.dataset.scn); approved = false; go(0); return; }
    const st = e.target.closest("[data-stage]");
    if (st && !st.disabled) { go(Number(st.dataset.stage)); return; }
    const mod = e.target.closest("[data-module]");
    if (mod) { selectedModule = mod.dataset.module; renderModules(); return; }
    const l = e.target.closest(".hw-lang-btn");
    if (l) applyLang(l.dataset.lang);
  });
  $("prev-stage").addEventListener("click", () => go(stage - 1));
  $("next-stage").addEventListener("click", () => { if (stage >= lastStage()) go(0); else go(stage + 1); });
  $("scenario-list").addEventListener("keydown", (e) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const i = SCN.indexOf(scn) + (e.key === "ArrowRight" ? 1 : -1);
    scn = SCN[(i + SCN.length) % SCN.length]; approved = false; go(0);
    const b = $(`scn-${scn.id}`); if (b) b.focus();
  });

  sequenceField();
  renderModules();
  let initial = "en";
  try { initial = localStorage.getItem("paleorigor-lang") || "en"; } catch (_) { /* storage unavailable */ }
  if (location.hash === "#zh") initial = "zh";
  applyLang(initial === "zh" ? "zh" : "en");
})();
