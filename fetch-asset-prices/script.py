#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "requests",
#   "beautifulsoup4",
# ]
# ///
"""
资产价格获取脚本
读取投资组合，批量获取最新价格并计算财务指标
"""

import pandas as pd
import requests
import time
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# 设置控制台输出编码为 UTF-8 (Windows 兼容)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def load_api_key():
    """从 api_key.txt 读取 API license"""
    key_file = Path("api_key.txt")

    if not key_file.exists():
        print("❌ 错误：找不到 api_key.txt 文件")
        return None

    with open(key_file, 'r', encoding='utf-8') as f:
        license_key = f.read().strip()

    return license_key


def load_reference_data():
    """加载股票和基金列表作为参考数据"""
    stock_map = {}  # {code: (name, exchange)}
    fund_map = {}
    etf_map = {}    # ETF 单独的映射表

    # 加载股票列表
    stock_file = Path("assetBasicInfo/stockCN.csv")
    if stock_file.exists():
        try:
            df_stock = pd.read_csv(stock_file, encoding='utf-8-sig', dtype={'Code': str})
            for _, row in df_stock.iterrows():
                stock_map[row['Code']] = (row['Name'], row['Exchange'])
            print(f"✓ 已加载股票列表: {len(stock_map)} 条")
        except Exception as e:
            print(f"⚠️  加载股票列表失败: {e}")
    else:
        print("⚠️  警告：assetBasicInfo/stockCN.csv 不存在，请先运行 prepare-market-data")

    # 加载ETF列表
    etf_file = Path("assetBasicInfo/etfCN.csv")
    if etf_file.exists():
        try:
            df_etf = pd.read_csv(etf_file, encoding='utf-8-sig', dtype={'Code': str})
            for _, row in df_etf.iterrows():
                etf_map[row['Code']] = (row['Name'], row['Exchange'])
            print(f"✓ 已加载ETF列表: {len(etf_map)} 条")
        except Exception as e:
            print(f"⚠️  加载ETF列表失败: {e}")
    else:
        print("⚠️  警告：assetBasicInfo/etfCN.csv 不存在，请先运行 prepare-market-data")

    # 加载开放式基金列表
    fund_file = Path("assetBasicInfo/fundCN.csv")
    if fund_file.exists():
        try:
            df_fund = pd.read_csv(fund_file, encoding='utf-8-sig', dtype={'Code': str})
            for _, row in df_fund.iterrows():
                fund_map[row['Code']] = (row['Name'], row['Exchange'])
            print(f"✓ 已加载开放式基金列表: {len(fund_map)} 条")
        except Exception as e:
            print(f"⚠️  加载开放式基金列表失败: {e}")
    else:
        print("⚠️  警告：assetBasicInfo/fundCN.csv 不存在，请先运行 prepare-market-data")

    return stock_map, fund_map, etf_map


def get_stock_price(code, license_key):
    """获取股票实时价格"""
    # 清理代码，只保留数字部分
    clean_code = code.replace('.', '').replace('SH', '').replace('SZ', '')

    api_url = f"https://api.biyingapi.com/hsstock/real/time/{clean_code}/{license_key}"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'p' in data:
            return float(data['p'])
        return None

    except Exception as e:
        print(f"  ⚠️  获取 {code} 价格失败: {e}")
        return None


def get_fund_price(code, license_key):
    """获取基金实时价格，返回 (price, name, source) 元组
    source: 'api' 或 'scraper' 或 None
    """
    # 清理代码
    clean_code = code.replace('.', '').replace('SH', '').replace('SZ', '')

    api_url = f"https://api.biyingapi.com/fd/real/time/{clean_code}/{license_key}"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'p' in data and data['p'] is not None:
            return float(data['p']), None, 'api'
        # API 返回成功但没有价格数据，尝试爬虫
        return scrape_fund_price_from_eastmoney(clean_code)

    except Exception:
        # API 失败，尝试爬虫
        return scrape_fund_price_from_eastmoney(clean_code)


def scrape_fund_price_from_eastmoney(code):
    """从天天基金网爬取基金净值和名称，返回 (price, name, 'scraper') 或 (None, None, None)"""
    url = f"https://fund.eastmoney.com/{code}.html"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()

        # 使用 content 并手动解码为 UTF-8，避免编码问题
        soup = BeautifulSoup(response.content.decode('utf-8', errors='ignore'), 'html.parser')

        # 提取基金名称（从页面标题）
        fund_name = None
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            # 标题格式：基金名称(代码)基金净值_估值_行情走势—天天基金网
            # 提取括号前的部分
            if '(' in title_text:
                fund_name = title_text.split('(')[0].strip()
            elif '（' in title_text:
                fund_name = title_text.split('（')[0].strip()
            else:
                # 备用：去掉后缀
                for suffix in ['基金净值', '基金估值', '行情走势', '—天天基金网']:
                    if suffix in title_text:
                        fund_name = title_text.split(suffix)[0].strip()
                        break

        # 查找单位净值
        # 方法1：查找包含大号数字且颜色为红/绿的span（单位净值通常显示为大号红色）
        for span in soup.find_all('span', class_=lambda x: x and 'ui-font-large' in str(x)):
            text = span.get_text().strip()
            # 检查是否为纯数字（可能是价格）
            try:
                value = float(text)
                # 单位净值通常在 0.1 - 100 之间
                if 0.01 < value < 1000:
                    return value, fund_name, 'scraper'
            except ValueError:
                continue

        # 方法2：查找所有带 ui-num 类的数字，找第一个合理的净值
        for span in soup.find_all('span', class_='ui-num'):
            text = span.get_text().strip()
            try:
                value = float(text)
                if 0.01 < value < 1000:
                    # 检查是否在"单位净值"相关区域
                    parent = span.find_parent(class_=lambda x: x and ('item' in str(x).lower() or 'info' in str(x).lower()))
                    if parent:
                        # 检查区域内是否有"单位净值"文字
                        area_text = parent.get_text()
                        if '单位净值' in area_text or '净值' in area_text:
                            return value, fund_name, 'scraper'
            except ValueError:
                continue

        return None, None, None

    except Exception:
        return None, None, None


def load_portfolio(portfolio_file):
    """加载投资组合文件"""
    file_path = Path(portfolio_file)

    if not file_path.exists():
        print(f"❌ 错误：找不到投资组合文件 {portfolio_file}")
        print(f"   请在当前目录下创建 {portfolio_file} 文件")
        print(f"   必需列：Code, Quantity, Cost, AssetCategory, AssetType")
        return None

    try:
        # 读取时将 Code 列作为字符串类型
        df = pd.read_csv(file_path, encoding='utf-8-sig', dtype={'Code': str})

        # 检查必需列
        required_cols = ['Code', 'Quantity', 'Cost', 'AssetCategory', 'AssetType']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"❌ 错误：缺少必需的列: {', '.join(missing_cols)}")
            return None

        # 检查数据
        if df.empty:
            print("❌ 错误：投资组合文件为空")
            return None

        print(f"✓ 已加载投资组合: {len(df)} 项资产")
        return df

    except Exception as e:
        print(f"❌ 读取投资组合文件失败: {e}")
        return None


def match_asset_info(code, asset_category, stock_map, fund_map, etf_map=None, scraped_names=None):
    """匹配资产名称和交易所，支持 ETF 回退查询和爬虫名称"""
    if etf_map is None:
        etf_map = {}
    if scraped_names is None:
        scraped_names = {}

    # 现金类资产直接返回固定信息
    if asset_category == '现金':
        return ("现金", "—")

    # 对于基金，优先使用爬虫获取的名称
    if asset_category == '基金' and code in scraped_names:
        fund_name = scraped_names[code]
        # 交易所信息仍需要从列表中查找
        exchange = "未知"
        if code in fund_map:
            exchange = fund_map[code][1]
        elif code in etf_map:
            exchange = etf_map[code][1]
        # 尝试不带后缀的匹配查找交易所
        if exchange == "未知":
            code_base = code.split('.')[0]
            for k, v in fund_map.items():
                if k.startswith(code_base):
                    exchange = v[1]
                    break
            if exchange == "未知":
                for k, v in etf_map.items():
                    if k.startswith(code_base):
                        exchange = v[1]
                        break
        return (fund_name, exchange)

    if asset_category == '股票':
        if code in stock_map:
            return stock_map[code]
        # 尝试不带后缀的匹配
        code_base = code.split('.')[0]
        for k, v in stock_map.items():
            if k.startswith(code_base):
                return v

    elif asset_category == '基金':
        # 先在开放式基金列表中查找
        if code in fund_map:
            return fund_map[code]
        # 尝试不带后缀的匹配
        code_base = code.split('.')[0]
        for k, v in fund_map.items():
            if k.startswith(code_base):
                return v

        # 如果开放式基金列表中找不到，尝试在 ETF 列表中查找
        if etf_map:
            if code in etf_map:
                return etf_map[code]
            # 尝试不带后缀的匹配
            for k, v in etf_map.items():
                if k.startswith(code_base):
                    return v

    return ("未知", "未知")


def calculate_metrics(row):
    """计算财务指标"""
    quantity = row['Quantity']
    cost = row['Cost']
    current_price = row['CurrentPrice']

    total_cost = quantity * cost
    market_value = quantity * current_price
    profit_loss = market_value - total_cost
    profit_loss_pct = (profit_loss / total_cost * 100) if total_cost > 0 else 0

    return total_cost, market_value, profit_loss, profit_loss_pct


def main():
    """主函数"""
    print("=" * 60)
    print("💰 资产价格获取")
    print("=" * 60)
    print()

    # 解析参数
    portfolio_file = "portfolio.csv"
    output_file = "portfolio_with_prices.csv"

    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:]):
            if arg.endswith('.csv') and i == 0:
                portfolio_file = arg
            elif arg.startswith('--output='):
                output_file = arg.split('=')[1]

    print(f"📂 输入文件: {portfolio_file}")
    print(f"📂 输出文件: {output_file}")
    print()

    # 加载 API license
    license_key = load_api_key()
    if not license_key:
        sys.exit(1)

    print(f"🔑 API License: {license_key[:8]}...")
    print()

    # 加载参考数据
    stock_map, fund_map, etf_map = load_reference_data()

    if not stock_map and not fund_map and not etf_map:
        print()
        print("❌ 错误：缺少参考数据文件")
        print("   请先运行: prepare-market-data")
        sys.exit(1)

    print()

    # 加载投资组合
    df_portfolio = load_portfolio(portfolio_file)
    if df_portfolio is None:
        sys.exit(1)

    print()

    # 获取价格
    print("📡 正在获取实时价格...")
    print("-" * 60)

    success_count = 0
    fail_count = 0

    prices = []
    scraped_names = {}  # 存储爬虫获取的基金名称 {code: name}

    for idx, row in df_portfolio.iterrows():
        # 确保 code 是字符串类型
        code = str(row['Code']).strip()
        category = row['AssetCategory']

        print(f"  [{idx+1}/{len(df_portfolio)}] {code} ({category})", end=" ")

        if category == '股票':
            price = get_stock_price(code, license_key)
            source = 'api'
            fund_name = None
        elif category == '基金':
            price, fund_name, source = get_fund_price(code, license_key)
            if fund_name and source == 'scraper':
                scraped_names[code] = fund_name
        elif category == '现金':
            price = float(row['Cost'])
            source = 'cash'
            fund_name = None
            print(f"✓ ¥{price:.2f} (现金)")
        else:
            price = None
            source = None
            fund_name = None
            print("✗ 未知类别")

        if source == 'cash':
            # 现金已在上方打印日志，只追加价格
            prices.append(price)
        elif price is not None:
            source_str = "" if source == 'api' else f" ({source})"
            print(f"✓ ¥{price:.2f}{source_str}")
            prices.append(price)
            success_count += 1
        else:
            print("✗ 获取失败")
            prices.append(0.0)
            fail_count += 1

        # 控制请求频率（避免超限）
        if idx < len(df_portfolio) - 1:
            time.sleep(0.2)

    print("-" * 60)
    print(f"✓ 成功: {success_count}, ✗ 失败: {fail_count}")
    print()

    # 添加价格到数据框
    df_portfolio['CurrentPrice'] = prices

    # 匹配资产信息
    print("🔍 正在匹配资产信息...")

    asset_info = df_portfolio.apply(
        lambda row: match_asset_info(
            row['Code'],
            row['AssetCategory'],
            stock_map,
            fund_map,
            etf_map,
            scraped_names
        ),
        axis=1
    )

    df_portfolio['Name'] = [info[0] for info in asset_info]

    # 计算财务指标
    print("🧮 正在计算财务指标...")

    metrics = df_portfolio.apply(calculate_metrics, axis=1)
    df_portfolio['TotalCost'] = [m[0] for m in metrics]
    df_portfolio['MarketValue'] = [m[1] for m in metrics]
    df_portfolio['ProfitLoss'] = [m[2] for m in metrics]
    df_portfolio['ProfitLossPct'] = [m[3] for m in metrics]

    # 重新排列列
    columns_order = [
        'Code', 'Name', 'AssetCategory', 'AssetType',
        'Quantity', 'Cost', 'CurrentPrice',
        'TotalCost', 'MarketValue', 'ProfitLoss', 'ProfitLossPct'
    ]

    # 只保留存在的列
    columns_order = [col for col in columns_order if col in df_portfolio.columns]
    df_portfolio = df_portfolio[columns_order]

    # 保存结果
    print()
    try:
        df_portfolio.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✓ 已保存结果: {output_file}")
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")
        sys.exit(1)

    # 回写 Name 到 portfolio.csv（仅补填空值，不覆盖已有内容）
    try:
        df_source = pd.read_csv(portfolio_file, encoding='utf-8-sig', dtype={'Code': str})

        if 'Name' in df_source.columns:
            # 只回写有效名称（排除 '未知' 和空值）
            name_lookup = {
                code: name for code, name in zip(df_portfolio['Code'], df_portfolio['Name'])
                if name and str(name).strip() not in ('', '未知')
            }
            blank_mask = df_source['Name'].isna() | (df_source['Name'].astype(str).str.strip() == '')
            writable_mask = blank_mask & df_source['Code'].isin(name_lookup)
            if writable_mask.any():
                df_source['Name'] = df_source['Name'].astype(object)
                df_source.loc[writable_mask, 'Name'] = df_source.loc[writable_mask, 'Code'].map(name_lookup)
                df_source.to_csv(portfolio_file, index=False, encoding='utf-8-sig')
                written = writable_mask.sum()
                skipped = blank_mask.sum() - written
                print(f"✓ 已回写 Name 到 {portfolio_file}（写入 {written} 条，跳过 {skipped} 条未解析）")
    except Exception as e:
        print(f"⚠️  回写 {portfolio_file} 失败（不影响主要结果）: {e}")

    # 输出摘要
    print()
    print("=" * 60)
    print("📋 持仓摘要")
    print("=" * 60)

    total_cost = df_portfolio['TotalCost'].sum()
    total_market_value = df_portfolio['MarketValue'].sum()
    total_profit_loss = df_portfolio['ProfitLoss'].sum()
    total_profit_loss_pct = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0

    print(f"总成本:     ¥{total_cost:,.2f}")
    print(f"总市值:     ¥{total_market_value:,.2f}")
    print(f"总盈亏:     ¥{total_profit_loss:,.2f} ({total_profit_loss_pct:+.2f}%)")
    print()
    print("💡 可以使用 generate-daily-report 生成完整报表")


if __name__ == "__main__":
    main()
