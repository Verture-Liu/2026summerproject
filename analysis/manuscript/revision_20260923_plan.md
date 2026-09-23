# PaleoRigor 改稿方案 — 2026-09-23

基线稿：`latest version_PaleoRigor_Astra_language_polished.docx`（2026-09-21）
策略：只做**不需要补新实验**的修改，把稿子推到"随时可投"状态。

所有数字均已对照 `analysis/benchmark_v5/results/summary.json`、
`analysis/benchmark_multimodel/v4_pro/results/summary.json` 和 48×3 份
`provenance.json` 逐一核验。正文现有数字无一处虚报。

---

## A. 核心问题：把"对照实验"如实重构为"控制层消融实验"

### A.0 为什么必须改

两臂实际收到的 system prompt 差异（证据：运行记录 `request.json` 中的原文，
非源码重构，已导出为 Supplementary File 4）：

| | 控制臂 `raw_llm` | PaleoRigor 臂 |
| --- | ---: | ---: |
| system prompt 总长 | 35,929 字符 | 76,029 字符 |
| 两臂逐字节相同的部分 | 35,682 字符 | 35,682 字符 |
| 该臂独有内容 | **247 字符**（4 句话） | **40,347 字符** |

共同部分（`shared_contract.txt`，35,682 字符，逐字节一致）包含
WORKFLOW_JSON_SCHEMA、BLOCKED_JSON_SCHEMA、FILES、AVAILABLE_SKILLS。
两臂看到的任务、文件、技能目录、响应 schema 完全相同——这部分设计是干净的。

PaleoRigor 臂独有的 40,347 字符包含四样东西：

1. 30 条工作流编排规则（分阶段模板、格式兼容约束、各 skill 输出约定）
2. **一个完整的 `VALID_EXAMPLE` 示例工作流**——控制臂一个示例都没有
3. 6 条 `PALEORIGOR_CONTROL_LAYER` 规则，**逐条点名了四个 reason code**：
   `file_type_mismatch`、`missing_mate`、`unsupported_scientific_claim`、
   `missing_prerequisite`
4. schema / FILES / AVAILABLE_SKILLS 的**第二份副本**（见下方"实现缺陷"）

而 v5 的四个 boundary 场景（H5-B1…B4）测的正是第 3 项点名的那四个码。

因此 "PaleoRigor boundary 12/12" 有相当部分来自提示词里写了答案。把这些规则编码进
系统**本身就是 PaleoRigor 的贡献**，结果不假；但现稿把它描述成
"matched control … minimal planning prompt"，而实际差距是 247 字符 vs 40,347 字符、
外加一个示范样例。审稿人打开仓库两分钟就能发现，并且会用 "circular" 这个词。

### A.0b 附带发现的实现缺陷（建议修，但不影响结果有效性）

`build_system_prompt()`（`src/research_agent/agent/prompts.py`）和
`_common_contract()`（`analysis/benchmark_v2/prompts.py`）各自都拼接了
WORKFLOW_JSON_SCHEMA、FILES、AVAILABLE_SKILLS，导致 PaleoRigor 臂的 prompt 里
这三块**各出现两次**，约 35,000 字符纯属重复。

影响：不改变任务信息，不影响结果有效性，但让 PaleoRigor 臂的 prompt 长度虚高到
控制臂的 2.1 倍，单次调用 prompt token 约 22,386（见 provenance 记录）。修掉可省
近一半 token 成本，也让"长度差异"不再成为可被攻击的混杂因素。

建议：在 `_common_contract()` 中对 paleorigor 臂跳过已由 `build_system_prompt()`
提供的块。若修改，需重跑 v5 与 V4-Pro 并注明版本——所以**投稿前不要动**，
放进"发表后的下一版"。

### A.1 Results 小标题（原 p41）

- 原：`Matched model comparisons assessed the contribution of workflow rules`
- 新：`A control-layer ablation isolated the contribution of the planning contract`

### A.2 Results 正文（原 p42）—— 整段替换

> This comparison was an ablation of the PaleoRigor control layer, not a trial
> against an external tool. Both arms used the same model, task files, workflow
> schema, blocked-decision schema, uploaded-file summaries, skill catalogue,
> call-order protocol, execution path and scoring rules. They differed only in
> the planning instructions. The control arm received a four-sentence planner
> instruction (247 characters). The PaleoRigor arm received the full planning contract, which
> encodes thirty staged-workflow and format-compatibility rules, one worked
> example workflow, and six control-layer rules naming the four boundary reason
> codes the system is designed to emit (40,347 characters in total). The two
> arms' shared task context — schemas, uploaded-file summaries and skill
> catalogue — was byte-identical at 35,682 characters. The boundary comparison
> therefore measures whether an encoded rule is applied consistently, not
> whether a planner identifies the boundary unaided. Both system prompts are
> reproduced verbatim in Supplementary File 4. With V4-Flash, PaleoRigor passed
> 23 of 24 runs (95.8%), compared with 19 of 24 (79.2%) for the ablated arm, a
> difference of 16.7 percentage points. Five paired outcomes favored PaleoRigor
> and one favored the ablated arm (exact McNemar p = 0.219). With V4-Pro, the
> corresponding counts were 24 of 24 and 19 of 24, a difference of 20.8
> percentage points; all five discordant pairs favored PaleoRigor (p = 0.0625).
> Across both configurations, the descriptive totals were 47 of 48 successes
> (97.9%) for PaleoRigor and 38 of 48 (79.2%) for the ablated arms.

### A.3 Abstract Results 段（原 p8）—— 两句改写

- 原：`The same planning model given a minimal workflow prompt passed 19 of 24 (79.2%)`
- 新：`An ablation that removed the PaleoRigor planning contract from the same
  model passed 19 of 24 (79.2%)`
- 原：`Repeating the fixed design with a second model configuration yielded 24 of
  24 successes for PaleoRigor and 19 of 24 for the matched control.`
- 新：`Repeating the frozen design with a second model configuration yielded 24
  of 24 successes for PaleoRigor and 19 of 24 for the ablated arm.`

同样把 Key points 第三条、Table 3 末行、Discussion 与 Conclusions 中所有
`matched (raw-model) control` 一律改为 `ablated arm` / `control-layer ablation`。

### A.4 Limitations 新增一段

> The control arm is an ablation, not an external baseline. Because the
> PaleoRigor planning contract names the four boundary reason codes explicitly,
> the 12 of 12 boundary result shows that the encoded control layer is applied
> consistently; it does not show that the system infers scientific boundaries
> independently. Separating those two effects would require a third arm given
> the boundary rules but not the workflow-staging rules, which was not run.
> Comparison with manual command-line practice, fixed standard operating
> procedures, or established workflow engines such as Snakemake and Nextflow
> also remains outstanding. Until such comparisons are available, these results
> support the internal design claim and not a claim of advantage over current
> practice.

**可选低成本补充实验**（若你后面改主意）：跑一个"知情对照臂"——控制臂也给那 6 条
boundary 规则，但不给 30 条工作流编排规则。24 次调用，约半小时，能把 A.4 里
"was not run" 换成真数据，直接堵死最尖锐的那条审稿意见。

---

## B. 未报告实验臂的如实声明

`analysis/benchmark_multimodel/v4_flash_vision_exp/` 存有第三个模型配置的运行记录，
正文完全未提。审稿人比对仓库时会发现。

**事实**（来自 24 份 provenance.json）：
模型 `deepseek-v4-flash-vision-exp`，仅 `raw_llm` 臂，24 次运行，17 次成功
（70.8%；Wilson 95% CI 50.8–85.1%），无配对 PaleoRigor 臂，
运行于 2026-08-21T13:07–13:17 UTC，code commit `b5d3d18`。

### B.1 Methods「Engineering benchmark protocol」末尾新增

> A third model configuration, deepseek-v4-flash-vision-exp, was also run
> against the frozen v5 design on 21 August 2026, but the experiment was not
> completed: only the control arm was executed (17 of 24 successes, 70.8%). No
> matched PaleoRigor arm was run, so the configuration yields no paired
> comparison and contributes no result to this manuscript. Its manifest, run
> records and summary are retained under
> `analysis/benchmark_multimodel/v4_flash_vision_exp` and are reported here so
> that the repository materials can be reconciled with the results presented
> above.

### B.2 Supplementary Table S6 增一行，标注该配置为 exploratory / incomplete

---

## C. 规划模型与运行环境的完整披露（新增 Methods 小节）

现稿只说了 "one planning model"、temperature 0、thinking mode、JSON mode。
以下全部可从源码与运行记录取得，应完整写出。

### C.1 新增 Methods 小节 `Planning-model configuration`

> All planning calls used the OpenAI-compatible chat-completions endpoint at
> `https://api.deepseek.com`. Each request set `temperature` to 0, enabled the
> provider's extended-reasoning mode (`thinking: enabled`) and required a JSON
> object response (`response_format: json_object`), with a 120 s per-request
> timeout. Transport and HTTP errors were retried up to twice with exponential
> backoff capped at 4 s. When a returned object failed schema validation, the
> planner issued exactly one repair call that resupplied the original system
> prompt together with the validation errors and the invalid object, and
> instructed the model to correct the JSON without changing the intended task; a
> second failure aborted the run. In the reported evaluations no request
> required a retry and no completion required a repair call: every one of the
> 48 v5 runs and 48 V4-Pro runs succeeded on its first attempt. The provider
> exposes no sampling seed, so runs are not bit-reproducible.
>
> The frozen v5 evaluation used `deepseek-v4-flash` and ran on 19 August 2026
> between 02:34 and 02:50 UTC at repository commit `4be5f2f`. The preregistered
> second-model check used `deepseek-v4-pro` and ran on 19 August 2026 between
> 06:52 and 07:14 UTC at commit `728a226`. The only change to the evaluation
> code between those commits was the addition of per-model configuration
> loading in `analysis/benchmark_v2/config.py`; scenarios, prompts, schemas,
> scoring and the agent source were byte-identical. Each run stores its own
> provenance record containing the arm, start and end times, the model string
> reported by the API, token usage, latency, attempt count, repair-call count
> and the repository commit. Both arms' complete system prompts are reproduced
> in Supplementary File 4.

### C.2 新增 Supplementary File 4

内容：两臂 system prompt 全文 + blocked-decision schema + 一份完整 provenance
记录样例。这是堵住 A 节问题最直接的证据。

---

## D. Windows 支持：正文落后于代码，需更新

代码事实：`packaging/windows/` 完整，`.github/workflows/windows-build.yml` 已跑通，
`paleorigor/README.md` 已写明 Windows 安装流程与 Credential Manager 存储。
Windows 端 Samtools 为 **1.24**（macOS 是 1.23.1），Java 为 Eclipse Temurin
21.0.8+9（macOS 是 Azul Zulu 21.0.8）。

### D.1 Results 小标题（原 p56）

- 原：`The macOS application bundled the tools required for local use`
- 新：`Packaged applications bundled the tools required for local use`

### D.2 Results 正文（原 p57）末尾追加

> A Windows 10/11 x64 installer is produced by a separate native build workflow
> from the same backend source, bundling the same seven tools with a Eclipse
> Temurin 21 runtime and storing model credentials in Windows Credential
> Manager. Its tool provenance and archive checksums are pinned in
> `packaging/windows/tool-sources.json`. The reported evaluation was performed
> on macOS; the Windows build was verified by its automated build and
> tool-identity checks only, and was not used to generate any reported result.

### D.3 Limitations 相应句

- 原：`Windows support and broader usability testing remained outside this evaluation.`
- 新：`A Windows 10/11 x64 build is available but was not used for any reported
  result; cross-platform equivalence and usability testing remained outside
  this evaluation.`

### D.4 Availability 小节同步

`Supported packaged platform:` 改为 `Apple Silicon macOS 13 or later; Windows
10/11 x64 (build verified, not used for reported results).`

### D.5 ⚠️ 需要你确认

正文写 "all 299 project tests passed"。我现在数到 **329 个测试函数**，说明
打包验证之后又加了测试。投稿前需在打包机上重跑 `pytest` 并把数字更新为实测值。

---

## E. 源文件身份验证（审稿意见 T13）

现状：本地原始 FASTQ 未保留在仓库（正文已说明不重复存储公共数据），所以无法回溯
计算 MD5。ENA 的 filereport 服务是提供 `fastq_md5` 字段的。

### E.1 Methods `Source-level agreement metrics` 末尾新增

> ENA's filereport service publishes an MD5 checksum for each submitted FASTQ
> file. Because the public sequencing files were not retained after analysis,
> checksums were not recomputed here, and agreement is reported only at the
> metadata level. Δreads and Rbytes cannot exclude different content of
> identical read count and compressed length. A cryptographic checksum
> comparison should therefore be the primary source-identity metric in future
> releases, with Δreads and Rbytes retained as secondary descriptors.

### E.2 Figure 4D 图注补一句同义限制说明

**可选低成本补数据**：重新下载六个 FASTQ、算 md5、与 ENA `fastq_md5` 比对，
即可把 T13 从"承认局限"升级为"已解决"。取决于文件大小，可能需要数小时下载。

---

## F. 缩写表（审稿意见 T12 剩余项）

在 Keywords 之后、Abstract 之前插入：

| Abbreviation | Definition |
| --- | --- |
| aDNA | ancient DNA |
| API | application programming interface |
| bp | base pairs |
| CI | confidence interval |
| ENA | European Nucleotide Archive |
| GC | guanine–cytosine |
| JSON | JavaScript Object Notation |
| LLM | large language model |
| QC | quality control |
| SOP | standard operating procedure |
| SRA | Sequence Read Archive |

---

## G. 可复现发布（T7）—— 仓库侧已完成

本次已新建：

- `LICENSE` — MIT，并附第三方组件说明
- `THIRD_PARTY_NOTICES.md` — 七个工具 + Java 运行时的许可证、上游、GPL 源码义务；
  macOS 与 Windows 分列（版本确有差异）
- `CITATION.cff` — 已通过 YAML 校验，作者与 DOI 处留 TODO
- `requirements.lock` — 从 `.venv`（Python 3.13.9）抽取的 48 个固定版本；
  已核实 pandas 2.3.3、matplotlib 3.11.0 与正文 Table S6 一致

仍需你操作：

1. `git tag v0.2.0` 并建 GitHub Release
2. Release 接入 Zenodo，取得 DOI
3. 正文 + Table S6 + Availability 中所有 GitHub 链接由 main 分支改为该 tag
4. `.github/workflows/` 增加 macOS/Linux 测试矩阵（T9）

⚠️ 许可证注意：`packaging/windows/licenses/` 目前只有 README，七个工具的许可证
原文要在原生 staging 阶段才复制进去。若 Release 里附带 Windows 安装包，必须确保
安装包内确实含有这些 GPL 许可证原文，否则构成 GPL 违规。

---

## H. 仍需你提供才能完成的占位符

- 作者名单、单位、ORCID、通讯作者邮箱
- 资助来源与各资助方角色
- Authors' contributions（CRediT）
- Acknowledgements
- `LICENSE` 与 `CITATION.cff` 中的版权持有人（当前写的是 "PaleoRigor authors"）
