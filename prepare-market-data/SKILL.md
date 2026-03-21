---
name: prepare-market-data
description: 获取并缓存A股股票列表和基金列表（ETF/开放式基金）的基础信息。首次使用或每日更新时调用。
trigger: "更新基础数据" | "获取股票列表" | "获取基金列表" | "更新市场数据" | "prepare market"
arguments:
  data_types:
    description: "需要更新的数据类型：stocks（股票）、funds（基金）、all（全部，默认）"
    required: false
  force_refresh:
    description: "是否强制刷新缓存（默认：false，如有缓存则跳过）"
    required: false
---

# 基础数据准备

## 功能说明

本 skill 会从 API 获取最新的股票和基金列表，并缓存到本地 CSV 文件中供后续使用。

### 数据文件

- **stockCN.csv** - A股股票列表（Code, Name, Exchange）
- **fundCN.csv** - 基金列表（Code, Name, Exchange）

## 执行步骤

### 1. 环境检查

1. **检查 Python 环境**
   - 确认系统已安装 Python 3.x
   - 检查必要的库：pandas, requests
   - 如缺少库，提示用户安装：`pip install pandas requests`

2. **读取 API License**
   - 检查当前工作目录下是否存在 `api_key.txt` 文件
   - 如不存在，停止执行并提示用户创建该文件，填入 API license
   - 读取 license 内容，去除首尾空白字符

### 2. 数据获取

根据 `data_types` 参数决定获取哪些数据：

#### 获取股票列表（如果 data_types 为 stocks 或 all）

1. **检查缓存**
   - 判断 `stockCN.csv` 是否存在
   - 如果存在且 `force_refresh=false`，跳过获取

2. **调用 API**
   - API: `https://api.biyingapi.com/hslt/list/{license}`
   - 方法: GET

3. **解析响应**
   - 解析返回的 JSON 数据
   - 提取字段：`dm` → Code, `mc` → Name, `jys` → Exchange
   - 转换交易所代码：sh → SH, sz → SZ

4. **保存到 CSV**
   - 文件名：`stockCN.csv`
   - 列名：Code, Name, Exchange
   - 编码：utf-8-sig（支持 Excel 打开）

5. **输出日志**
   - 显示获取的股票数量
   - 显示保存路径

#### 获取基金列表（如果 data_types 为 funds 或 all）

1. **检查缓存**
   - 判断 `fundCN.csv` 是否存在
   - 如果存在且 `force_refresh=false`，跳过获取

2. **调用 API**
   - ETF列表 API: `https://api.biyingapi.com/fd/list/etf/{license}`
   - 开放式基金 API: `https://api.biyingapi.com/fd/list/all/{license}`
   - 方法: GET

3. **解析响应**
   - 合并两个 API 的返回结果
   - 提取字段：`dm` → Code, `mc` → Name, `jys` → Exchange
   - 转换交易所代码：sh → SH, sz → SZ

4. **保存到 CSV**
   - 文件名：`fundCN.csv`
   - 列名：Code, Name, Exchange
   - 编码：utf-8-sig（支持 Excel 打开）

5. **输出日志**
   - 显示获取的基金数量
   - 显示保存路径

### 3. 错误处理

- **API 调用失败**：显示错误信息，提示检查网络和 license
- **数据格式错误**：显示返回内容，提示联系 API 提供商
- **文件写入失败**：检查目录权限

### 4. 完成提示

显示执行摘要：
- ✓ 股票列表：stockCN.csv（XXX 条记录）
- ✓ 基金列表：fundCN.csv（XXX 条记录）
- 提示：这些文件已缓存，后续 skills 会自动使用

---

## 使用示例

```
# 更新所有数据
用户: 更新基础数据

# 只更新股票列表
用户: 只更新股票列表

# 强制刷新
用户: 强制更新市场数据

# 检查现有数据
用户: 检查基础数据是否最新
```
