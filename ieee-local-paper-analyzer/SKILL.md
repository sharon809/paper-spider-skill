---
name: ieee-local-paper-analyzer
description: 在本地主机网络环境中抓取 IEEE 论文与 metadata（题目、作者、摘要、DOI、年份、关键词、PDF 链接），并对论文集合进行快速阅读式总结与主题分析。适用于有本地 IP 学术数据库访问权限的场景。
---

# IEEE 本地论文抓取与分析 Skill

## 何时使用
当用户需要：
- 在**本地主机**（拥有学术数据库访问权限的 IP）抓取 IEEE 论文数据。
- 批量收集 metadata（title/authors/abstract/year/doi/keywords/pdf url）。
- 对抓取结果做“快速阅读”与汇总分析（主题、趋势、高频术语、代表论文）。

## 工作流
1. **先检索再抓取细节**：优先用 `ieeexplore rest/search` 返回结构化结果。
2. **按需补全详情**：若需要更完整信息，再访问文章页解析补充字段。
3. **落盘为 JSONL/CSV**：便于后续筛选与分析。
4. **分析输出 markdown 报告**：包含主题、时间分布、关键词与代表论文。

## 快速开始
在仓库根目录运行：

```bash
python3 ieee-local-paper-analyzer/scripts/crawl_ieee.py \
  --query "graph neural network" \
  --max-records 100 \
  --out data/ieee_gnn.jsonl

python3 ieee-local-paper-analyzer/scripts/analyze_papers.py \
  --input data/ieee_gnn.jsonl \
  --top-k 12 \
  --report-out data/ieee_gnn_report.md
```

## 参数建议
- 抓取阶段：
  - `--start-year` / `--end-year`：缩小范围，降低被限流概率。
  - `--sleep-sec`：请求间隔建议 `0.5~1.5`。
  - `--max-records`：先小批量验证（20~50）再放大。
- 分析阶段：
  - `--top-k`：10~20 通常足够。
  - `--min-year`：仅分析近年趋势时启用。

## 本地运行要点
- 必须在有数据库访问权限的本机网络中运行（公司/校园网或 VPN）。
- 遇到 429/403：
  1) 增大 `--sleep-sec`；
  2) 缩小检索窗口（关键词、年份）；
  3) 分批抓取并合并。

## 输出字段约定
脚本输出 JSONL 默认字段：
- `query`, `title`, `authors`, `publication_title`, `year`, `doi`
- `abstract`, `keywords`, `document_url`, `pdf_url`
- `publisher`, `content_type`, `source`

## 质量检查清单
抓取完成后，至少做以下检查：
1. 样本数是否满足预期（>= 目标数量的 90%）。
2. `title`、`year`、`doi` 非空率是否可接受。
3. 重复标题比例是否过高（>15% 需复查 query 或去重逻辑）。
4. 报告中的主题是否与 query 语义一致。

## 使用脚本
- 抓取：`scripts/crawl_ieee.py`
- 分析：`scripts/analyze_papers.py`

