---
name: financial-data-downloader
description: >
  项目唯一的数据下载 Agent。支持两种模式：
  1. analysis — 为 balanced-finance-analyst / macro-finance-analyst 下载最近 3 个月宏观指标 (17 项)
  2. backtest — 为 Backtest Agent 下载 10 年历史数据 (7 项)
---

# Financial Data Downloader

> [!IMPORTANT]
> 本项目中 **只有此 Agent 被授权执行数据下载**。其它 Agent 不得自行联网下载数据。

---

## 两种下载模式

### 模式一：Analysis（分析数据）

| 项 | 说明 |
|:---|:-----|
| **触发条件** | 上游 Agent 为 `balanced-finance-analyst` 或 `macro-finance-analyst`，**且** `datas/analysis/` 下不存在当天日期文件夹 (`YYYY-MM-DD`) |
| **数据范围** | 最近 3 个月（下载 1 年数据后裁剪至最新 25%） |
| **输出目录** | `datas/analysis/YYYY-MM-DD/` |
| **防重复** | 如目标文件夹已存在，跳过下载（`--force` 可覆盖） |

**支持指标（17 项）：**

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

### 模式二：Backtest（回测数据）

| 项 | 说明 |
|:---|:-----|
| **触发条件** | 上游 Agent 为 `Backtest Agent`，**且** 提示词中明确包含「用最新数据」 |
| **数据范围** | 10 年 |
| **输出目录** | `datas/backtest/` |

**支持标的（7 项）：**

| 输出文件 | 数据源 | 代码 |
|----------|--------|------|
| `QQQ.csv` | Yahoo Finance | QQQ |
| `SHV.csv` | Yahoo Finance | SHV |
| `WRESBAL.csv` | FRED | WRESBAL |
| `WTREGEN.csv` | FRED | WTREGEN |
| `RRPONTSYD.csv` | FRED | RRPONTSYD |
| `BAMLH0A0HYM2.csv` | FRED | BAMLH0A0HYM2 |
| `PCEPI.csv` | FRED | PCEPI |

---

## 快速使用

### 1. 安装依赖

```bash
pip install -r .agent/skills/data-downloader/requirements.txt
```

### 2. 分析数据下载

```bash
# 自动检测当天文件夹是否存在，不存在则下载
python .agent/skills/data-downloader/scripts/download_financial_data.py --mode analysis

# 强制重新下载（即使今天已下载）
python .agent/skills/data-downloader/scripts/download_financial_data.py --mode analysis --force
```

### 3. 回测数据下载

```bash
python .agent/skills/data-downloader/scripts/download_financial_data.py --mode backtest
```

---

## 输出格式

### Analysis 模式

每个指标独立 CSV，保存在 `datas/analysis/YYYY-MM-DD/`：

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
| `QRA_Info.csv` | 最近 QRA 公告链接 |
| `MOVE.csv` | 债市波动率指数时间序列 |
| `COPPER.csv` | 铜期货价格时间序列 |
| `GOLD.csv` | 黄金期货价格时间序列 |
| `COPPER_GOLD_RATIO.csv` | 铜金比时间序列 |
| `Summary.csv` | 所有指标汇总信息 |

### Backtest 模式

每个标的独立 CSV（10 年完整数据），保存在 `datas/backtest/`。

---

## 技术说明

- **FRED 数据**：通过 FRED 公开 CSV API 获取，无需 API Key
- **QRA 公告**：爬取 Treasury.gov 官方页面
- **MOVE / COPPER / GOLD**：通过 Yahoo Finance API (`yfinance`) 获取
- **Analysis 数据范围**：下载最近 1 年数据，保留最新 25%（≈3 个月）
- **Backtest 数据范围**：下载最近 10 年完整数据
