"""
IR 搜索模块 - 使用 Tavily 搜索公司 IR 网页
V1.1 优化: 添加公司数据库预设，提高搜索准确性
"""

import json
import os
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
    4. Tavily搜索
    
    Args:
        company: 公司名称或股票代码
        use_cache: 是否使用缓存
        
    Returns:
        {
            "company": str,
            "ir_url": str,
            "source": "direct" | "database" | "cache" | "search",
            "company_name": str,
            "market": str
        }
    """
    from tavily import TavilyClient
    from dotenv import load_dotenv

    load_dotenv()
    
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

    # 4. Tavily 搜索
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not found in environment")

    client = TavilyClient(api_key=api_key)

    # 构建优化的搜索查询
    # 尝试多种搜索策略
    search_queries = [
        f"{query} investor relations official",
        f"{query} IR investor financial reports",
        f"site:{query}.com investor" if not query.isdigit() else f"{query} investor relations",
    ]
    
    print(f"🔍 搜索: {query}")

    ir_url = None
    company_name = query
    market = "unknown"

    for search_query in search_queries:
        try:
            response = client.search(
                query=search_query,
                search_depth="advanced",
                max_results=5
            )

            # 从结果中提取 IR 网页
            for result in response.get("results", []):
                url = result.get("url", "")
                title = result.get("title", "").lower()
                
                # 排除聚合网站和不相关页面
                exclude_domains = ["alphaspread", "simplywall", "tipranks", "macrotrends", "stockanalysis"]
                if any(domain in url.lower() for domain in exclude_domains):
                    continue
                
                # 排除直接返回文件链接
                if any(ext in url.lower() for ext in [".pdf", ".xlsx", ".doc"]):
                    continue

                # 识别 IR 相关页面
                ir_keywords = ["investor", "ir.", "/ir/", "investors", "投资关系", "financial"]
                if any(kw in url.lower() or kw in title for kw in ir_keywords):
                    ir_url = url
                    # 尝试从标题提取公司名
                    if " - " in result.get("title", ""):
                        company_name = result["title"].split(" - ")[0].strip()
                    elif " | " in result.get("title", ""):
                        company_name = result["title"].split(" | ")[0].strip()
                    break

            if ir_url:
                break

        except Exception as e:
            print(f"⚠️ 搜索失败: {e}")
            continue

    if not ir_url:
        raise ValueError(f"未找到 {company} 的 IR 网页")

    # 保存到缓存
    cache[cache_key] = {
        "ir_url": ir_url,
        "company_name": company_name,
        "market": market,
        "last_updated": datetime.now().strftime("%Y-%m-%d")
    }
    save_cache(cache)

    return {
        "company": company,
        "ir_url": ir_url,
        "source": "search",
        "company_name": company_name,
        "market": market
    }


if __name__ == "__main__":
    # 测试
    test_queries = ["腾讯", "AAPL", "不存在的公司"]
    for q in test_queries:
        try:
            result = search_ir_url(q)
            print(f"✅ {q} → {result['company_name']} ({result['source']})")
            print(f"   URL: {result['ir_url']}")
        except Exception as e:
            print(f"❌ {q}: {e}")