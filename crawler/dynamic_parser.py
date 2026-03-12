"""
动态内容解析器 - 解析JavaScript渲染页面中的文件数据
支持解析 __NEXT_DATA__ 等常见前端框架数据嵌入方式
"""

import json
import re
import asyncio
from typing import Optional
from playwright.async_api import async_playwright


async def extract_next_data(url: str, timeout: int = 60000) -> dict:
    """
    提取页面中的 __NEXT_DATA__ 数据 (Next.js框架)
    
    Returns:
        解析后的JSON数据
    """
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, timeout=timeout)
            await asyncio.sleep(2)
            
            # 提取 __NEXT_DATA__
            next_data = await page.eval_on_selector('script#__NEXT_DATA__', 'el => el.textContent')
            
            if next_data:
                return json.loads(next_data)
            
        except Exception as e:
            print(f"提取 __NEXT_DATA__ 失败: {e}")
        finally:
            await browser.close()
    
    return {}


async def extract_embedded_json(url: str, timeout: int = 60000) -> list:
    """
    提取页面中嵌入的各种JSON数据
    
    查找:
    - __NEXT_DATA__ (Next.js)
    - window.__INITIAL_STATE__
    - window.pageData
    - 其他内联JSON
    """
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, timeout=timeout)
            await asyncio.sleep(2)
            
            # 获取页面HTML
            html = await page.content()
            
            # 1. 查找 __NEXT_DATA__
            next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if next_data_match:
                try:
                    data = json.loads(next_data_match.group(1))
                    return [('next_data', data)]
                except:
                    pass
            
            # 2. 查找 window.__INITIAL_STATE__ 或类似变量
            initial_state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({[^;]+});', html)
            if initial_state_match:
                try:
                    data = json.loads(initial_state_match.group(1))
                    return [('initial_state', data)]
                except:
                    pass
            
            # 3. 查找其他JSON数据
            json_pattern = re.compile(r'window\.(\w+)\s*=\s*(\{[^;]+\});')
            matches = json_pattern.findall(html)
            
            results = []
            for var_name, json_str in matches:
                try:
                    data = json.loads(json_str)
                    results.append((var_name, data))
                except:
                    pass
            
            return results
            
        except Exception as e:
            print(f"提取嵌入JSON失败: {e}")
        finally:
            await browser.close()
    
    return []


def parse_alibaba_reports(next_data: dict) -> list:
    """
    解析阿里巴巴IR页面的报告数据
    
    Returns:
        [{"title": str, "date": str, "url": str, "type": str}, ...]
    """
    reports = []
    
    try:
        # 尝试多种路径
        paths = [
            "props.pageProps.reports",
            "props.pageProps.earnings",
            "props.initialProps.pageProps.reports",
        ]
        
        for path in paths:
            parts = path.split(".")
            data = next_data
            for part in parts:
                if isinstance(data, dict) and part in data:
                    data = data[part]
                else:
                    data = None
                    break
            
            if data and isinstance(data, list):
                for item in data:
                    report = {
                        "title": item.get("title", ""),
                        "date": item.get("date", item.get("publishDate", "")),
                        "url": item.get("pdfUrl", item.get("url", "")),
                        "type": item.get("type", "report")
                    }
                    if report["url"]:
                        # 补全URL
                        if not report["url"].startswith("http"):
                            report["url"] = "https://www.alibabagroup.com" + report["url"]
                        reports.append(report)
                
                if reports:
                    return reports
                    
    except Exception as e:
        print(f"解析报告数据失败: {e}")
    
    return reports


async def analyze_dynamic_page(url: str) -> list:
    """
    分析动态页面，提取文件列表
    
    Returns:
        [{"title": str, "url": str, "type": str}, ...]
    """
    print(f"🔍 分析动态页面: {url}")
    
    # 1. 尝试提取 __NEXT_DATA__
    next_data = await extract_next_data(url)
    
    if next_data:
        print(f"✅ 找到 __NEXT_DATA__")
        
        # 根据URL判断解析方法
        if "alibabagroup.com" in url:
            reports = parse_alibaba_reports(next_data)
            if reports:
                print(f"✅ 解析到 {len(reports)} 个报告")
                return reports
    
    # 2. 尝试提取其他嵌入JSON
    embedded_data = await extract_embedded_json(url)
    
    if embedded_data:
        print(f"✅ 找到 {len(embedded_data)} 个嵌入数据块")
    
    return []


if __name__ == "__main__":
    # 测试
    async def test():
        url = "https://www.alibabagroup.com/en-US/ir-financial-reports-quarterly-results"
        reports = await analyze_dynamic_page(url)
        
        print("\n报告列表:")
        for r in reports[:10]:
            print(f"  [{r['date']}] {r['title'][:50]}...")
            print(f"    URL: {r['url'][:70]}")
    
    asyncio.run(test())