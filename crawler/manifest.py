"""
清单生成模块 - 生成 Markdown 格式的文件清单
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .downloader import DownloadResult
from .analyzer import FileInfo


# 清单目录
MANIFEST_DIR = Path(__file__).parent.parent / "manifests"

# 类型显示名称
TYPE_NAMES = {
    "annual": "年报",
    "quarterly": "季报",
    "presentation": "演示文稿",
    "transcript": "会议纪要",
    "announcement": "公告",
    "esg": "ESG报告",
    "other": "其他"
}


def format_size(size: int) -> str:
    """格式化文件大小"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / 1024 / 1024:.2f} MB"


def generate_manifest(
    company: str,
    ir_url: str,
    results: list[DownloadResult],
    company_name: Optional[str] = None
) -> str:
    """
    生成 Markdown 清单

    Args:
        company: 公司标识
        ir_url: IR 网页 URL
        results: 下载结果列表
        company_name: 公司名称

    Returns:
        清单文件路径
    """
    # 按类型分组
    grouped = {}
    for r in results:
        if r.success:
            file_type = r.file_info.file_type
            if file_type not in grouped:
                grouped[file_type] = []
            grouped[file_type].append(r)

    # 生成 Markdown
    lines = [
        f"# {company_name or company} - IR文件清单",
        "",
        f"**爬取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**IR网址**: {ir_url}",
        ""
    ]

    # 按类型输出
    type_order = ["annual", "quarterly", "presentation", "transcript", "announcement", "esg", "other"]

    for file_type in type_order:
        if file_type not in grouped:
            continue

        files = grouped[file_type]
        type_name = TYPE_NAMES.get(file_type, "其他")

        lines.append(f"## {type_name} ({len(files)} 文件)")
        lines.append("")
        lines.append("| 文件名 | 大小 |")
        lines.append("|--------|------|")

        for r in sorted(files, key=lambda x: x.file_info.filename, reverse=True):
            size_str = format_size(r.size)
            # 相对路径
            rel_path = Path(r.local_path).relative_to(
                Path(__file__).parent.parent / "downloads"
            ) if r.local_path else ""
            lines.append(f"| [{r.file_info.filename}](../downloads/{rel_path}) | {size_str} |")

        lines.append("")

    # 统计信息
    total_files = sum(len(v) for v in grouped.values())
    total_size = sum(r.size for v in grouped.values() for r in v)

    lines.extend([
        "---",
        "",
        "## 统计",
        "",
        f"- 总文件数: {total_files}",
        f"- 总大小: {format_size(total_size)}",
        f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ])

    # 保存文件
    manifest_path = MANIFEST_DIR / f"{company}.md"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"📝 清单已保存: {manifest_path}")

    return str(manifest_path)


if __name__ == "__main__":
    # 测试
    from .analyzer import FileInfo

    test_results = [
        DownloadResult(
            file_info=FileInfo(
                url="https://example.com/report2024.pdf",
                filename="2024_annual_report.pdf",
                file_type="annual",
                extension=".pdf"
            ),
            success=True,
            local_path="/tmp/test/2024_annual_report.pdf",
            size=15 * 1024 * 1024
        ),
        DownloadResult(
            file_info=FileInfo(
                url="https://example.com/q3.pdf",
                filename="Q3_2024_report.pdf",
                file_type="quarterly",
                extension=".pdf"
            ),
            success=True,
            local_path="/tmp/test/Q3_2024_report.pdf",
            size=5 * 1024 * 1024
        )
    ]

    path = generate_manifest("test_company", "https://example.com/ir", test_results, "Test Company")
    print(f"生成清单: {path}")