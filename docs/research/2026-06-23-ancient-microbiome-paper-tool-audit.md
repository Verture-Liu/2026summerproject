# 古微生物组论文工具与 Skill 审查

日期：2026-06-23

## 文件核对

用户提供了 8 个 PDF 文件，其中包含 6 篇独立论文：

- `PIIS0092867424008997.pdf` 与 `PIIS0092867424008997-2.pdf` 完全相同。
- `s41586-021-03532-0.pdf` 与 `s41586-021-03532-0-2.pdf` 完全相同。

## 六篇论文的主要计算工具

### 1. Bronze Age cheese reveals human-Lactobacillus interactions over evolutionary history

主要工具：

- FastQC：测序质量检查
- leeHom：接头去除与双端 reads 合并
- MALTn、MEGAN：分类比对与结果查看
- BWA、SAMtools：参考序列比对和覆盖统计
- MITObim、MIRA：迭代组装
- mapDamage：古 DNA 损伤评估
- CheckM：重建基因组质量检查
- RAST：基因组功能注释
- JSpecies、BLAST+、MUMmer：ANI 与基因组比较
- BPGA：泛基因组分析
- PhyloPhlAn、RAxML、Geneious：系统发育

### 2. Natural products from reconstructed bacterial genomes of the Middle and Upper Paleolithic

主要工具：

- MEGAHIT、metaSPAdes：古代宏基因组组装
- FreeBayes：修正损伤相关组装错误
- PyDamage：判断 MAG 是否具有古 DNA 损伤
- MetaWRAP：宏基因组分箱与 MAG refinement
- CheckM、GUNC：MAG 完整度、污染和嵌合检查
- GTDB：MAG 分类
- antiSMASH：生物合成基因簇识别
- BiG-SCAPE：BGC 相似性网络和家族聚类
- CRAGE：异源表达实验系统

论文分析代码：
https://github.com/paleobiotechnology/EMN001_Paleofuran

### 3. Reconstruction of ancient microbial genomes from the human gut

主要工具：

- AdapterRemoval、Cutadapt：接头和短 reads 去除
- KneadData、Bowtie2：人源 DNA 去除
- MetaPhlAn2、SourceTracker2、CoproID、Kraken2：分类、来源和宿主判断
- MEGAHIT：宏基因组组装
- Bowtie2、SAMtools：reads 回贴
- MetaBAT2：分箱
- CheckM：MAG 质控
- dRep、MUMmer、Mash、FastANI：去冗余与 ANI
- GTDB-Tk：分类
- mapDamage、DamageProfiler：古 DNA 损伤
- Prokka、hmmsearch、dbCAN：功能与 CAZyme 注释
- IQ-TREE、PhyloPhlAn、Roary、RAxML、BEAST2：系统发育与分子钟

论文分析代码：
https://github.com/kosticlab/ancient-microbiome-denovo

### 4. Identification of antimicrobial peptides from ancient gut microbiomes

主要工具：

- KneadData：人源 DNA 去除
- SPAdes meta 模式：宏基因组组装
- ORF_hunter.py：短 ORF 与肽序列提取
- AMPLiT：AMP 预测
- Propy3、Word2Vec：肽特征
- 细胞毒性预测工具：候选过滤
- AlphaFold3：候选 AMP 结构预测

AMPLiT：
https://github.com/ChenSizhe13893461199/AMPLiT

### 5. A 5700 year-old human genome and oral microbiome from chewed birch pitch

主要工具：

- PALEOMIX、AdapterRemoval、BWA：古 DNA 预处理与比对
- mapDamage、Schmutzi、HaploGrep：损伤、污染和线粒体分析
- ADMIXTOOLS：D/f 统计
- MetaPhlAn2、MALT、MEGAN6：微生物分类
- SeqKit：序列去重
- SAMtools、BEDTools、Circos：覆盖度分析与展示
- MEGAHIT、BLASTn：组装和毒力基因搜索
- Holi：古环境 DNA 分类

### 6. The Iceman's microbiome

主要工具：

- USEARCH、VSEARCH：扩增子合并、过滤、去冗余和 ASV
- MAFFT、TrimAl、IQ-TREE：序列比对与系统发育
- fastp：接头和低质量序列清理
- SPAdes、MEGAHIT、metaSPAdes：组装
- MetaBAT2、MaxBin2、CONCOCT、DAS Tool：多工具分箱
- BUSCO、FGMP、CheckM2：基因组质量检查
- dRep、Kraken2、GTDB-Tk、PhyloPhlAn：去冗余与分类
- CoverM、Bowtie2、SAMtools：丰度和覆盖度
- DamageProfiler、PMDtools：古 DNA 损伤
- Prokka、funannotate、eggNOG-mapper、OrthoFinder：功能和直系同源注释
- MetaPhlAn4、StrainPhlAn：物种和菌株级分析

## 现有本地 Skills 覆盖

已经具备：

- `sample_sheet_prepare`
- `fastq_qc`
- `host_dna_removal`
- `ancient_dna_authentication`
- `amp_prediction`
- 肽序列 CSV 八项处理 Skills

## GitHub Agent Skill 搜索结果

发现并已保留在隔离区：

- `ubcd-ibfg/fastq-qc-skill`

未找到可信、可直接接入的以下工具专用 Agent Skills：

- MetaPhlAn、Kraken2、MALT/MEGAN
- MEGAHIT、metaSPAdes
- MetaBAT2、MaxBin2、CONCOCT、DAS Tool
- CheckM/CheckM2、dRep、GTDB-Tk
- DamageProfiler、PyDamage、PMDtools
- Prokka、eggNOG-mapper
- antiSMASH、BiG-SCAPE
- BLAST、MAFFT、IQ-TREE、PhyloPhlAn

`mcap91/bioinfo-agent-toolkit` 是通用 Skill 目录和编排框架，没有上述论文工具的可执行 Skills。
`nebulia37/BioinfoClaw` 当前只有 README。
`Jack123-Wang/AI_Bioinformatic` 仅包含 GEO 搜索和单细胞注释 Skills。

## 建议新增的本地 Skill 包

按论文复用频率和当前研究路线排序：

1. `ancient-read-preprocessing`
   - AdapterRemoval / Cutadapt / fastp

2. `metagenome-taxonomy`
   - MetaPhlAn4 / Kraken2 / MALT

3. `metagenome-assembly`
   - MEGAHIT / metaSPAdes

4. `mag-reconstruction`
   - MetaBAT2 / MaxBin2 / CONCOCT / DAS Tool
   - CheckM2 / dRep / GTDB-Tk

5. `ancient-dna-authentication-extended`
   - DamageProfiler / PyDamage / PMDtools

6. `microbial-genome-annotation`
   - Prokka / eggNOG-mapper

7. `natural-product-mining`
   - antiSMASH / BiG-SCAPE

8. `comparative-genomics`
   - BLAST / MAFFT / IQ-TREE / PhyloPhlAn

每个包继续遵守当前规则：只检查本地环境、只调用已安装工具、缺失时给安装说明、不自动安装。
