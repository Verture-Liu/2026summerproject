# 两个版本的差异

两份稿件**除定位表述外完全相同**：结构、数据、图表、参考文献、Limitations 全部一致，
共 223 段，只有 6 段不同。

| | VARIANT-A | VARIANT-B |
| --- | --- | --- |
| 题目 | expert-guided workflows for traceable **paleomicrobiome data processing** | expert-gated, auditable data preparation **upstream of ancient metagenomic profiling** |
| 自我定位 | 一个处理古微生物组数据的工具 | 已有分析流程之前的一道控制层 |

## 六处差异

**1. 题目**

- A：PaleoRigor: expert-guided workflows for traceable paleomicrobiome data processing
- B：PaleoRigor: expert-gated, auditable data preparation upstream of ancient metagenomic profiling

**2. 摘要 Background**

- A：古生物学家需要易用的工具来检查文件选择和处理决策。
- B：已有流程在操作者选定输入文件和分析方法之后才开始；它们不检查那个选择，不记录启动前发生过的改动，也不限制从 QC 输出能得出什么结论。这些前分析决策正是错误变得不可挽回的地方。

**3. 摘要 Conclusions**

- A：PaleoRigor 支持专家解释之前的工作流审查与可追溯的数据处理。
- B：PaleoRigor 占据的是分析之前那一步。它产出经核验的输入、一份变换记录、以及一份关于"现有证据不支持什么"的明确声明，供已有的古宏基因组流程使用。

**4. Background 结尾**

- A：缺的是一种机制，能在运行前明确陈述所提分析并约束其行为。
- B：缺的是一道**跑在这些流程之前**的层：陈述分析、约束行为、记录改动，并把生物学结论的责任留给研究者。

**5. Background 中 PaleoRigor 的介绍段**

- A：无额外说明。
- B：增加一句——PaleoRigor 不是分析流程，也不取代分析流程：它的产出正是 aMeta 或 nf-core/eager 随后要消费的、经核验的输入、变换记录和审计轨迹。

**6. Discussion**

- A：源文件与工作流审查可以先于接头去除、损伤分析、去宿主、分类鉴定等步骤。
- B：同上，并补充"无论这些步骤是手工执行还是通过已有流程执行"。

## 判断这件事的两个问题

**一，证据支持哪一个？**

论文报告的分析步骤（文件类型识别、配对检查、FastQC/MultiQC/SeqKit、与 ENA/SRA 元数据比对、
表格清洗）没有一项是古 DNA 特有的。真正体现领域知识的是那四条拒绝规则——QC 不能证明真实性、
损伤分析需要比对数据和明确参考等。两个版本都保留了这部分内容。

差别在于：A 的题目暗示方法本身是古微生物组专用的；B 把领域特异性明确限定在
"分析之前这一段"和拒绝规则上。

**二，审稿人会怎么读？**

已有的中文多视角审稿报告中，Cc.2（古微生物学特异验证不足）与 Cc.5（主张范围强于当前证据）
指向的都是这个问题。B 通过收窄适用范围回应了它们；A 保留原范围，则需要靠补实验来支撑。
