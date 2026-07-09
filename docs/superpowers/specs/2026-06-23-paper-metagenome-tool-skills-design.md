# 论文宏基因组工具调用 Skills 设计

## 范围

第一批覆盖四段高频流程：

1. reads 预处理：fastp、AdapterRemoval、Cutadapt
2. 物种分类：MetaPhlAn、Kraken2、MALT
3. 宏基因组组装：MEGAHIT、metaSPAdes
4. MAG 分析：MetaBAT2、MaxBin2、CONCOCT、DAS Tool、CheckM2、dRep、GTDB-Tk

## 结构

新增一个 `ancient-metagenome-tools` 内置 Skill 包。每个工具保留独立
Skill 名称和参数协议，但复用一个安全的本地命令执行基类。管理层 Router
自动发现该包并可把多个 Skill 串成工作流。

## 安全约束

- 不自动安装软件或数据库。
- 不使用 shell 字符串、通配符或用户提供的任意附加参数。
- 所有命令以参数列表执行。
- 输出仅写入任务工作目录。
- 工具或数据库缺失时返回安装提示。
- 保存 stdout、stderr、命令元数据和工具来源。

## 成功标准

- Router 能发现全部新 Skills。
- 缺失依赖时不会启动子进程。
- 工具存在时生成符合官方 CLI 结构的参数列表。
- 输出缺失或命令失败时返回失败状态。
- 现有 CSV、AMPLiT 和古 DNA Skills 不受影响。
