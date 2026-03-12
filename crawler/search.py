"""
IR 搜索模块 - 搜索公司 IR 网页
V1.2: 简化版本，依赖预设数据库和缓存，不使用外部搜索API
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

# 缓存文件路径
CACHE_FILE = Path(__file__).parent.parent / "cache" / "ir_mapping.json"

# 导入公司数据库
from .company_db import lookup_company, COMPANY_IR_DATABASE


def load_cache() -> dict:
    """加载本地缓存"""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    """保存缓存"""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def normalize_query(query: str) -> str:
    """标准化查询"""
    return query.strip()


def search_ir_url(company: str, use_cache: bool = True) -> dict:
    """
    搜索公司 IR 网页
    
    优先级:
    1. 直接URL输入
    2. 公司数据库预设
    3. 本地缓存
    4. 提示用户手动指定
    
    Args:
        company: 公司名称或股票代码
        use_cache: 是否使用缓存
        
    Returns:
        {
            "company": str,
            "ir_url": str,
            "source": "direct" | "database" | "cache" | "manual",
            "company_name": str,
            "market": str
        }
    """
    query = normalize_query(company)

    # 1. 检查是否是直接 URL
    if query.startswith("http"):
        return {
            "company": company,
            "ir_url": query,
            "source": "direct",
            "company_name": "Unknown",
            "market": "unknown"
        }

    # 2. 检查公司数据库预设
    db_result = lookup_company(query)
    if db_result:
        print(f"📚 从预设数据库找到: {db_result['company_name']}")
        return {
            "company": company,
            "ir_url": db_result["ir_url"],
            "source": "database",
            "company_name": db_result["company_name"],
            "market": db_result["market"]
        }

    # 3. 检查本地缓存
    cache = load_cache()
    cache_key = query.upper()
    
    if use_cache and cache_key in cache:
        cached = cache[cache_key]
        print(f"💾 从缓存加载: {cached.get('company_name', company)}")
        return {
            "company": company,
            "ir_url": cached["ir_url"],
            "source": "cache",
            "company_name": cached.get("company_name", company),
            "market": cached.get("market", "unknown")
        }

    # 4. 未找到，提示用户
    print(f"\n❌ 未找到 {company} 的 IR 网址")
    print(f"\n💡 解决方案:")
    print(f"   1. 直接指定 IR 网址: python skill.py https://ir.example.com")
    print(f"   2. 查看预设公司列表: python skill.py --list")
    print(f"   3. 添加到预设数据库: 编辑 crawler/company_db.py")
    
    raise ValueError(f"未找到 {company} 的 IR 网址，请直接指定或添加到预设数据库")


def add_to_cache(company: str, ir_url: str, company_name: str = None, market: str = "unknown"):
    """
    添加公司到缓存
    
    Args:
        company: 公司名/代码
        ir_url: IR网址
        company_name: 公司名称
        market: 市场
    """
    cache = load_cache()
    cache_key = company.upper()
    
    cache[cache_key] = {
        "ir_url": ir_url,
        "company_name": company_name or company,
        "market": market,
        "last_updated": datetime.now().strftime("%Y-%m-%d")
    }
    
    save_cache(cache)
    print(f"✅ 已添加到缓存: {company} -> {ir_url}")


if __name__ == "__main__":
    # 测试
    test_queries = ["腾讯", "瑞幸咖啡", "不存在的公司"]
    for q in test_queries:
        try:
            result = search_ir_url(q)
            print(f"✅ {q} → {result['company_name']} ({result['source']})")
            print(f"   URL: {result['ir_url']}")
        except Exception as e:
            print(f"❌ {q}: {e}")