---
name: pdf-converter
description: 将 Markdown 文件转换为美观的 PDF 文档。支持中文、表格、代码块、GitHub Alert 等复杂格式，提供多种样式模板。
---

# PDF 转换器 (Markdown to PDF Converter)

将 Markdown 文件转换为排版精美的 PDF 文档，支持中文和复杂格式。

## 快速使用

### 1. 安装系统依赖 (首次使用)

```bash
# macOS
brew install cairo pango gdk-pixbuf libffi
```

### 2. 安装 Python 依赖

```bash
cd /Users/patrick_0000/develop/AIPOC/FinanceAgent/.agent/skills/pdf-converter
pip install -r requirements.txt
```

### 3. 转换文件

```bash
# 基本用法
python scripts/convert_to_pdf.py input.md output.pdf

# 使用报告样式
python scripts/convert_to_pdf.py input.md output.pdf --style report

# 转换金融分析报告示例
python scripts/convert_to_pdf.py ../macro-finance-analyst/report/report-20260203-1548.md report.pdf --style report
```

---

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `input` | 输入 Markdown 文件路径 | (必需) |
| `output` | 输出 PDF 文件路径 | (必需) |
| `--style` | 样式模板 (`default` / `report`) | `default` |
| `--paper` | 纸张大小 (`a4` / `letter`) | `a4` |

---

## 支持的 Markdown 特性

| 特性 | 支持状态 |
|------|----------|
| 标题 (h1-h6) | ✅ |
| 粗体/斜体 | ✅ |
| 有序/无序列表 | ✅ |
| 表格 | ✅ |
| 代码块 (语法高亮) | ✅ |
| 引用块 | ✅ |
| GitHub Alert (NOTE/TIP/WARNING/CAUTION) | ✅ |
| 链接 | ✅ |
| 图片 (本地/网络) | ✅ |
| 中文内容 | ✅ |
| Emoji | ✅ |

---

## 样式模板

### default - 默认样式
- 简洁现代的设计
- 适合一般文档

### report - 报告样式
- 专业商务风格
- 适合金融分析报告
- 包含页眉/页脚
- 表格增强样式

---

## 技术说明

- **Markdown 解析**: `markdown` + 多种扩展
- **PDF 渲染**: `WeasyPrint` (基于 Cairo)
- **代码高亮**: `Pygments`
- **中文支持**: 使用系统中文字体 (苹方/思源黑体)
