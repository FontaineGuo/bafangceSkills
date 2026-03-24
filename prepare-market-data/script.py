#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "requests",
# ]
# ///
"""
基础数据准备脚本
获取股票列表和基金列表并缓存到本地 CSV 文件
"""

import pandas as pd
import requests
import os
import sys
from pathlib import Path

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
        print(f"   请在当前目录下创建 api_key.txt 文件，并填入您的 API license")
        return None

    with open(key_file, 'r', encoding='utf-8') as f:
        license_key = f.read().strip()

    if not license_key:
        print("❌ 错误：api_key.txt 文件为空")
        return None

    return license_key


def fetch_stock_list(license_key):
    """获取股票列表"""
    api_url = f"https://api.biyingapi.com/hslt/list/{license_key}"

    try:
        print("📡 正在获取股票列表...")
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()

        data = response.json()

        if not data:
            print("⚠️  警告：API 返回的数据为空")
            return None

        # 转换为 DataFrame
        df = pd.DataFrame(data)

        # 重命名字段
        df = df.rename(columns={
            'dm': 'Code',
            'mc': 'Name',
            'jys': 'Exchange'
        })

        # 确保 Code 列为字符串类型，保留前导0
        df['Code'] = df['Code'].astype(str)

        # 转换交易所代码为大写
        df['Exchange'] = df['Exchange'].str.upper()

        return df

    except requests.exceptions.RequestException as e:
        print(f"❌ API 请求失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 解析数据失败: {e}")
        return None


def fetch_fund_lists(license_key):
    """获取基金列表，返回 ETF 和开放式基金两个 DataFrame"""
    etf_url = f"https://api.biyingapi.com/fd/list/etf/{license_key}"
    all_url = f"https://api.biyingapi.com/fd/list/all/{license_key}"

    etf_data = []
    open_fund_data = []

    # 获取 ETF 列表
    try:
        print("📡 正在获取 ETF 列表...")
        response = requests.get(etf_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data:
            etf_data = data
            print(f"   ✓ 获取到 {len(data)} 个 ETF")
    except Exception as e:
        print(f"⚠️  获取 ETF 列表失败: {e}")

    # 获取开放式基金列表
    try:
        print("📡 正在获取开放式基金列表...")
        response = requests.get(all_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data:
            open_fund_data = data
            print(f"   ✓ 获取到 {len(data)} 个开放式基金")
    except Exception as e:
        print(f"⚠️  获取开放式基金列表失败: {e}")

    # 处理 ETF 数据
    df_etf = None
    if etf_data:
        df_etf = pd.DataFrame(etf_data)
        df_etf = df_etf.rename(columns={
            'dm': 'Code',
            'mc': 'Name',
            'jys': 'Exchange'
        })
        # 确保 Code 列为字符串类型，保留前导0
        df_etf['Code'] = df_etf['Code'].astype(str)
        df_etf['Exchange'] = df_etf['Exchange'].str.upper()
        df_etf = df_etf.drop_duplicates(subset=['Code'], keep='first')

    # 处理开放式基金数据
    df_open = None
    if open_fund_data:
        df_open = pd.DataFrame(open_fund_data)
        df_open = df_open.rename(columns={
            'dm': 'Code',
            'mc': 'Name',
            'jys': 'Exchange'
        })
        # 确保 Code 列为字符串类型，保留前导0
        df_open['Code'] = df_open['Code'].astype(str)
        df_open['Exchange'] = df_open['Exchange'].str.upper()
        df_open = df_open.drop_duplicates(subset=['Code'], keep='first')

    return df_etf, df_open


def save_to_csv(df, filename, description):
    """保存到 CSV 文件"""
    if df is None or df.empty:
        print(f"⚠️  跳过保存 {filename}：无数据")
        return False

    try:
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✓ 已保存 {description}: {filename} ({len(df)} 条记录)")
        return True
    except Exception as e:
        print(f"❌ 保存文件失败 {filename}: {e}")
        return False


def check_file_exists(filename):
    """检查文件是否存在"""
    return Path(filename).exists()


def main():
    """主函数"""
    print("=" * 60)
    print("📊 基础数据准备")
    print("=" * 60)

    # 解析命令行参数
    data_types = "all"  # 默认获取所有数据
    force_refresh = False

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg in ["stocks", "funds", "all"]:
                data_types = arg
            elif arg == "--force":
                force_refresh = True

    print(f"📋 数据类型: {data_types}")
    print(f"🔄 强制刷新: {'是' if force_refresh else '否'}")
    print()

    # 读取 API license
    license_key = load_api_key()
    if not license_key:
        sys.exit(1)

    print(f"🔑 API License: {license_key[:8]}...")
    print()

    # 确保输出目录存在
    Path("assetBasicInfo").mkdir(exist_ok=True)

    results = {"stock": False, "etf": False, "fund": False}

    # 处理股票列表
    if data_types in ["stocks", "all"]:
        stock_file = "assetBasicInfo/stockCN.csv"

        if check_file_exists(stock_file) and not force_refresh:
            print(f"⏭️  股票列表已存在，跳过获取 ({stock_file})")
            results["stock"] = True
        else:
            df_stock = fetch_stock_list(license_key)
            if df_stock is not None:
                results["stock"] = save_to_csv(df_stock, stock_file, "股票列表")
        print()

    # 处理基金列表（ETF 和开放式基金）
    if data_types in ["funds", "all"]:
        etf_file = "assetBasicInfo/etfCN.csv"
        fund_file = "assetBasicInfo/fundCN.csv"

        if check_file_exists(etf_file) and check_file_exists(fund_file) and not force_refresh:
            print(f"⏭️  基金列表已存在，跳过获取 ({etf_file}, {fund_file})")
            results["etf"] = True
            results["fund"] = True
        else:
            df_etf, df_open = fetch_fund_lists(license_key)
            if df_etf is not None:
                results["etf"] = save_to_csv(df_etf, etf_file, "ETF列表")
            if df_open is not None:
                results["fund"] = save_to_csv(df_open, fund_file, "开放式基金列表")
        print()

    # 输出摘要
    print("=" * 60)
    print("📋 执行摘要")
    print("=" * 60)

    if results["stock"]:
        print("✓ 股票列表: assetBasicInfo/stockCN.csv")
    else:
        print("✗ 股票列表: 获取失败")

    if results["etf"]:
        print("✓ ETF列表: assetBasicInfo/etfCN.csv")
    else:
        print("✗ ETF列表: 获取失败")

    if results["fund"]:
        print("✓ 开放式基金列表: assetBasicInfo/fundCN.csv")
    else:
        print("✗ 开放式基金列表: 获取失败")

    print()
    print("💡 这些文件已缓存，后续 skills 会自动使用")


if __name__ == "__main__":
    main()
