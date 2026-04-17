#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
# ]
# ///
"""
资产再平衡计划生成器

读取 portfolio_with_prices.csv 和 asset_allocation.csv，
根据用户给出的目标总市值，计算每种资产类型的调仓金额，
生成 re_balance.md 调仓计划文件。
"""

import sys
import os
from datetime import datetime
import pandas as pd


def load_portfolio(portfolio_file: str) -> pd.DataFrame:
    df = pd.read_csv(portfolio_file, encoding="utf-8-sig")
    required_cols = {"Code", "Name", "AssetType", "MarketValue"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"❌ 错误：{portfolio_file} 缺少必需列：{', '.join(missing)}")
        sys.exit(1)
    df["MarketValue"] = pd.to_numeric(df["MarketValue"], errors="coerce").fillna(0)
    return df


def load_allocation(allocation_file: str) -> pd.DataFrame:
    df = pd.read_csv(allocation_file, encoding="utf-8-sig")
    required_cols = {"AssetType", "Allocation", "Bias"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"❌ 错误：{allocation_file} 缺少必需列：{', '.join(missing)}")
        sys.exit(1)
    df["Allocation"] = pd.to_numeric(df["Allocation"], errors="coerce").fillna(0)
    df["Bias"] = pd.to_numeric(df["Bias"], errors="coerce").fillna(0)
    return df


def fmt_money(value: float) -> str:
    """格式化金额，保留2位小数，加千分位"""
    sign = "+" if value > 0 else ""
    return f"{sign}¥{value:,.2f}"


def fmt_money_abs(value: float) -> str:
    return f"¥{value:,.2f}"


def fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


def generate_rebalance_plan(
    target_total: float,
    portfolio_file: str,
    allocation_file: str,
    output_file: str,
) -> None:
    # 读取数据
    portfolio = load_portfolio(portfolio_file)
    allocation = load_allocation(allocation_file)

    # 当前总市值
    current_total = portfolio["MarketValue"].sum()

    # 按 AssetType 分组求当前市值
    current_by_type = portfolio.groupby("AssetType")["MarketValue"].sum().to_dict()

    # 计算调仓数据
    rows = []
    total_buy = 0.0
    total_sell = 0.0
    has_cash = False

    for _, alloc_row in allocation.iterrows():
        asset_type = alloc_row["AssetType"]
        target_pct = float(alloc_row["Allocation"])
        current_value = current_by_type.get(asset_type, 0.0)
        current_pct = (current_value / current_total * 100) if current_total > 0 else 0.0
        target_value = target_total * (target_pct / 100)
        adjustment = target_value - current_value

        if adjustment > 0.005:
            action = "买入"
            total_buy += adjustment
        elif adjustment < -0.005:
            action = "卖出"
            total_sell += abs(adjustment)
        else:
            action = "无需调整"
            adjustment = 0.0

        is_cash = "现金" in asset_type
        if is_cash:
            has_cash = True

        rows.append({
            "asset_type": asset_type,
            "current_value": current_value,
            "current_pct": current_pct,
            "target_pct": target_pct,
            "target_value": target_value,
            "adjustment": adjustment,
            "action": action,
            "is_cash": is_cash,
        })

    # 持仓中有但 allocation 未配置的类型
    configured_types = set(allocation["AssetType"].tolist())
    unconfigured = {k: v for k, v in current_by_type.items() if k not in configured_types}

    # 资金缺口
    fund_gap = target_total - current_total
    if fund_gap > 0.005:
        gap_label = f"+{fmt_money_abs(fund_gap)}（需追加资金）"
    elif fund_gap < -0.005:
        gap_label = f"-{fmt_money_abs(abs(fund_gap))}（当前市值超出目标，可赎回）"
    else:
        gap_label = f"{fmt_money_abs(0)}（与目标一致）"

    # 生成 Markdown 内容
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []

    lines.append("# 资产再平衡计划\n")
    lines.append(f"**生成时间：** {now}  ")
    lines.append(f"**目标总市值：** {fmt_money_abs(target_total)}  ")
    lines.append(f"**当前总市值：** {fmt_money_abs(current_total)}  ")
    lines.append(f"**资金缺口：** {gap_label}  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 调仓明细表
    lines.append("## 调仓明细")
    lines.append("")
    lines.append("| 资产类型 | 当前市值 | 当前占比 | 目标占比 | 目标市值 | 调仓金额 | 操作 |")
    lines.append("|----------|----------|----------|----------|----------|----------|------|")

    for row in rows:
        adj = row["adjustment"]
        adj_str = fmt_money(adj) if adj != 0.0 else "¥0.00"
        lines.append(
            f"| {row['asset_type']} "
            f"| {fmt_money_abs(row['current_value'])} "
            f"| {fmt_pct(row['current_pct'])} "
            f"| {fmt_pct(row['target_pct'])} "
            f"| {fmt_money_abs(row['target_value'])} "
            f"| {adj_str} "
            f"| {row['action']} |"
        )

    lines.append("")
    if has_cash:
        lines.append("> ⚠️ 现金类资产调仓需手动操作，请根据实际情况决定是否调整。")
        lines.append("")

    if unconfigured:
        lines.append("> ℹ️ 以下资产类型在持仓中存在但未在配置文件中定义，未计入再平衡计算：")
        for t, v in unconfigured.items():
            lines.append(f">   - **{t}**：当前市值 {fmt_money_abs(v)}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 汇总
    net = total_buy - total_sell
    net_str = fmt_money(net) if net != 0.0 else "¥0.00"
    lines.append("## 汇总")
    lines.append("")
    lines.append(f"- 总买入金额：{fmt_money_abs(total_buy)}")
    lines.append(f"- 总卖出金额：{fmt_money_abs(total_sell)}")
    lines.append(f"- 净操作金额：{net_str}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 当前持仓明细
    lines.append("## 当前持仓明细（参考）")
    lines.append("")
    lines.append("| 代码 | 名称 | 资产类型 | 当前市值 |")
    lines.append("|------|------|----------|----------|")

    for _, asset_row in portfolio.iterrows():
        code = str(asset_row.get("Code", ""))
        name = str(asset_row.get("Name", ""))
        asset_type = str(asset_row.get("AssetType", ""))
        market_value = float(asset_row.get("MarketValue", 0))
        lines.append(f"| {code} | {name} | {asset_type} | {fmt_money_abs(market_value)} |")

    lines.append("")

    # 写入文件
    content = "\n".join(lines)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    # 输出摘要
    print(f"✓ 调仓计划生成成功：{output_file}")
    print(f"  目标总市值：{fmt_money_abs(target_total)}")
    print(f"  当前总市值：{fmt_money_abs(current_total)}")
    print(f"  资金缺口：{gap_label}")
    if total_buy > 0:
        print(f"  总买入：{fmt_money_abs(total_buy)}")
    if total_sell > 0:
        print(f"  总卖出：{fmt_money_abs(total_sell)}")


def main() -> None:
    if len(sys.argv) < 2:
        print("用法：uv run script.py <目标总市值> [portfolio_with_prices.csv] [asset_allocation.csv] [re_balance.md]")
        print("示例：uv run script.py 100000")
        sys.exit(1)

    try:
        target_total = float(sys.argv[1])
    except ValueError:
        print(f"❌ 错误：目标总市值必须是数字，收到：{sys.argv[1]}")
        sys.exit(1)

    if target_total <= 0:
        print("❌ 错误：目标总市值必须大于 0")
        sys.exit(1)

    portfolio_file = sys.argv[2] if len(sys.argv) > 2 else "portfolio_with_prices.csv"
    allocation_file = sys.argv[3] if len(sys.argv) > 3 else "asset_allocation.csv"
    output_file = sys.argv[4] if len(sys.argv) > 4 else "re_balance.md"

    # 检查输入文件
    if not os.path.exists(portfolio_file):
        print(f"❌ 错误：找不到 {portfolio_file}")
        print("  请先运行 fetch-asset-prices 生成持仓价格文件")
        sys.exit(1)

    if not os.path.exists(allocation_file):
        print(f"❌ 错误：找不到 {allocation_file}")
        print("  请先创建资产配置目标文件 asset_allocation.csv")
        sys.exit(1)

    generate_rebalance_plan(target_total, portfolio_file, allocation_file, output_file)


if __name__ == "__main__":
    main()
