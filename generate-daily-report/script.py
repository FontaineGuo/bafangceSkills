#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
# ]
# ///
"""
日度报表生成脚本
根据持仓数据和资产配置目标生成完整的日度报表
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# 设置控制台输出编码为 UTF-8 (Windows 兼容)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def load_portfolio(portfolio_file):
    """加载带价格的投资组合"""
    file_path = Path(portfolio_file)

    if not file_path.exists():
        print(f"❌ 错误：找不到投资组合文件 {portfolio_file}")
        print(f"   请先运行 fetch-asset-prices 生成该文件")
        return None

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig', dtype={'Code': str})

        # 检查必需列
        required_cols = ['Code', 'AssetType', 'MarketValue', 'ProfitLoss', 'ProfitLossPct']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"❌ 错误：缺少必需的列: {', '.join(missing_cols)}")
            return None

        print(f"✓ 已加载投资组合: {len(df)} 项资产")
        return df

    except Exception as e:
        print(f"❌ 读取投资组合文件失败: {e}")
        return None


def load_allocation(allocation_file):
    """加载资产配置目标"""
    file_path = Path(allocation_file)

    if not file_path.exists():
        print(f"❌ 错误：找不到资产配置文件 {allocation_file}")
        print(f"   请创建该文件，包含列：AssetType, Allocation, Bias")
        return None

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')

        # 检查必需列
        required_cols = ['AssetType', 'Allocation', 'Bias']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"❌ 错误：缺少必需的列: {', '.join(missing_cols)}")
            return None

        print(f"✓ 已加载资产配置: {len(df)} 个类型")
        return df

    except Exception as e:
        print(f"❌ 读取资产配置文件失败: {e}")
        return None


def calculate_summary(df_portfolio):
    """计算汇总指标"""
    total_cost = df_portfolio['TotalCost'].sum() if 'TotalCost' in df_portfolio.columns else 0
    total_market_value = df_portfolio['MarketValue'].sum()
    total_profit_loss = df_portfolio['ProfitLoss'].sum()
    total_profit_loss_pct = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0

    return {
        'total_cost': total_cost,
        'total_market_value': total_market_value,
        'total_profit_loss': total_profit_loss,
        'total_profit_loss_pct': total_profit_loss_pct
    }


def calculate_allocation_analysis(df_portfolio, df_allocation):
    """计算资产配置分析"""
    # 按资产类型分组
    grouped = df_portfolio.groupby('AssetType')['MarketValue'].sum().reset_index()
    grouped.columns = ['AssetType', 'MarketValue']

    total_market_value = grouped['MarketValue'].sum()
    grouped['ActualAllocation'] = (grouped['MarketValue'] / total_market_value * 100).round(2)

    # 合并目标配置
    analysis = pd.merge(
        grouped,
        df_allocation,
        on='AssetType',
        how='left'
    )

    # 计算偏离度
    analysis['Deviation'] = (analysis['ActualAllocation'] - analysis['Allocation']).abs().round(2)

    # 检查是否超出偏差
    analysis['Status'] = analysis.apply(
        lambda row: '⚠️ 超出偏差' if row['Deviation'] > row['Bias'] else '✓',
        axis=1
    )

    return analysis


def generate_warnings(analysis):
    """生成配置警告信息"""
    warnings = []

    for _, row in analysis[analysis['Status'] == '⚠️ 超出偏差'].iterrows():
        actual = row['ActualAllocation']
        target = row['Allocation']
        bias = row['Bias']
        asset_type = row['AssetType']

        if actual > target:
            msg = f"• {asset_type}配置比例 {actual}%，高于目标 {target}%，超出偏差范围 {bias}%"
        else:
            msg = f"• {asset_type}配置比例 {actual}%，低于目标 {target}%，超出偏差范围 {bias}%"

        warnings.append(msg)

    return warnings


def save_csv_report(df_portfolio, analysis, summary, output_file):
    """保存 CSV 格式报表"""
    try:
        # 资产明细
        detail_cols = [
            'Code', 'Name', 'Exchange', 'AssetCategory', 'AssetType',
            'Quantity', 'Cost', 'CurrentPrice',
            'TotalCost', 'MarketValue', 'ProfitLoss', 'ProfitLossPct'
        ]
        detail_cols = [col for col in detail_cols if col in df_portfolio.columns]
        df_detail = df_portfolio[detail_cols].copy()

        # 添加合并行（用于配置分析）
        # CSV 格式下，我们在后面添加配置分析部分

        # 保存主报表
        with open(output_file, 'w', encoding='utf-8-sig') as f:
            # 写入资产明细
            f.write("=== 资产明细 ===\n")
            df_detail.to_csv(f, index=False)

            f.write("\n\n=== 配置分析 ===\n")
            analysis_cols = ['AssetType', 'ActualAllocation', 'Allocation', 'Deviation', 'Bias', 'Status']
            analysis[analysis_cols].to_csv(f, index=False)

            f.write("\n\n=== 汇总信息 ===\n")
            f.write(f"总成本,{summary['total_cost']:.2f}\n")
            f.write(f"总市值,{summary['total_market_value']:.2f}\n")
            f.write(f"总盈亏,{summary['total_profit_loss']:.2f}\n")
            f.write(f"总收益率,{summary['total_profit_loss_pct']:.2f}%\n")

        print(f"✓ 已保存 CSV 报表: {output_file}")
        return True

    except Exception as e:
        print(f"❌ 保存 CSV 报表失败: {e}")
        return False


def save_text_report(df_portfolio, analysis, summary, warnings, output_file):
    """保存文本格式报表"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 标题
            f.write("=" * 40 + "\n")
            f.write("  投资组合日度报表\n")
            f.write(f"  日期：{datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("=" * 40 + "\n\n")

            # 资产明细
            f.write("📊 资产明细\n")
            f.write("-" * 40 + "\n")

            detail_cols = ['Code', 'Name', 'AssetType', 'Quantity', 'Cost', 'CurrentPrice', 'MarketValue', 'ProfitLoss', 'ProfitLossPct']
            detail_cols = [col for col in detail_cols if col in df_portfolio.columns]

            for _, row in df_portfolio.iterrows():
                code = row.get('Code', 'N/A')
                name = row.get('Name', 'N/A')
                asset_type = row.get('AssetType', 'N/A')
                quantity = row.get('Quantity', 0)
                cost = row.get('Cost', 0)
                current_price = row.get('CurrentPrice', 0)
                market_value = row.get('MarketValue', 0)
                profit_loss = row.get('ProfitLoss', 0)
                profit_loss_pct = row.get('ProfitLossPct', 0)

                profit_sign = '+' if profit_loss >= 0 else ''
                profit_pct_sign = '+' if profit_loss_pct >= 0 else ''

                f.write(f"{code:<10} {name:<14} {asset_type:<6} ")
                f.write(f"{quantity:>6} {cost:>6.2f} {current_price:>6.2f} ")
                f.write(f"{market_value:>10,.2f} {profit_sign}{profit_loss:>8.2f} {profit_pct_sign}{profit_loss_pct:>6.2f}%\n")

            # 配置分析
            f.write("\n📈 配置分析\n")
            f.write("-" * 40 + "\n")
            f.write(f"{'资产类型':<12} {'实际比例':>10} {'目标比例':>10} {'偏离度':>8} {'状态':>12}\n")

            for _, row in analysis.iterrows():
                asset_type = row['AssetType']
                actual = row['ActualAllocation']
                target = row['Allocation']
                deviation = row['Deviation']
                status = row['Status']

                f.write(f"{asset_type:<12} {actual:>9.1f}% {target:>9.1f}% {deviation:>7.1f}% {status:>12}\n")

            # 汇总信息
            f.write("\n📋 汇总信息\n")
            f.write("-" * 40 + "\n")
            profit_sign = '+' if summary['total_profit_loss'] >= 0 else ''
            profit_pct_sign = '+' if summary['total_profit_loss_pct'] >= 0 else ''

            f.write(f"总成本：     ¥{summary['total_cost']:,.2f}\n")
            f.write(f"总市值：     ¥{summary['total_market_value']:,.2f}\n")
            f.write(f"总盈亏：     {profit_sign}¥{summary['total_profit_loss']:,.2f} ({profit_pct_sign}{summary['total_profit_loss_pct']:.2f}%)\n")

            # 警告信息
            if warnings:
                f.write("\n⚠️ 配置警告\n")
                f.write("-" * 40 + "\n")
                for warning in warnings:
                    f.write(f"{warning}\n")

        print(f"✓ 已保存文本报表: {output_file}")
        return True

    except Exception as e:
        print(f"❌ 保存文本报表失败: {e}")
        return False


def save_html_report(df_portfolio, analysis, summary, warnings, output_file):
    """保存 HTML 格式报表"""
    template_path = Path(__file__).parent / "report_template.html"

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
    except Exception as e:
        print(f"❌ 读取 HTML 模板失败: {e}")
        return False

    try:
        # ── 资产明细行 ──
        asset_rows = []
        for _, row in df_portfolio.iterrows():
            pl = row.get('ProfitLoss', 0)
            pl_pct = row.get('ProfitLossPct', 0)
            cls = 'profit' if pl >= 0 else 'loss'
            sign = '+' if pl >= 0 else ''
            asset_rows.append(f"""
          <tr>
            <td class="code">{row.get('Code', '')}</td>
            <td>{row.get('Name', '未知')}</td>
            <td><span class="tag">{row.get('AssetType', '')}</span></td>
            <td>{row.get('Quantity', 0):,.0f}</td>
            <td>¥{row.get('Cost', 0):.3f}</td>
            <td>¥{row.get('CurrentPrice', 0):.3f}</td>
            <td>¥{row.get('MarketValue', 0):,.2f}</td>
            <td class="{cls}">{sign}¥{pl:,.2f}</td>
            <td class="{cls}">{sign}{pl_pct:.2f}%</td>
          </tr>""")

        # ── 配置分析行 ──
        alloc_rows = []
        for _, row in analysis.iterrows():
            actual = row['ActualAllocation']
            target = row['Allocation']
            bias = row['Bias']
            is_warn = row['Status'] == '⚠️ 超出偏差'

            low  = max(0.0, target - bias)
            high = min(100.0, target + bias)
            fill_cls = 'over-high' if actual > high else ('over-low' if actual < low else '')

            alloc_rows.append(f"""
          <tr>
            <td class="alloc-name">{row['AssetType']}</td>
            <td class="alloc-bar-cell">
              <div class="bar-track">
                <div class="bar-fill {fill_cls}" style="width:{min(actual,100):.1f}%"></div>
                <div class="bar-target" style="left:{low:.1f}%;width:{high-low:.1f}%"></div>
              </div>
            </td>
            <td class="alloc-nums">{actual:.1f}% / {target:.1f}%±{bias:.1f}%</td>
            <td class="alloc-status">
              {'<span class="badge-warn">⚠ 超偏差</span>' if is_warn else '<span class="badge-ok">✓</span>'}
            </td>
          </tr>""")

        # ── 警告区块 ──
        if warnings:
            items = '\n'.join(f'<li>{w.lstrip("• ")}</li>' for w in warnings)
            warnings_html = f"""
  <section>
    <div class="warning-list">
      <div class="w-title">⚠ 配置警告（{len(warnings)} 项）</div>
      <ul>{items}</ul>
    </div>
  </section>"""
            warning_badge = f'⚠ {len(warnings)} 项配置警告'
        else:
            warnings_html = ''
            warning_badge = '✓ 配置均在目标范围内'

        pl_total = summary['total_profit_loss']
        pl_cls  = 'profit' if pl_total >= 0 else 'loss'
        pl_sign = '+' if pl_total >= 0 else ''

        html = (html
            .replace('{{REPORT_DATE}}',        datetime.now().strftime('%Y-%m-%d'))
            .replace('{{TOTAL_COST}}',         f"{summary['total_cost']:,.2f}")
            .replace('{{TOTAL_MARKET_VALUE}}', f"{summary['total_market_value']:,.2f}")
            .replace('{{TOTAL_PROFIT_LOSS}}',  f"{abs(pl_total):,.2f}")
            .replace('{{TOTAL_RETURN_PCT}}',   f"{abs(summary['total_profit_loss_pct']):.2f}")
            .replace('{{PROFIT_LOSS_CLASS}}',  pl_cls)
            .replace('{{PROFIT_SIGN}}',        pl_sign)
            .replace('{{ASSET_TABLE_ROWS}}',   '\n'.join(asset_rows))
            .replace('{{ALLOCATION_ROWS}}',    '\n'.join(alloc_rows))
            .replace('{{WARNINGS_HTML}}',      warnings_html)
            .replace('{{WARNING_COUNT_BADGE}}', warning_badge)
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✓ 已保存 HTML 报表: {output_file}")
        return True

    except Exception as e:
        print(f"❌ 保存 HTML 报表失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("📊 生成日度资产报表")
    print("=" * 60)
    print()

    # 解析参数
    portfolio_file = "portfolio_with_prices.csv"
    allocation_file = "asset_allocation.csv"
    output_csv = "report/daily_report.csv"
    output_txt = "report/daily_report.txt"
    output_html = "report/daily_report.html"

    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:]):
            if arg.endswith('.csv') and i == 0:
                portfolio_file = arg
            elif arg.startswith('--allocation='):
                allocation_file = arg.split('=')[1]
            elif arg.startswith('--output='):
                output_csv = arg.split('=')[1]
                output_txt = output_csv.replace('.csv', '.txt')
                output_html = output_csv.replace('.csv', '.html')

    print(f"📂 投资组合: {portfolio_file}")
    print(f"📂 资产配置: {allocation_file}")
    print(f"📂 输出文件: {output_csv}, {output_txt}, {output_html}")
    print()

    # 加载数据
    df_portfolio = load_portfolio(portfolio_file)
    if df_portfolio is None:
        sys.exit(1)

    df_allocation = load_allocation(allocation_file)
    if df_allocation is None:
        sys.exit(1)

    print()

    # 计算汇总指标
    print("🧮 正在计算汇总指标...")
    summary = calculate_summary(df_portfolio)

    # 计算配置分析
    print("📊 正在分析资产配置...")
    analysis = calculate_allocation_analysis(df_portfolio, df_allocation)

    # 生成警告
    warnings = generate_warnings(analysis)

    # 保存报表
    print()
    print("💾 正在生成报表...")

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    csv_ok  = save_csv_report(df_portfolio, analysis, summary, output_csv)
    txt_ok  = save_text_report(df_portfolio, analysis, summary, warnings, output_txt)
    html_ok = save_html_report(df_portfolio, analysis, summary, warnings, output_html)

    # 输出摘要
    print()
    print("=" * 60)
    print("📋 报表摘要")
    print("=" * 60)

    profit_sign = '+' if summary['total_profit_loss'] >= 0 else ''
    profit_pct_sign = '+' if summary['total_profit_loss_pct'] >= 0 else ''

    print(f"总资产：     ¥{summary['total_market_value']:,.2f}")
    print(f"总盈亏：     {profit_sign}¥{summary['total_profit_loss']:,.2f} ({profit_pct_sign}{summary['total_profit_loss_pct']:.2f}%)")

    if warnings:
        print()
        print(f"⚠️ 发现 {len(warnings)} 个配置警告：")
        for warning in warnings:
            print(f"  {warning}")
    else:
        print()
        print("✓ 所有资产配置均符合目标范围")

    print()

    if csv_ok and txt_ok and html_ok:
        print("✓ 报表生成成功")
    else:
        print("✗ 部分报表生成失败")


if __name__ == "__main__":
    main()
