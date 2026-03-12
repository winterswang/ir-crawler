"""
网页分析模块 - 使用 Playwright 分析 IR 网页，提取文件链接
"""

import re
import asyncio
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from urllib.parse import urljoin, urlparse


@dataclass
class FileInfo:
    """文件信息"""
    url: str
    filename: str
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
    ],
    "quarterly": [
        r"quarterly",
        r"季报",
        r"10-Q",
        r"quarterly\s*report",
        r"季度报告",
        r"earnings\s*release",
    ],
    "presentation": [
        r"investor\s*presentation",
        r"investor\s*deck",
        r"演示文稿",
        r"路演",
        r"presentation",
        r"slides?",
    ],
    "transcript": [
        r"transcript",
        r"电话会议",
        r"earnings\s*call",
        r"会议纪要",
    ],
    "announcement": [
        r"announcement",
        r"公告",
        r"notice",
        r"新闻稿",
        r"press\s*release",
    ],
    "esg": [
        r"esg",
        r"sustainability",
        r"社会责任",
        r"可持续发展",
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


async def analyze_page(url: str, max_scrolls: int = 5) -> list[FileInfo]:
    """
    分析 IR 网页，提取文件链接

    Args:
        url: IR 网页 URL
        max_scrolls: 最大滚动次数

    Returns:
        文件信息列表
    """
    from playwright.async_api import async_playwright

    files = []
    seen_urls = set()

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
                title = link.get("title", "")

                # 检查是否是文件链接
                parsed = urlparse(href)
                ext = Path(parsed.path).suffix.lower()

                if ext in SUPPORTED_EXTENSIONS:
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)

                    # 分类文件
                    file_type = classify_file(href, title)
                    filename = link.get("download") or extract_filename(href)

                    files.append(FileInfo(
                        url=href,
                        filename=filename,
                        file_type=file_type,
                        extension=ext,
                        title=title
                    ))

            print(f"✅ 识别到 {len(files)} 个文件")

        except Exception as e:
            print(f"❌ 分析失败: {e}")
        finally:
            await browser.close()

    return files


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
        files = await analyze_page("https://www.tencent.com/en-us/investors.html")
        for f in sort_by_priority(files)[:10]:
            print(f"[{f.file_type}] {f.filename} -> {f.url[:60]}...")

    asyncio.run(test())