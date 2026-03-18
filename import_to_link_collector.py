#!/usr/bin/env python3
"""
IR-Crawler 文件导入脚本

将下载的 IR 文件（年报、季报等）导入到 Link-Collector 知识库
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent / "link-collector"))

from link_collector import CollectorService


def parse_filename(filename: str) -> dict:
    """
    解析文件名
    
    示例: TencentHoldingsLimited_Annual_2024.pdf
    返回: {"company": "Tencent Holdings Limited", "type": "Annual", "year": "2024"}
    """
    parts = filename.replace('.pdf', '').replace('.xlsx', '').replace('.pptx', '').split('_')
    
    result = {
        "company": "",
        "type": "",
        "year": ""
    }
    
    if len(parts) >= 3:
        # 公司名称（可能包含空格）
        result["company"] = parts[0].replace('Limited', ' Limited').replace('Inc', ' Inc').strip()
        result["type"] = parts[1]  # Annual, Quarterly, etc.
        result["year"] = parts[2] if len(parts) > 2 else ""
    
    return result


def get_file_type_name(file_type: str) -> str:
    """获取文件类型的中文名称"""
    type_map = {
        "annual": "年报",
        "quarterly": "季报",
        "presentation": "演示文稿",
        "transcript": "电话会议纪要",
        "esg": "ESG报告",
        "proxy": "委托声明书"
    }
    return type_map.get(file_type.lower(), file_type)


def import_ir_files(ir_downloads_dir: Path, service: CollectorService, 
                     company: str = None, limit: int = None):
    """
    导入 IR 文件到 Link-Collector
    
    Args:
        ir_downloads_dir: IR 下载目录
        service: Link-Collector 服务
        company: 只导入指定公司的文件
        limit: 限制导入数量
    """
    # 扫描所有文件
    all_files = []
    
    for company_dir in ir_downloads_dir.iterdir():
        if not company_dir.is_dir():
            continue
        
        company_name = company_dir.name
        
        # 如果指定了公司，只处理该公司
        if company and company.lower() not in company_name.lower():
            continue
        
        for file_type_dir in company_dir.iterdir():
            if not file_type_dir.is_dir():
                continue
            
            file_type = file_type_dir.name
            
            for file_path in file_type_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.xlsx', '.pptx']:
                    all_files.append({
                        "path": file_path,
                        "company": company_name,
                        "file_type": file_type
                    })
    
    print(f"📚 发现 {len(all_files)} 个 IR 文件")
    
    if limit:
        all_files = all_files[:limit]
        print(f"📋 限制模式：导入 {limit} 个文件")
    
    success_count = 0
    error_count = 0
    
    for i, file_info in enumerate(all_files, 1):
        file_path = file_info["path"]
        company_name = file_info["company"]
        file_type = file_info["file_type"]
        
        # 解析文件名
        parsed = parse_filename(file_path.name)
        
        # 构建标题
        type_name = get_file_type_name(file_type)
        year = parsed.get("year", "")
        title = f"{company_name} {type_name}"
        if year:
            title += f" {year}"
        
        print(f"  [{i}] 导入: {title}")
        
        try:
            result = service.process_file(
                str(file_path),
                options={
                    "category": "investment",
                    "sub_category": "research-reports",
                    "tags": [company_name, type_name, "IR文件"],
                    "save_to": str(ir_downloads_dir),  # 同时保存到原目录
                    "author": company_name,  # 设置作者为公司名称
                }
            )
            
            if result.get("success"):
                success_count += 1
            else:
                print(f"      ❌ 失败: {result.get('error', '未知错误')}")
                error_count += 1
                
        except Exception as e:
            print(f"      ❌ 异常: {e}")
            error_count += 1
    
    print(f"\n📊 导入完成:")
    print(f"  成功: {success_count} 个")
    print(f"  失败: {error_count} 个")
    
    return success_count, error_count


def main():
    # IR 下载目录
    ir_downloads_dir = Path("/root/.openclaw/workspace/ir-crawler/downloads")
    
    # Link-Collector 服务
    service = CollectorService()
    
    # 检查参数
    company = None
    limit = None
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--test":
            limit = 3
            print("🧪 测试模式：仅导入 3 个文件\n")
        elif arg == "--all":
            print("📦 全量模式：导入所有文件\n")
        elif arg.startswith("--company="):
            company = arg.split("=")[1]
            print(f"🏢 公司模式：只导入 {company} 的文件\n")
        elif arg.isdigit():
            limit = int(arg)
            print(f"📋 限制模式：导入 {limit} 个文件\n")
    
    # 执行导入
    import_ir_files(ir_downloads_dir, service, company, limit)


if __name__ == "__main__":
    main()