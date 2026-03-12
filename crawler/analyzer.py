"""
网页分析模块 - 使用 Playwright 分析 IR 网页，提取文件链接
V1.1 优化: 公司名称提取、文件名优化
"""

import re
import asyncio
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from urllib.parse import urljoin, urlparse


@dataclass
class PageInfo:
    """页面信息"""
    title: str
    company_name: str
    files: list


@dataclass
class FileInfo:
    """文件信息"""
    url: str
    filename: str
    display_name: str  # 用于显示的名称
    file_type: str  # annual, quarterly, presentation, transcript, other
    extension: str
    size: Optional[int] = None
    title: Optional[str] = None


# 文件类型识别模式
FILE_PATTERNS = {
    "annual": [
        r"annual\s*report",
        r"年报",
        r"20-F",
        r"10-K",
        r"年度报告",
        r"annual\s*report",
        r"financial\s*year",
        r"fiscal\s*year",
    ],
    "quarterly": [
        r"quarterly",
        r"季报",
        r"10-Q",
        r"quarterly\s*report",
        r"季度报告",
        r"earnings\s*release",
        r"interim\s*report",
    ],
    "presentation": [
        r"investor\s*presentation",
        r"investor\s*deck",
        r"演示文稿",
        r"路演",
        r"presentation",
        r"slides?",
        r"investor\s*briefing",
    ],
    "transcript": [
        r"transcript",
        r"电话会议",
        r"earnings\s*call",
        r"会议纪要",
        r"call\s*transcript",
    ],
    "announcement": [
        r"announcement",
        r"公告",
        r"notice",
        r"新闻稿",
        r"press\s*release",
        r"news",
    ],
    "esg": [
        r"esg",
        r"sustainability",
        r"社会责任",
        r"可持续发展",
        r"csr\s*report",
    ]
}

# 支持的文件扩展名
SUPPORTED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".pptx", ".ppt", ".docx", ".doc", ".mp3", ".m4a", ".wav"}


def classify_file(url: str, title: str = "") -> str:
    """根据 URL 和标题分类文件"""
    text = f"{url} {title}".lower()

    for file_type, patterns in FILE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return file_type

    return "other"


def extract_filename(url: str) -> str:
    """从 URL 提取文件名"""
    path = urlparse(url).path
    filename = Path(path).name

    if not filename:
        filename = "unknown_file"

    # 清理文件名
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    return filename


def generate_display_name(url: str, link_text: str, filename: str) -> str:
    """
    生成用于显示的文件名
    
    优先使用链接文字，其次使用文件名
    """
    link_text = link_text.strip() if link_text else ""
    
    # 如果链接文字有意义（长度适中，不是纯数字/hash）
    if link_text and 3 < len(link_text) < 100:
        # 检查是否像有意义的标题
        if not re.match(r'^[a-f0-9]{20,}$', link_text):  # 不是纯hash
            # 清理链接文字
            display = re.sub(r'\s+', '_', link_text)
            display = re.sub(r'[<>:"/\\|?*]', '', display)
            # 添加扩展名
            ext = Path(url).suffix
            if ext and not display.lower().endswith(ext.lower()):
                display = f"{display}{ext}"
            return display
    
    # 使用原始文件名
    return filename


def extract_company_name(page_title: str, url: str) -> str:
    """
    从页面标题提取公司名称
    
    常见格式:
    - "Apple Inc. - Investor Relations"
    - "Tencent Holdings Limited - Investors"
    - "Investor Relations | Microsoft"
    """
    if not page_title:
        return "Unknown"
    
    # 移除常见后缀
    title = page_title
    suffixes = [
        r"\s*[-|]\s*Investor\s*Relations.*",
        r"\s*[-|]\s*Investors.*",
        r"\s*[-|]\s*IR.*",
        r"\s*[-|]\s*Investment\s*Relations.*",
        r"\s*·\s*投资者关系.*",
    ]
    
    for suffix in suffixes:
        title = re.sub(suffix, "", title, flags=re.IGNORECASE)
    
    # 清理
    title = title.strip()
    
    # 如果标题太长或太短，可能不是公司名
    if len(title) < 2 or len(title) > 100:
        # 尝试从 URL 提取
        domain = urlparse(url).netloc
        # 移除 www. 和常见前缀
        domain = re.sub(r'^(www\.|ir\.|investor\.)', '', domain)
        # 提取主域名
        parts = domain.split('.')
        if parts:
            return parts[0].capitalize()
        return "Unknown"
    
    return title


async def analyze_page(url: str, max_scrolls: int = 5) -> tuple[list[FileInfo], str]:
    """
    分析 IR 网页，提取文件链接和公司名称
    
    Args:
        url: IR 网页 URL
        max_scrolls: 最大滚动次数
        
    Returns:
        (文件信息列表, 公司名称)
    """
    from playwright.async_api import async_playwright

    files = []
    seen_urls = set()
    company_name = "Unknown"

    print(f"🌐 正在分析: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            # 加载页面
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)  # 等待动态内容

            # 提取页面标题和公司名称
            page_title = await page.title()
            company_name = extract_company_name(page_title, url)
            print(f"🏢 公司名称: {company_name}")

            # 滚动加载更多内容
            for i in range(max_scrolls):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(1)

            # 提取所有链接
            links = await page.eval_on_selector_all("a[href]", """
                (elements) => elements.map(el => ({
                    href: el.href,
                    title: el.textContent.trim(),
                    download: el.download
                }))
            """)

            print(f"📋 找到 {len(links)} 个链接")

            for link in links:
                href = link.get("href", "")
                link_text = link.get("title", "")

                # 检查是否是文件链接
                parsed = urlparse(href)
                ext = Path(parsed.path).suffix.lower()

                if ext in SUPPORTED_EXTENSIONS:
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)

                    # 分类文件
                    file_type = classify_file(href, link_text)
                    filename = link.get("download") or extract_filename(href)
                    
                    # 生成显示名称
                    display_name = generate_display_name(href, link_text, filename)

                    files.append(FileInfo(
                        url=href,
                        filename=filename,
                        display_name=display_name,
                        file_type=file_type,
                        extension=ext,
                        title=link_text
                    ))

            print(f"✅ 识别到 {len(files)} 个文件")

        except Exception as e:
            print(f"❌ 分析失败: {e}")
        finally:
            await browser.close()

    return files, company_name


def group_by_type(files: list[FileInfo]) -> dict[str, list[FileInfo]]:
    """按类型分组文件"""
    groups = {}
    for f in files:
        if f.file_type not in groups:
            groups[f.file_type] = []
        groups[f.file_type].append(f)
    return groups


def sort_by_priority(files: list[FileInfo]) -> list[FileInfo]:
    """按优先级排序文件"""
    priority_order = {
        "annual": 0,
        "quarterly": 1,
        "presentation": 2,
        "transcript": 3,
        "announcement": 4,
        "esg": 5,
        "other": 6
    }
    return sorted(files, key=lambda f: priority_order.get(f.file_type, 6))


if __name__ == "__main__":
    # 测试
    async def test():
        files, company = await analyze_page("https://investor.apple.com")
        print(f"\n公司: {company}")
        for f in sort_by_priority(files)[:10]:
            print(f"[{f.file_type}] {f.display_name} -> {f.url[:60]}...")

    asyncio.run(test())