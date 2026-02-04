---
name: 国际金融数据下载器
description: 一键下载 18 种国际宏观金融指标的 1 年期 CSV 数据。支持 FRED 系列指标批量下载、财政部 QRA 公告获取，以及 MOVE 指数自动下载。
---

# 国际金融数据下载器 (Financial Data Downloader)

一键下载关键宏观流动性监控指标，输出为多个 CSV 文件。

## 支持的数据指标

| 代码 | 名称 | 频率 | 数据源 |
|------|------|------|--------|
| **WALCL** | 美联储总资产 | 周 | FRED |
| **WTREGEN** | 财政部 TGA 账户 | 周 | FRED |
| **RRPONTSYD** | 隔夜逆回购余额 | 日 | FRED |
| **WRESBAL** | 银行准备金余额 | 周 | FRED |
| **BUSLOANS** | 商业和工业贷款 | 周 | FRED |
| **M2SL** | M2 货币供应量 | 月 | FRED |
| **T10Y2Y** | 10Y-2Y 收益率曲线 | 日 | FRED |
| **DGS2** | 2年期国债收益率 | 日 | FRED |
| **BAMLC0A0CM** | 企业债利差 (OAS) | 日 | FRED |
| **T10YIE** | 10 年期通胀预期 | 日 | FRED |
| **DTWEXBGS** | 美元指数 (DXY广义) | 日 | FRED |
| **DCOILWTICO** | WTI 原油价格 | 日 | FRED |
| **QRA** | 财政部季度再融资公告 | 季 | Treasury.gov |
| **MOVE** | 债市波动率指数 | 日 | Yahoo Finance |
| **COPPER** | 铜期货价格 | 日 | Yahoo Finance |
| **GOLD** | 黄金期货价格 | 日 | Yahoo Finance |
| **COPPER_GOLD_RATIO** | 铜金比 (自动计算) | 日 | Yahoo Finance |

---

## 快速使用

### 1. 安装依赖

```bash
cd /Users/patrick_0000/develop/AIPOC/FinanceAgent/.agent/skills/data-downloader
pip install -r requirements.txt
```

### 2. 运行下载

```bash
python scripts/download_financial_data.py
```

默认输出到 `../macro-finance-analyst/finance-data/` 目录，每个指标保存为独立的 CSV 文件

> [!NOTE]
> 如果目标目录已存在同名文件，脚本将自动替换。

### 3. 自定义输出路径

```bash
python scripts/download_financial_data.py --output /path/to/your/folder
```

---

## 输出格式

每个指标保存为独立的 CSV 文件：

| 文件名 | 内容 |
|--------|------|
| `WALCL.csv` | 美联储总资产时间序列 |
| `WTREGEN.csv` | TGA 账户余额时间序列 |
| `RRPONTSYD.csv` | 逆回购余额时间序列 |
| `WRESBAL.csv` | 银行准备金时间序列 |
| `BUSLOANS.csv` | 商业贷款时间序列 |
| `M2SL.csv` | M2 货币供应量时间序列 |
| `T10Y2Y.csv` | 收益率曲线时间序列 |
| `DGS2.csv` | 2年期国债收益率时间序列 |
| `BAMLC0A0CM.csv` | 企业债利差时间序列 |
| `T10YIE.csv` | 通胀预期时间序列 |
| `DTWEXBGS.csv` | 美元指数 (DXY) 时间序列 |
| `DCOILWTICO.csv` | WTI 原油价格时间序列 |
| `QRA_Info.csv` | 最近 4 个季度 QRA 公告链接 |
| `MOVE.csv` | 债市波动率指数时间序列 |
| `COPPER.csv` | 铜期货价格时间序列 |
| `GOLD.csv` | 黄金期货价格时间序列 |
| `COPPER_GOLD_RATIO.csv` | 铜金比时间序列 (自动计算) |
| `Summary.csv` | 所有指标汇总信息 |

---

## MOVE 指数说明

> [!NOTE]
> MOVE 指数 (ICE BofA MOVE Index) 通过 Yahoo Finance 自动下载，代码为 `^MOVE`。

**数据来源：**
- Yahoo Finance: [https://finance.yahoo.com/quote/%5EMOVE](https://finance.yahoo.com/quote/%5EMOVE)
- 使用 `yfinance` 库自动获取历史数据

---

## 技术说明

- **FRED 数据**：通过 FRED 公开 CSV API 获取，无需 API Key
- **QRA 公告**：爬取 Treasury.gov 官方页面
- **MOVE 指数**：通过 Yahoo Finance API (`yfinance`) 获取，代码 `^MOVE`
- **数据范围**：默认下载最近 1 年（365 天）数据，但是只取25%的最新数据
- **更新频率**：建议每周末运行一次以保持数据最新
