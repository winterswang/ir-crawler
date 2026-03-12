"""
IR 搜索模块 - 使用 Tavily 搜索公司 IR 网页
"""

import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

# 缓存文件路径
CACHE_FILE = Path(__file__).parent.parent / "cache" / "ir_mapping.json"


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


def normalize_company_name(name: str) -> str:
    """标准化公司名称/代码"""
    return name.strip().upper()


def search_ir_url(company: str, use_cache: bool = True) -> dict:
    """
    搜索公司 IR 网页

    Args:
        company: 公司名称或股票代码
        use_cache: 是否使用缓存

    Returns:
        {
            "company": str,
            "ir_url": str,
            "source": "cache" | "search",
            "company_name": str,
            "market": str
        }
    """
    from tavily import TavilyClient
    from dotenv import load_dotenv

    load_dotenv()

    normalized = normalize_company_name(company)
    cache = load_cache()

    # 1. 检查缓存
    if use_cache and normalized in cache:
        cached = cache[normalized]
        return {
            "company": company,
            "ir_url": cached["ir_url"],
            "source": "cache",
            "company_name": cached.get("company_name", company),
            "market": cached.get("market", "unknown")
        }

    # 2. 检查是否是直接 URL
    if company.startswith("http"):
        return {
            "company": company,
            "ir_url": company,
            "source": "direct",
            "company_name": "Unknown",
            "market": "unknown"
        }

    # 3. Tavily 搜索
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not found in environment")

    client = TavilyClient(api_key=api_key)

    # 构建搜索查询
    query = f"{company} investor relations official site"

    print(f"🔍 搜索: {query}")

    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5
        )

        # 从结果中提取 IR 网页
        ir_url = None
        company_name = company
        market = "unknown"

        for result in response.get("results", []):
            url = result.get("url", "")
            title = result.get("title", "").lower()

            # 识别 IR 相关页面
            ir_keywords = ["investor", "ir.", "/ir/", "investors", "投资关系"]
            if any(kw in url.lower() or kw in title for kw in ir_keywords):
                ir_url = url
                # 尝试从标题提取公司名
                if " - " in result.get("title", ""):
                    company_name = result["title"].split(" - ")[0].strip()
                break

        if not ir_url and response.get("results"):
            # 如果没找到明确的 IR 页面，使用第一个结果
            ir_url = response["results"][0].get("url")

        if not ir_url:
            raise ValueError(f"未找到 {company} 的 IR 网页")

        # 保存到缓存
        cache[normalized] = {
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

    except Exception as e:
        raise ValueError(f"搜索失败: {e}")


if __name__ == "__main__":
    # 测试
    result = search_ir_url("腾讯控股")
    print(json.dumps(result, ensure_ascii=False, indent=2))