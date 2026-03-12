#!/usr/bin/env python3
"""
IR Crawler Skill - 上市公司IR网页爬取工具

用法:
    python skill.py <公司名/股票代码/IR网址> [--max-files N]
"""

import asyncio
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from crawler.search import search_ir_url
from crawler.analyzer import analyze_page, sort_by_priority
from crawler.downloader import download_files
from crawler.manifest import generate_manifest


def print_banner():
    """打印横幅"""
    print("""
╔═══════════════════════════════════════════╗
║       IR Crawler v1.0 - IR文件爬取工具     ║
╚═══════════════════════════════════════════╝
""")


async def crawl_ir(company: str, max_files: int = None) -> dict:
    """
    爬取 IR 文件

    Args:
        company: 公司名称/股票代码/IR网址
        max_files: 最大下载文件数

    Returns:
        {
            "success": bool,
            "company": str,
            "ir_url": str,
            "files_found": int,
            "files_downloaded": int,
            "manifest_path": str,
            "error": str (if failed)
        }
    """
    print_banner()

    try:
        # 1. 搜索 IR 网页
        print(f"📌 目标: {company}")
        print("-" * 40)

        ir_info = search_ir_url(company)
        ir_url = ir_info["ir_url"]
        company_name = ir_info.get("company_name", company)

        print(f"🏢 公司: {company_name}")
        print(f"🔗 IR网址: {ir_url}")
        print(f"📍 来源: {ir_info['source']}")
        print("-" * 40)

        # 2. 分析网页
        files = await analyze_page(ir_url)

        if not files:
            return {
                "success": False,
                "company": company,
                "ir_url": ir_url,
                "files_found": 0,
                "files_downloaded": 0,
                "error": "未找到可下载的文件"
            }

        print(f"\n📋 文件类型分布:")
        from collections import Counter
        type_counts = Counter(f.file_type for f in files)
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"   {t}: {c} 文件")

        # 3. 下载文件
        results = await download_files(files, company_name, max_files=max_files)

        # 4. 生成清单
        manifest_path = generate_manifest(
            company=company_name,
            ir_url=ir_url,
            results=results,
            company_name=company_name
        )

        # 统计
        success_count = sum(1 for r in results if r.success)

        print("\n" + "=" * 40)
        print("✅ 爬取完成!")
        print(f"   发现文件: {len(files)}")
        print(f"   下载成功: {success_count}")
        print(f"   清单路径: {manifest_path}")
        print("=" * 40)

        return {
            "success": True,
            "company": company_name,
            "ir_url": ir_url,
            "files_found": len(files),
            "files_downloaded": success_count,
            "manifest_path": manifest_path
        }

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "company": company,
            "error": str(e)
        }


def main():
    """主函数"""
    import argparse

    load_dotenv()

    parser = argparse.ArgumentParser(description="IR Crawler - IR文件爬取工具")
    parser.add_argument("company", help="公司名称/股票代码/IR网址")
    parser.add_argument("--max-files", "-m", type=int, default=None, help="最大下载文件数")
    parser.add_argument("--json", "-j", action="store_true", help="输出JSON格式")

    args = parser.parse_args()

    # 运行爬取
    result = asyncio.run(crawl_ir(args.company, args.max_files))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())