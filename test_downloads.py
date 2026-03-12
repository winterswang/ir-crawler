#!/usr/bin/env python3
"""
IR下载测试 - 测试所有预设公司的IR下载能力
记录成功/失败情况及原因
"""

import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

import sys
sys.path.insert(0, str(Path(__file__).parent))

from crawler.company_db import COMPANY_IR_DATABASE
from crawler.analyzer import analyze_page
from crawler.downloader import download_files

# 加载环境变量
load_dotenv('/root/.openclaw/workspace/deer-flow-analysis/backend/.env')

# 测试结果文件
RESULTS_FILE = Path(__file__).parent / "download_test_results.json"


async def test_company_download(company_key: str, info: dict, max_files: int = 3) -> dict:
    """
    测试单个公司的IR下载
    
    Returns:
        {
            "company": str,
            "ir_url": str,
            "page_load": bool,  # 页面是否能加载
            "files_found": int,
            "files_downloaded": int,
            "error_type": str or None,
            "error_message": str or None,
            "solutions": list
        }
    """
    result = {
        "company": info["company_name"],
        "market": info["market"],
        "ir_url": info["ir_url"],
        "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "page_load": False,
        "files_found": 0,
        "files_downloaded": 0,
        "error_type": None,
        "error_message": None,
        "solutions": []
    }
    
    print(f"\n{'='*60}")
    print(f"测试: {info['company_name']} ({info['market']})")
    print(f"IR: {info['ir_url']}")
    print(f"{'='*60}")
    
    try:
        # 1. 测试页面加载和分析
        print("📄 测试页面加载...")
        files, company_name = await analyze_page(info["ir_url"], max_scrolls=3)
        
        result["page_load"] = True
        result["files_found"] = len(files)
        print(f"✅ 页面加载成功，找到 {len(files)} 个文件")
        
        if not files:
            result["error_type"] = "no_files"
            result["error_message"] = "页面解析成功但未找到文件"
            result["solutions"] = ["检查文件扩展名过滤规则", "检查页面是否需要特殊权限"]
            return result
        
        # 2. 测试文件下载
        print(f"📥 测试下载 (最多{max_files}个)...")
        download_results = await download_files(files, info["company_name"], max_files=max_files)
        
        success_count = sum(1 for r in download_results if r.success)
        result["files_downloaded"] = success_count
        
        if success_count > 0:
            print(f"✅ 下载成功: {success_count}/{len(download_results)}")
        
        # 检查失败原因
        failed = [r for r in download_results if not r.success]
        if failed:
            error_types = set(r.error for r in failed if r.error)
            result["error_type"] = "download_failed"
            result["error_message"] = f"{len(failed)} 个文件下载失败: {', '.join(error_types)}"
            result["solutions"] = [
                "增加重试次数",
                "添加代理支持",
                "检查文件URL是否需要特殊请求头"
            ]
        
        return result
        
    except asyncio.TimeoutError:
        result["error_type"] = "timeout"
        result["error_message"] = "页面加载超时"
        result["solutions"] = [
            "增加页面加载超时时间",
            "使用代理服务器",
            "检查网络连接"
        ]
        print(f"❌ 超时错误")
        return result
        
    except Exception as e:
        error_msg = str(e)
        
        # 分析错误类型
        if "ERR_HTTP2_PROTOCOL_ERROR" in error_msg:
            result["error_type"] = "http2_error"
            result["error_message"] = "HTTP2协议错误"
            result["solutions"] = [
                "使用HTTP/1.1降级",
                "添加代理支持",
                "检查服务器HTTP2支持"
            ]
        elif "ERR_CONNECTION" in error_msg or "Connection reset" in error_msg:
            result["error_type"] = "connection_error"
            result["error_message"] = "连接被重置"
            result["solutions"] = [
                "检查防火墙设置",
                "使用代理服务器",
                "降低请求频率"
            ]
        elif "net::ERR" in error_msg:
            result["error_type"] = "network_error"
            result["error_message"] = error_msg
            result["solutions"] = [
                "检查网络连接",
                "使用代理",
                "验证URL是否可访问"
            ]
        else:
            result["error_type"] = "unknown"
            result["error_message"] = error_msg
            result["solutions"] = ["检查错误详情", "添加错误处理"]
        
        print(f"❌ 错误: {error_msg}")
        return result


async def main():
    """测试所有公司"""
    print("=" * 60)
    print("IR Crawler 下载测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_results = []
    
    # 按市场分组测试
    markets = {}
    for key, info in COMPANY_IR_DATABASE.items():
        market = info["market"]
        if market not in markets:
            markets[market] = []
        markets[market].append((key, info))
    
    for market, companies in markets.items():
        print(f"\n\n{'#'*60}")
        print(f"# 市场: {market}")
        print(f"{'#'*60}")
        
        for company_key, info in companies:
            result = await test_company_download(company_key, info, max_files=3)
            all_results.append(result)
            
            # 避免频繁请求
            print("\n⏳ 等待3秒...")
            await asyncio.sleep(3)
    
    # 生成报告
    print("\n\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    # 统计
    total = len(all_results)
    success = sum(1 for r in all_results if r["files_downloaded"] > 0)
    page_failed = sum(1 for r in all_results if not r["page_load"])
    download_failed = sum(1 for r in all_results if r["page_load"] and r["files_found"] > 0 and r["files_downloaded"] == 0)
    no_files = sum(1 for r in all_results if r["page_load"] and r["files_found"] == 0)
    
    print(f"\n📊 统计:")
    print(f"   总测试数: {total}")
    print(f"   ✅ 下载成功: {success}")
    print(f"   ❌ 页面加载失败: {page_failed}")
    print(f"   ❌ 下载失败: {download_failed}")
    print(f"   ⚠️ 未找到文件: {no_files}")
    
    # 按错误类型分组
    print("\n📋 错误类型分布:")
    error_types = {}
    for r in all_results:
        if r["error_type"]:
            et = r["error_type"]
            if et not in error_types:
                error_types[et] = []
            error_types[et].append(r["company"])
    
    for et, companies in error_types.items():
        print(f"\n   {et}:")
        for c in companies:
            print(f"      - {c}")
    
    # 详细结果表格
    print("\n\n📋 详细结果:")
    print("| 公司 | 市场 | 页面加载 | 文件数 | 下载 | 错误类型 |")
    print("|------|------|----------|--------|------|----------|")
    for r in all_results:
        load = "✅" if r["page_load"] else "❌"
        print(f"| {r['company'][:15]} | {r['market']} | {load} | {r['files_found']} | {r['files_downloaded']} | {r['error_type'] or '-'} |")
    
    # 保存结果
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n\n💾 结果已保存: {RESULTS_FILE}")


if __name__ == "__main__":
    asyncio.run(main())