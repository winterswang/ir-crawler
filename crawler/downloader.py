"""
文件下载模块 - 异步下载 IR 文件
V1.1 优化: 添加重试机制
"""

import asyncio
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
import aiohttp
from urllib.parse import urlparse

from .analyzer import FileInfo


@dataclass
class DownloadResult:
    """下载结果"""
    file_info: FileInfo
    success: bool
    local_path: Optional[str] = None
    error: Optional[str] = None
    size: int = 0


# 下载目录
DOWNLOAD_DIR = Path(__file__).parent.parent / "downloads"


def get_save_path(company: str, file_info: FileInfo) -> Path:
    """获取文件保存路径（使用规范化文件名）"""
    from .analyzer import normalize_filename
    
    # 清理公司名称
    safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-', '_')).strip()
    if not safe_company:
        safe_company = "Unknown"

    # 按类型分目录
    type_dir = {
        "annual": "annual",
        "quarterly": "quarterly",
        "presentation": "presentations",
        "transcript": "transcripts",
        "announcement": "announcements",
        "esg": "esg",
        "other": "other"
    }.get(file_info.file_type, "other")

    save_dir = DOWNLOAD_DIR / safe_company / type_dir
    save_dir.mkdir(parents=True, exist_ok=True)

    # 使用规范化文件名
    normalized_filename = normalize_filename(
        file_info.filename,
        company,
        file_info.file_type,
        file_info.title or ""
    )

    return save_dir / normalized_filename


async def download_file(
    session: aiohttp.ClientSession,
    file_info: FileInfo,
    company: str,
    timeout: int = 120,
    max_retries: int = 3
) -> DownloadResult:
    """下载单个文件（支持重试）"""
    save_path = get_save_path(company, file_info)

    # 如果文件已存在，跳过
    if save_path.exists():
        size = save_path.stat().st_size
        print(f"⏭️ 已存在: {file_info.filename}")
        return DownloadResult(
            file_info=file_info,
            success=True,
            local_path=str(save_path),
            size=size
        )

    last_error = None
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"🔄 重试 {attempt}/{max_retries}: {file_info.filename}")
                await asyncio.sleep(2)  # 重试前等待

            async with session.get(
                file_info.url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            ) as response:
                if response.status == 200:
                    content = await response.read()

                    # 保存文件
                    with open(save_path, "wb") as f:
                        f.write(content)

                    size = len(content)
                    print(f"✅ 下载成功: {file_info.filename} ({size / 1024:.1f} KB)")

                    return DownloadResult(
                        file_info=file_info,
                        success=True,
                        local_path=str(save_path),
                        size=size
                    )
                else:
                    last_error = f"HTTP {response.status}"
                    continue  # 重试

        except asyncio.TimeoutError:
            last_error = "Timeout"
            print(f"⏰ 超时: {file_info.filename} (尝试 {attempt + 1})")
            continue  # 重试
            
        except (aiohttp.ClientError, ConnectionError) as e:
            last_error = str(e)
            print(f"⚠️ 连接错误: {file_info.filename} - {e}")
            continue  # 重试
            
        except Exception as e:
            last_error = str(e)
            print(f"❌ 下载失败: {file_info.filename} - {e}")
            break  # 其他错误不重试

    # 所有重试都失败
    print(f"❌ 下载失败: {file_info.filename} - {last_error}")
    return DownloadResult(
        file_info=file_info,
        success=False,
        error=last_error
    )


async def download_files(
    files: list[FileInfo],
    company: str,
    max_concurrent: int = 3,
    max_files: Optional[int] = None
) -> list[DownloadResult]:
    """
    批量下载文件

    Args:
        files: 文件列表
        company: 公司名称
        max_concurrent: 最大并发数
        max_files: 最大下载数量 (None = 无限制)

    Returns:
        下载结果列表
    """
    from .analyzer import sort_by_priority

    # 按优先级排序
    sorted_files = sort_by_priority(files)

    # 限制下载数量
    if max_files:
        sorted_files = sorted_files[:max_files]

    print(f"📥 准备下载 {len(sorted_files)} 个文件...")

    results = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def download_with_semaphore(session, file_info):
        async with semaphore:
            return await download_file(session, file_info, company)

    async with aiohttp.ClientSession() as session:
        tasks = [download_with_semaphore(session, f) for f in sorted_files]
        results = await asyncio.gather(*tasks)

    # 统计
    success = sum(1 for r in results if r.success)
    total_size = sum(r.size for r in results if r.success)

    print(f"\n📊 下载完成: {success}/{len(results)} 文件, 共 {total_size / 1024 / 1024:.2f} MB")

    return list(results)


if __name__ == "__main__":
    # 测试
    async def test():
        from .analyzer import analyze_page

        files, _ = await analyze_page("https://investor.apple.com")
        if files:
            results = await download_files(files[:3], "Apple")
            for r in results:
                print(f"{'✅' if r.success else '❌'} {r.file_info.filename}")

    asyncio.run(test())