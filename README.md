# 投资组合管理 Skills

这是一套用于管理个人投资组合的 Claude Code Skills，支持股票、基金等资产的价格查询、盈亏计算和资产配置分析。

## 📦 包含的 Skills

### 1. prepare-market-data（基础数据准备）
获取并缓存A股股票列表和基金列表的基础信息。

**触发方式：**
- "更新基础数据"
- "获取股票列表"
- "获取基金列表"

**功能：**
- 获取 A 股股票列表 → `stockCN.csv`
- 获取基金列表（ETF + 开放式基金）→ `fundCN.csv`
- 缓存到本地，避免重复请求

---

### 2. fetch-asset-prices（获取资产价格）
读取投资组合CSV文件，批量获取资产的最新价格，并计算财务指标。

**触发方式：**
- "获取资产价格"
- "更新持仓价格"
- "计算盈亏"

**功能：**
- 读取 `portfolio.csv`
- 批量获取实时价格
- 计算成本总价、市值、盈亏金额、盈亏百分比
- 输出 → `portfolio_with_prices.csv`

---

### 3. generate-daily-report（生成日度报表）
根据持仓数据和资产配置目标，生成完整的日度投资报表。

**触发方式：**
- "生成资产报表"
- "生成日报"
- "投资组合分析"

**功能：**
- 读取带价格的投资组合
- 计算资产配置比例
- 检查配置偏离度，生成警告
- 输出 → `daily_report.csv` 和 `daily_report.txt`

---

## 🚀 快速开始

### 步骤 1：准备配置文件

1. **API License**
   ```bash
   cp examples/api_key.txt.example api_key.txt
   # 编辑 api_key.txt，填入您的 API License
   ```

2. **投资组合**（如果您还没有）
   ```bash
   cp examples/portfolio.csv.example portfolio.csv
   # 编辑 portfolio.csv，填入您的持仓信息
   ```

3. **资产配置**（如果您还没有）
   ```bash
   cp examples/asset_allocation.csv.example asset_allocation.csv
   # 编辑 asset_allocation.csv，设置您的资产配置目标
   ```

### 步骤 2：首次使用

```bash
# 1. 更新基础数据（首次必须）
用户: 更新基础数据

# 2. 获取资产价格
用户: 获取我的持仓最新价格

# 3. 生成报表
用户: 生成今天的投资报表
```

### 步骤 3：日常使用

```bash
# 一键生成报表（会自动执行必要的步骤）
用户: 生成今天的投资报表
```

---

## 📁 项目结构

```text
bafangceSkills/
├── prepare-market-data/           # Skill 1: 基础数据准备
│   ├── SKILL.md                   # Skill 定义文件
│   └── script.py                  # 实现脚本
│
├── fetch-asset-prices/            # Skill 2: 获取资产价格
│   ├── SKILL.md
│   └── script.py
│
├── generate-daily-report/         # Skill 3: 生成日度报表
│   ├── SKILL.md
│   └── script.py
│
├── examples/                      # 配置文件模板
│   ├── api_key.txt.example
│   ├── portfolio.csv.example
│   └── asset_allocation.csv.example
│
└── README.md
```

### 输入文件（用户维护）

| 文件名 | 说明 | 必需 |
|--------|------|------|
| `api_key.txt` | API License | ✓ |
| `portfolio.csv` | 投资组合 | ✓ |
| `asset_allocation.csv` | 资产配置目标 | ✓ |

### 缓存文件（自动生成）

| 文件名 | 说明 | 生成方式 |
|--------|------|----------|
| `stockCN.csv` | 股票列表 | prepare-market-data |
| `fundCN.csv` | 基金列表 | prepare-market-data |
| `portfolio_with_prices.csv` | 带价格的投资组合 | fetch-asset-prices |

### 输出文件（自动生成）

| 文件名 | 说明 | 生成方式 |
|--------|------|----------|
| `daily_report.csv` | CSV 格式报表 | generate-daily-report |
| `daily_report.txt` | 文本格式报表 | generate-daily-report |

---

## 📋 配置文件格式

### portfolio.csv（投资组合）

```csv
Code,Quantity,Cost,AssetCategory,AssetType
000001.SZ,1000,15.50,股票,股票
159001.SZ,5000,2.80,基金,ETF
```

**字段说明：**
- `Code` - 资产代码（带交易所后缀，如 .SZ、.SH）
- `Quantity` - 持仓数量
- `Cost` - 成本价
- `AssetCategory` - 资产类别（股票/基金）
- `AssetType` - 资产类型（用于配置分析，如：股票、ETF、开放式基金等）

### asset_allocation.csv（资产配置）

```csv
AssetType,Allocation,Bias
股票,60,5
ETF,30,5
开放式基金,10,3
```

**字段说明：**
- `AssetType` - 资产类型（需与 portfolio.csv 中的 AssetType 对应）
- `Allocation` - 目标配置比例（百分比）
- `Bias` - 允许偏离范围（百分比）

---

## 🔄 工作流程

```
┌─────────────────────────────────────────────────────┐
│  用户：生成今天的投资报表                              │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  Skill 1: prepare-market-data                        │
│  - 检查 stockCN.csv、fundCN.csv                      │
│  - 如不存在，从 API 获取并缓存                         │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  Skill 2: fetch-asset-prices                         │
│  - 读取 portfolio.csv                                │
│  - 批量获取实时价格                                   │
│  - 计算财务指标                                        │
│  - 输出 portfolio_with_prices.csv                    │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  Skill 3: generate-daily-report                      │
│  - 读取 portfolio_with_prices.csv                    │
│  - 读取 asset_allocation.csv                         │
│  - 计算配置比例和偏离度                               │
│  - 生成 daily_report.csv 和 daily_report.txt          │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ 依赖要求

- Python 3.x
- pandas
- requests

安装依赖：
```bash
pip install pandas requests
```

---

## 📊 报表示例

### CSV 报表

包含详细的资产明细、配置分析和汇总信息，可用 Excel 打开。

### 文本报表

```
========================================
  投资组合日度报表
  日期：2026-03-19
========================================

📊 资产明细
----------------------------------------
000001.SZ   平安银行        股票    1000  15.50  16.20   16,200   +700    +4.52%
159001     货币ETF易方达   ETF     5000   2.80   2.85   14,250   +250    +1.79%

📈 配置分析
----------------------------------------
资产类型     实际比例   目标比例   偏离度   状态
股票         65.0%      60.0%      5.0%     ✓
ETF          30.0%      30.0%      0.0%     ✓
开放式基金   5.0%       10.0%      5.0%     ⚠️ 超出偏差

📋 汇总信息
----------------------------------------
总成本：     ¥155,000.00
总市值：     ¥162,450.00
总盈亏：     +¥7,450.00 (+4.81%)

⚠️ 配置警告
----------------------------------------
• 开放式基金配置比例 5.0%，低于目标 10.0%，超出偏差范围 3.0%
```

---

## ⚠️ 注意事项

1. **API 频率限制**：1 分钟 300 次请求（免费版）
2. **数据更新时间**：
   - 股票/基金列表：每日 16:20 更新
   - 实时价格：盘中实时更新
3. **文件编码**：所有 CSV 文件使用 UTF-8-BOM 编码，兼容 Excel
4. **建议**：交易日收盘后运行，获取当日收盘价

---

## 📝 许可证

本项目仅供个人学习使用。

API 服务来自：必盈 API（https://api.biyingapi.com/）

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
