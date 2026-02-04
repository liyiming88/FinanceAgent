---
description: 获取当日美国金融市场新闻并保存为 Markdown
---

# 获取当日金融新闻 (Fetch Daily News)

自动搜索并整合当日美国金融市场新闻，按信息源分层输出 Markdown 文件。

## 执行步骤

### 1. 搜索第一层来源（投行机构）

使用 `search_web` 工具，依次搜索以下投行的当日市场观点：

```
搜索词示例：
- "Goldman Sachs market outlook today"
- "Morgan Stanley research note today"
- "J.P. Morgan market view today"
- "Bank of America market commentary"
```

// turbo-all

### 2. 搜索第二层来源（财经媒体）

使用 `search_web` 工具，搜索财经媒体的当日重要报道：

```
搜索词示例：
- "site:cnbc.com markets today"
- "site:bloomberg.com markets today" 
- "site:reuters.com us markets today"
- "site:wsj.com markets today"
```

### 3. 整合并去重

- 按重要性和时效性排序新闻
- 去除重复报道
- 提取各新闻的核心观点

### 4. 生成 Markdown 文件

将整合后的新闻保存到 `macro-finance-analyst/daily-news/YYYY-MM-DD.md`，使用以下模板：

```markdown
# 美国金融市场每日新闻 - [日期]

## 📊 今日要点摘要
- [要点 1]
- [要点 2]
- [要点 3]

---

## 🏦 第一层：投行机构观点

### Goldman Sachs
- [新闻标题](URL)
  > 核心观点摘要

### Morgan Stanley
- [新闻标题](URL)
  > 核心观点摘要

### J.P. Morgan
- [新闻标题](URL)
  > 核心观点摘要

---

## 📰 第二层：财经媒体报道

### Bloomberg
- [新闻标题](URL)
  > 要点摘要

### CNBC
- [新闻标题](URL)
  > 要点摘要

### Reuters
- [新闻标题](URL)
  > 要点摘要

---

## ⚠️ 风险提示
[当日重大风险事件或预警信息]

---

*更新时间: [时间戳] (UTC+8)*
```

## 输出位置

文件保存路径：
- 目录：`/Users/patrick_0000/develop/AIPOC/FinanceAgent/.agent/skills/macro-finance-analyst/daily-news/`
- 文件名：`YYYY-MM-DD.md`（如 `2026-02-03.md`）

## 注意事项

1. **时效性**：优先搜索当日新闻，如无当日内容可扩展到24小时内
2. **来源可靠性**：投行观点优先级高于媒体报道
3. **链接有效性**：确保所有链接可访问
4. **中英文混合**：标题可保留英文原文，摘要可用中文总结
