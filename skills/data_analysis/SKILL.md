---
name: data-analysis
description: 本技能提供端到端的数据分析能力。智能体不仅可以通过沙盒安全执行 Python 代码进行数据清洗、统计建模与图表绘制，还能对数据结果进行商业归因与洞察提炼，最终生成包含执行摘要、图表证据、业务建议和可导出文档（Markdown/PDF）的完整分析报告。
---

## 1. 完整分析工作流 (Analysis Workflow)

智能体在接收到分析任务时，**必须**严格遵循以下四个阶段，严禁仅输出孤立的图表或原始数据：

```
[1. 数据探索与清洗] ➔ [2. 深度建模与图表生成] ➔ [3. 归因与洞察提炼] ➔ [4. 完整报告合成与交付]
```

1. **数据探索 (EDA)：** 扫描数据质量、缺失值及分布特征。
2. **深度分析与可视化：** 针对业务问题编写 Python 代码，计算核心指标，生成结构化图表并存入沙盒。
3. **归因与洞察 (Insight Synthesis)：** 结合计算结果回答“发生了什么”、“为什么发生”以及“未来趋势”。
4. **报告交付 (Report Delivery)：** 按统一模板输出结构化 Markdown 报告，必要时将报告编译导出为 HTML/PDF 文件供下载。

---

## 2. 可用工具 (Available Tools)

智能体在执行任务时，可调用以下基于沙盒 SDK 封装的原子工具接口。所有计算与数据变更均在隔离的沙盒实例中进行。

| 工具 API 名称 | 输入参数 | 预期输出结果 | 核心设计意图 & 适用场景 |
| :--- | :--- | :--- | :--- |
| `e2b_upload_dataset` | `file_name` (str)<br>`file_content` (bytes) | 沙盒内的绝对文件路径（如 `/home/user/data.csv`）。 | **数据资产上云：** 在分析前，将本地、数据库或第三方下载的数据集安全上传至沙盒内部存储区。 |
| `e2b_execute_python` | `code` (str) | JSON 对象：包含标准输出（stdout）、标准错误（stderr）以及图表/媒体资产（results/charts）。 | **代码级数据执行：** 在沙盒内运行任意复杂的 Pandas、NumPy、Scikit-learn、Matplotlib 代码块。 |
| `e2b_download_artifact`| `remote_path` (str) | 二进制文件流（bytes）。 | **分析结果导出：** 将沙盒中清洗好的新数据集、训练好的模型权重（`.pkl`）或生成的分析报告（`.md`/`.pdf`）下载至本地。 |
| `e2b_list_workspace` | `dir_path` (str, 可选) | 当前沙盒目录下的文件和文件夹结构列表。 | **沙盒状态审计：** 检查当前分析环境中的文件分布，确认临时生成的数据或图表位置。 |

---

## 3. 核心指令 (Core Commands)

在具体执行层，智能体需要动态生成高质量、无 Bug 的 Python 数据分析脚本，并通过沙盒发送执行。以下为智能体必须掌握的核心代码块与控制指令：

### 3.1 健壮的数据加载与探索 (Exploratory Data Analysis)
```python
import pandas as pd
import json

try:
    df = pd.read_csv('/home/user/dataset.csv', encoding='utf-8')
    info = {
        "shape": df.shape,
        "columns": list(df.columns),
        "missing_ratio": (df.isnull().sum() / len(df)).to_dict(),
        "summary_stats": df.describe(include='all', datetime_is_numeric=True).to_dict()
    }
    print(json.dumps(info, ensure_ascii=False, indent=2, default=str))
except Exception as e:
    print(f"Error loading file: {str(e)}")
```

### 3.2 动态可视化与图表捕获 (Data Visualization)
```python
import matplotlib.pyplot as plt
import seaborn as sns

# 设置支持中文的字体与美化样式
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(10, 6))
sns.lineplot(data=df, x='date', y='revenue', hue='category', ax=ax)
ax.set_title('Revenue Trend Analysis', fontsize=14, pad=15)

# 保存高清图表到沙盒，代码解析器会自动捕获图片资产
chart_path = '/home/user/revenue_trend.png'
plt.savefig(chart_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Chart generated successfully at {chart_path}")
```

### 3.3 自动化报告生成与持久化导出 (Report Builder)
```python
# 将数据分析结论与提炼的洞察直接写成结构化的 Markdown 文件
report_content = """# 数据分析报告：业务增长与异常归因分析

## 1. 执行摘要 (Executive Summary)
* **核心发现：** 本季度总营业额达到 1,250 万元，同比增长 15%，但 8 月份出现明显回落。
* **主要原因：** 供应链延迟导致核心产品 A 缺货 12 天，损失约 80 万元销售额。
* **行动建议：** 建立多供应商备选机制，优化库存预警阈值。

## 2. 数据概况与健康度
* **数据总量：** 50,000 条记录，涵盖 2025-01 至 2025-12。
* **质量评估：** 缺失值占比低于 0.2%，整体数据质量优良。

## 3. 深度分析与图表展示
![收益趋势图](/home/user/revenue_trend.png)

## 4. 关键洞察与业务建议
1. **洞察一：** 产品 B 在华东地区的渗透率最高（占比 42%）。
2. **建议一：** 建议加大华北地区的渠道推广资源投放。
"""

with open('/home/user/final_analysis_report.md', 'w', encoding='utf-8') as f:
    f.write(report_content)

print("Report rendered successfully to /home/user/final_analysis_report.md")
```

### 3.4 自动化沙盒生命周期与清理
```python
from e2b_code_interpreter import CodeInterpreter

sandbox = CodeInterpreter()
# ... 执行数据分析与报告合成工作流 ...
sandbox.close()  # 任务结束必须强制释放或销毁虚拟机，防止算力常驻导致不必要的账单支出
```

---

## 4. 完整报告输出规范 (Report Output Standard)

在完成代码计算与图表绘制后，智能体直接呈献给终端用户的**最终回复**必须包含以下六大核心模块（禁止仅输出“图表已生成”等简短提示）：

### 📋 报告输出格式模板

```markdown
# [报告标题：例如：2025年度销售数据异常归因与增长洞察报告]

## 1. 执行摘要 (Executive Summary)
* **背景与目标：** [简述分析背景与解决的关键问题]
* **核心结论：** [1-2 句精炼的量化结论]
* **关键行动建议：** [最优先建议 1-2 条]

## 2. 数据概况 (Data Overview)
* **数据规模：** [样本量、时间跨度、关键维度]
* **数据质量说明：** [缺失值处理、清洗规则]

## 3. 深度可视化与归因分析 (Key Findings & Visuals)
[嵌入生成的图表，并针对图表进行详细解读]
* **现象描述：** [图表展示的具体数据趋势/分布]
* **归因分析：** [深入解释数据变动背后的业务逻辑与因果关系]

## 4. 统计指标与量化支撑 (Quantitative Evidence)
| 分析维度 | 基期指标 | 现期指标 | 变动幅度 | P值/置信度 |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## 5. 战略建议与风险提示 (Recommendations & Risks)
* **短/中/长期建议：** [可落地的业务举措]
* **风险与局限性：** [数据分析本身的假设条件或局限性]

## 6. 分析产物导出 (Artifact Downloads)
* 📄 [下载 Markdown 格式报告](/home/user/final_analysis_report.md)
* 📊 [下载清洗后的数据集](/home/user/cleaned_dataset.csv)
* 将生成的趋势图和报告文件全部下载保存到本地 "../work_result/" 目录下。
```

---

## 5. 行为守则与安全护栏 (Safety & Strategy Guardrails)

### 5.1 分析质量 Guardrails（严禁裸数据输出）
* **图表必有解读：** 每一张生成的图表下方必须附带**至少一段**深度的业务解读（涵盖趋势变动、异常波动或分布特征）。
* **量化表达优先：** 严禁使用“大幅上升”、“明显下降”等模糊描述，必须使用具体数值与百分比（例如：“环比上升 23.4%”）。
* **报告闭环导出：** 分析完成后，智能体必须在沙盒中将完整报告持久化为 `.md` 或 `.pdf` 文件供用户下载。

### 5.2 代码防御性编程 (Anti-Crash)
* **异常全捕获：** 智能体编写的所有代码，必须严格使用 `try-except` 块包裹。严禁因单行异常导致整个 Python 进程崩塌，错误必须转化为明文日志返回。
* **内存与计算限制：** 沙盒有内存限制。处理超过 500MB 的大数据集时，必须主动使用分块读取（`chunksize`）或转换为 `parquet` 格式，严禁执行高风险 OOM (Out of Memory) 操作。

### 5.3 环境隔离与网络边界
* **数据孤岛原则：** 绝对禁止在代码中尝试通过网络工具（如 `curl`、`wget`、`requests`）向外网扫描或抓取敏感数据，除非受用户显式授权。
* **严禁执行阻塞或交互式指令：** 智能体生成的代码中严禁包含 `input()`、`time.sleep(3600)` 等会导致沙盒线程死锁、无限期挂起的交互式或无限循环命令。