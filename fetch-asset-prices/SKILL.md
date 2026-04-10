---
name: fetch-asset-prices
description: 读取投资组合CSV文件，批量获取资产的最新价格，计算成本、市值、盈亏等指标。当用户说"获取资产价格"、"更新持仓价格"、"计算盈亏"、"查询持仓市值"、"获取我的持仓最新价格"或"fetch prices"时触发。
argument-hint: "[portfolio_file] [output_file]"
---

# 获取资产价格

## 功能说明

本 skill 读取用户的投资组合文件，批量获取每项资产的最新价格，并计算各项财务指标。

### 输入文件

- **portfolio.csv** - 投资组合，包含列：
  - `Code` - 资产代码
  - `Quantity` - 持仓数量（货币基金由用户手动维护，反映份额累计变化）
  - `Cost` - 成本价（货币基金固定为 1.0）
  - `AssetCategory` - 资产类别（股票/基金/货币基金/现金）
  - `AssetType` - 资产类型（如：A股股票、ETF、开放式基金、货币基金等）
  - `TotalInvestment` - 投资本金（仅货币基金填写，其余留空）

### 依赖文件

- **stockCN.csv** - 股票列表（由 prepare-market-data 生成）
- **fundCN.csv** - 基金列表（由 prepare-market-data 生成）
- **api_key.txt** - API license

### 输出文件

- **portfolio_with_prices.csv** - 包含价格和计算结果的投资组合

## 执行步骤

### 1. 环境检查

1. **运行环境**
   - 使用 `uv run ${CLAUDE_SKILL_DIR}/script.py` 执行脚本
   - `uv` 会根据 script.py 头部的 inline metadata 自动创建隔离虚拟环境并安装依赖（pandas、requests、beautifulsoup4），无需手动安装
   - 如未安装 `uv`，提示用户执行 `brew install uv`

2. **检查依赖文件**
   - 检查 `stockCN.csv` 和 `fundCN.csv` 是否存在
   - 如不存在，提示用户先运行 `prepare-market-data`
   - 检查 `api_key.txt` 是否存在

### 2. 读取投资组合

1. **读取投资组合文件**
   - 文件路径：`$0`（默认：`portfolio.csv`）
   - 输出文件路径：`$1`（默认：`portfolio_with_prices.csv`）
   - 如文件不存在，停止执行并提示用户创建该文件
   - 检查必需列：Code, Quantity, Cost, AssetCategory, AssetType
   - `TotalInvestment` 列可选，货币基金行必须有值

2. **数据验证**
   - 确认数据不为空
   - 检查数值列（Quantity, Cost）是否为有效数字
   - 如有错误，停止执行并提示用户检查文件

### 3. 读取基础数据

1. **读取股票列表**（stockCN.csv）
   - 构建 Code → Name 的映射字典
   - 构建 Code → Exchange 的映射字典

2. **读取基金列表**（fundCN.csv）
   - 构建 Code → Name 的映射字典
   - 构建 Code → Exchange 的映射字典

### 4. 批量获取实时价格

1. **读取 API license**
   - 从 `api_key.txt` 读取

2. **遍历投资组合中的每项资产**
   - 根据 AssetCategory 判断调用哪个 API：
     - 股票：`https://api.biyingapi.com/hsstock/real/time/{code}/{license}`
     - 基金：`https://api.biyingapi.com/fd/real/time/{code}/{license}`
     - **现金**：不调用 API，价格固定为成本价（即 1），无需获取行情
     - **货币基金**：不调用 API，`CurrentPrice` 固定为 `1.0`；通过爬虫获取名称和七日年化
   - 提取返回数据中的 `p` 字段（最新价）
   - **货币基金爬虫**：
     - 爬虫 URL：`https://fund.eastmoney.com/{code}.html`
     - 提取字段：基金名称（`Name`）、七日年化收益率（`SevenDayYield`，如 `2.15%`）
     - 若爬取失败，`Name` 标记为 "未知"，`SevenDayYield` 标记为 `—`
   - **API 失败时的备用方案**：
     - 对于普通基金，如果 API 调用失败，自动尝试从天天基金网爬取净值
     - 爬虫 URL：`https://fund.eastmoney.com/{code}.html`
     - 提取单位净值作为价格

3. **控制请求频率**
   - 在批量请求时添加适当延迟（避免超限）
   - API 限制：1分钟300次

### 5. 计算财务指标

对每项资产计算：

- **成本总价** = Quantity × Cost
- **当前市值** = Quantity × 最新价
- **盈亏金额**：
  - 普通资产（股票/基金/现金）：`MarketValue - TotalCost`
  - **货币基金**：`MarketValue - TotalInvestment`（用投资本金替代持仓成本）
- **盈亏百分比**：
  - 普通资产：`(盈亏金额 / TotalCost) × 100%`
  - **货币基金**：`(盈亏金额 / TotalInvestment) × 100%`
- **资产名称** = 从 stockCN.csv 或 fundCN.csv 匹配（现金类固定为"现金"；货币基金从爬虫获取）
- **交易所** = 从 stockCN.csv 或 fundCN.csv 匹配（现金类固定为"—"；货币基金固定为"—"）

### 6. 匹配资产信息

对于每项资产：
1. 根据 AssetCategory 确定从哪个列表查找
2. 根据 Code 匹配资产名称和交易所
3. **货币基金**：名称和七日年化均来自爬虫，不查 stockCN.csv / fundCN.csv
4. 如匹配不到，标记为 "未知"

### 7. 保存结果

1. **输出到 CSV**
   - 文件名：`$1`（默认：`portfolio_with_prices.csv`）
   - 列：
     - Code, Name, Exchange, AssetCategory, AssetType
     - Quantity, Cost, CurrentPrice
     - TotalCost, MarketValue, TotalInvestment, ProfitLoss, ProfitLossPct
     - SevenDayYield（非货币基金行留空）

2. **编码格式**
   - 使用 utf-8-sig 编码（支持 Excel）

### 8. 输出摘要

显示：
- ✓ 成功获取价格的资产数量
- ✗ 获取失败的资产数量
- 总成本、总市值、总盈亏
- 保存路径

### 9. 错误处理

- **API 调用失败**：记录失败资产，继续处理其他资产
- **数据匹配失败**：显示警告，使用默认值
- **文件读写错误**：显示错误信息并停止

---

## 使用示例

```
# 使用默认文件名
用户: 获取我的持仓最新价格

# 指定输入文件
用户: 获取 my_portfolio.csv 的价格

# 查看计算结果
用户: 显示持仓盈亏情况
```

## 输出文件格式示例

| Code | Name | Exchange | AssetCategory | AssetType | Quantity | Cost | CurrentPrice | TotalCost | MarketValue | TotalInvestment | ProfitLoss | ProfitLossPct | SevenDayYield |
|------|------|----------|---------------|-----------|----------|------|--------------|-----------|-------------|-----------------|------------|---------------|---------------|
| 000001 | 平安银行 | SZ | 股票 | 中国股票ETF | 1000 | 15.50 | 16.20 | 15500 | 16200 | | 700 | 4.52% | |
| 163820 | 中银货币 | — | 货币基金 | 货币基金 | 12000 | 1.00 | 1.00 | 12000 | 12000 | 11700 | 300 | 2.56% | 1.85% |
