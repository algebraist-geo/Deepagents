---
name:Tavily-Search
description:本技能模块专为智能体（Agent）接入全网主流电商平台（淘宝、京东、拼多多）及品牌官网、评测网站而设计。本技能放弃了传统的脆弱爬虫架构，全面采用专门为大语言模型优化的 **Tavily Search API** 作为核心检索工具。它赋予智能体跨平台进行商品精准比价、参数提炼、优惠活动搜集以及多源口碑聚合的能力，为用户提供高效、合规、全网级的消费决策支持。---
---
## 2. 可用工具 (Available Tools)

智能体在执行任务时，可调用以下基于 Tavily Search 封装的原子工具接口。

| 工具 API 名称 | 输入参数 | 预期输出结果 | 核心设计意图 & 适用场景 |
| :--- | :--- | :--- | :--- |
| `tavily_product_query` | `keyword` (str)<br>`platform_filters` (list, 可选) | 结构化的全网商品卡片列表：包含商品名、各平台实时报价、来源链接、摘要信息。 | **跨平台精准比价：** 针对特定商品（如“iPhone 16 Pro 256G”），一键搜集淘宝、京东、拼多多的公开价格并进行横向对比。 |
| `tavily_extract_details` | `url` (str) | 从目标网页中抽取的商品核心技术参数、官方原价、上市时间及关键规格。 | **长尾网站/官网参数提取：** 针对品牌官网或垂直电商页面，利用 Tavily 的高清洁度文本返回，直接提炼商品元数据。 |
| `tavily_promotion_search` | `product_name` (str) | 当前有效的全网满减政策、平台百亿补贴动态、限时优待券及全网历史低价线索。 | **全网优惠全景透视：** 输入商品名称，在全网范围内搜索最新的优惠券、折扣券及大促活动组合方案。 |
| `tavily_review_synthesis` | `product_name` (str) | 综合知乎、什么值得买、各大电商评价等多源数据的 AI 情感倾向报告（核心优缺点汇总）。 | **全网口碑去水聚合：** 绕过单一平台的刷单评价，整合全网评测与真实用户反馈，提取商品优缺点共识。 |

---

## 3. 核心指令 (Core Commands)

在具体执行层，智能体通过向 Tavily API 发送经过提示词工程优化的结构化 Payload，实现高精度的商品数据打捞：

### 3.1 高级跨平台检索指令 (Advanced Querying)
*   **指令示例：**
    ```json
    {
      "query": "site:jd.com OR site:taobao.com OR site:pinduoduo.com '索尼WH-1000XM5' 价格 补贴",
      "search_depth": "advanced",
      "include_answer": true,
      "max_results": 5
    }
    ```
    *   **作用：** 利用 Tavily 的 `advanced` 深度搜索模式，配合 `site:` 语法限制，强制在三大主流电商的公开索引中定向打捞实时报价，并开启 `include_answer` 获取即时的全网价格归纳。

### 3.2 深度内容提取与去噪指令 (Extraction & Content Delivery)
*   **指令示例：**
    ```json
    {
      "url": "[https://www.apple.com.cn/macbook-pro/](https://www.apple.com.cn/macbook-pro/)",
      "include_raw_content": false,
      "extract_depth": "basic"
    }
    ```
    *   **作用：** 针对品牌官网，利用 Tavily 直接将混乱的 HTML 转化为大模型极易读取的纯文本/Markdown 结构。智能体无需维护任何 XPath 或 CSS 选择器，极大提升了对“新官网”或“未知网站”的适配弹性。

---

## 4. 行为守则与多平台适配护栏 (Safety & Strategy Guardrails)

### 4.1 搜索词优化准则 (Query Optimization)
*   **防止泛搜索：** 智能体在调用 Tavily 之前，必须对用户输入的模糊词进行结构化重构。例如：用户输入“买个便宜的空气炸锅”，智能体应将其重构为 `"空气炸锅 价格 对比 百亿补贴 推荐 site:smzdm.com OR site:jd.com"`，以确保 Tavily 返回的结果聚焦于价格和选购攻略。
*   **时效性控制：** 鉴于电商价格波动剧烈，智能体在使用 Tavily 检索时，应在 Query 中主动附带当前的年份与月份（例如：“2026年7月 京东 预售价格”），防止抓取到过期或历史大促的失效信息。

### 4.2 数据边界与反爬解脱
*   **合规遵从：** Tavily Search 仅能检索互联网上**已公开建立索引**的页面。智能体必须明确这一技术边界：无法通过本工具进入任何需要“登录后可见”的私有购物车、加密个人订单列表或需验证码的实时结算支付网关。