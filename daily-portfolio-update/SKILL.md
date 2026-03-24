---
name: daily-portfolio-update
description: 一键完成每日投资组合更新全流程：依次更新市场基础数据、获取最新资产价格、生成日度报表。当用户说"每日资产状况更新"、"一键资产状况更新"、"生成今日报告"或"daily asset update"时触发。
---

# 每日投资组合全流程更新

按顺序执行以下三个步骤，每步完成后再进行下一步。如任一步骤失败，停止执行并告知用户。

## 步骤 1：更新市场基础数据

调用 `prepare-market-data` skill，使用默认参数（all，不强制刷新）。

- 若 `assetBasicInfo/stockCN.csv` 和 `assetBasicInfo/fundCN.csv` 以及 `assetBasicInfo/etfCN.csv` 已存在，跳过此步并告知用户
- 若不存在或用户要求强制刷新，则执行更新

## 步骤 2：获取最新资产价格

调用 `fetch-asset-prices` skill，使用默认参数。

- 依赖步骤 1 的输出文件（assetBasicInfo/stockCN.csv、assetBasicInfo/fundCN.csv、assetBasicInfo/etfCN.csv）
- 读取 portfolio.csv，获取每项资产持有状态
- 输出 portfolio_with_prices.csv

## 步骤 3：生成日度报表

调用 `generate-daily-report` skill，使用默认参数。

- 依赖步骤 2 的输出文件（portfolio_with_prices.csv）
- 读取 asset_allocation.csv，分析配置偏离
- 输出 report/daily_report.csv、report/daily_report.txt、report/daily_report.html

## 完成汇总

三步全部完成后，显示：
- ✓ 市场数据状态
- ✓ 价格更新：成功/失败数量
- ✓ 报表路径
- ⚠️ 配置警告（如有）
