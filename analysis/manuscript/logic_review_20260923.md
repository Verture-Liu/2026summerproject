# 逻辑与结构审查

审查对象：`latest version_PaleoRigor_claims_narrowed.docx`（2026-09-23）
方法：按三层分别检查——论证链条、章节衔接、主张与证据的对应。

---

## 核心诊断

**Results 把同一批 48 次运行拆成了两个小节讲了两遍，导致同一个数字在正文里出现五次。**

`23 of 24` 在全文出现 9 次，其中 Results 内部 5 次（p29、p30、p35、p42、p48）。
`19 of 24` 出现 7 次。`McNemar p = 0.219` 出现 4 次。

关键在于这两个小节：

| 小节 | 报告内容 |
| --- | --- |
| 「A control-layer ablation isolated the contribution of the planning contract」 | 23/24 vs 19/24，16.7 pp，p = 0.219 |
| 「Final held-out evaluation met the prespecified workflow-success threshold」 | 23/24 vs 19/24，16.7 pp，p = 0.219 |

**这是同一个实验。** 消融对照就是 held-out 评测的对照臂，不是另一个实验。但分成两节、各带一个不同的标题、各报一遍完整数字，读者只能理解为两次独立实验——然后发现数字一模一样，于是怀疑自己看错了，或者怀疑作者在重复计数。

导师读出"逻辑有问题"，最可能就是卡在这里。

---

## A. 结构性问题

### A1. 同一实验分两节报告（见上）——严重

**修法**：合并为一节。消融是 held-out 评测的设计要素，应写在同一节的方法说明里，而不是单独成节。合并后 v5 结果在 Results 里只出现一次完整表述。

### A2. Results 以开发史开场，把主结果埋在后面——严重

现在 Results 第一句是：

> Development revealed four recurring problems... PaleoRigor passed 18 of 24 runs in v3 and 18 of 24 in v4 (75.0% in each round), with 12 failures overall.

读者进入 Results 看到的第一个数字是 **75%** 和 **12 次失败**。冻结版的 23/24 要到第三、第四小节才正式出现。

这是**按事情发生的顺序写，而不是按论证的顺序写**。结果就是论文读起来像"我们有很多 bug，后来修好了"，而不是"我们做了一个冻结的 held-out 评测，结果如下"。

**修法**：先报冻结评测的主结果，再用一段说明 v3/v4 是开发阶段、其失败记录保留在案。开发史是**背景**，不是**发现**。

### A3. 案例研究的顺序与论文主题相悖——中等

Case study 1 是肽表去重，论文自己写着：

> The case assessed general data handling rather than biological interpretation.
> without testing peptide biology or ancient-microbiome interpretation.

一篇古微生物组的论文，案例研究第一个是跟古 DNA 毫无关系的肽表，而真正相关的公共测序记录核对排在第二。读者在这里会问"我为什么在读肽段"。

**修法**：把 Case study 2（六个公共测序记录）提到第一位，肽表降为第二或移入补充材料。这同时解决了审稿报告里的 T11。

---

## B. 论证链条问题

### B1. Background 提出的需求，Results 没有回应——严重

Background 结尾（p20）把需求定义为：

> Researchers therefore need a way to **inspect and constrain** a proposed analysis before it runs

但 Results 测的全部是**规划模型是否输出了合规的 JSON 和正确的拒绝码**，没有任何一项测"研究者能不能 inspect"。

在没有用户评估的情况下，这个缺口是结构性的——Background 承诺的是人的能力，Results 交付的是程序的行为。

**修法**：收窄 Background 的承诺。把需求表述为"需要一种机制，使提出的分析在运行前成为**可检视的对象**，并把科学判断保留给专家"——机制是否被人用好，是另一个问题，论文已在 Limitations 声明未测。

### B2. "四类风险"这条主线立了但没贯穿——中等

两处列举措辞不一致：

| 位置 | 表述 |
| --- | --- |
| p11 Key points | ambiguous requests, incorrect source files, undocumented data changes, conclusions unsupported by the available evidence |
| p28 Results | unsuitable requests, incompatible files or references, undocumented transformations, conclusions unsupported by the evidence |

这是论文的组织骨架，两处必须逐字一致。更要紧的是：四类风险提出后，Results 并没有按它组织，读者无法把"这个证据对应哪类风险"对上号。

**修法**：统一措辞，并在 Results 各小节标题或首句显式回指它对应哪类风险。

### B3. Discussion 前三段基本是 Results 的复述——中等

p79 复述 benchmark 数字、p80 复述数据集数字、p81 复述 boundary 数字，每段末尾加一句解读。Discussion 的职责是解释"这意味着什么"，不是再报一遍。

**修法**：删去数字复述，只保留解读。三段可压缩成两段。

---

## C. 表述一致性问题（快速可修）

### C1. 23/24 与 12/12 的关系有歧义——重要

多处这样写：

> v5 passed 23 of 24 runs **and** handled all 12 boundary decisions correctly

读起来像 23 + 12 = 35 次运行。实际上 12 个 boundary 是**包含在** 24 次里的：11/12 supported + 12/12 boundary = 23/24。

只有 p35 写对了：

> PaleoRigor passed 23 of 24 runs: 11 of 12 supported workflows **and** 12 of 12 boundary decisions.

**修法**：p8（摘要）、p13（Key points）、p29、p92 全部改成 p35 的写法，用冒号表示分解关系。

### C2. p49 仍写作 "the control"

> Five runs passed only with PaleoRigor, whereas one passed only with **the control**

上一轮改名漏掉的一处，应为 `the ablated arm`。

### C3. 同一概念多种叫法

| 概念 | 文中出现的说法 |
| --- | --- |
| skill | skill / predefined local analysis module / registered skill / predefined module |
| 对照臂 | ablated arm / ablated control arm / the control |
| 边界测试 | boundary decision / blocked decision / boundary request / boundary run |
| 来源一致性 | source agreement / source-record agreement / record agreement / metadata-level correspondence |

**修法**：每个概念定一个术语，首次出现处定义，之后不再换词。

### C4. Background 过早前向引用

- p18 末尾引 `(Figure 1; Table 4)`——Table 4 是 Methods 里的数据集表
- p19 末尾引 Figure 4、Figure 5——读者此时还不知道这个系统是什么

**修法**：Background 只引 Figure 1。其余前向引用删除或移到 Results。

### C5. 小节标题与内容不符

| 标题 | 实际内容 |
| --- | --- |
| Development failures guided four workflow safeguards | 同时报告了 v5 冻结版结果——那不是 development |
| Prespecified criteria connected workflow checks to retained evidence | 实际在报结果，不是在讲判据 |
| Case study 3: a negative-control test | 文中别处又称 boundary audit；且它不是统计意义上的 negative control |

---

## 建议的 Results 新顺序

| # | 小节 | 内容 |
| --- | --- | --- |
| 1 | 控制层与判据 | Table 1 + Table 2：要防什么、怎么测。先立标准 |
| 2 | 冻结 held-out 评测 | **v5 结果只讲一次**，含消融设计、两个模型、逐场景分解。v3/v4 用一段作为开发背景 |
| 3 | 公共测序记录的来源核对 | 原 Case 2 提前——古微生物相关性最强 |
| 4 | 可追溯的表格变换 | 原 Case 1 降位，或移入补充材料 |
| 5 | 专家限定范围的边界审计 | 原 Case 3 |
| 6 | 打包应用 | 不变 |

改完后 v5 的 23/24 在 Results 里只出现一次，Discussion 里作为解读再提一次，摘要和结论各一次——总共四次，都是有理由的。现在是九次。

---

## 优先级

| 优先级 | 项目 | 工作量 |
| --- | --- | --- |
| 1 | A1 合并重复的两节 | 中 |
| 2 | A2 主结果前置、开发史后置 | 中 |
| 3 | C1 修正 23/24 与 12/12 的歧义 | 小 |
| 4 | B1 收窄 Background 的承诺 | 小 |
| 5 | B2 统一四类风险措辞 | 小 |
| 6 | C2–C5 术语与引用清理 | 小 |
| 7 | A3 案例顺序调整 | 中 |
| 8 | B3 压缩 Discussion 复述 | 中 |

第 3–6 项加起来约半小时，且互不干扰，可以先做。
第 1、2、7 项动结构，建议一次性做完，做完后通读一遍。
