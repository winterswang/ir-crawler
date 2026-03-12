#!/usr/bin/env python3
"""
验证预设公司IR链接 - 使用阿里云百炼搜索
"""

import os
import json
import time
from pathlib import Path

# 加载环境变量
from dotenv import load_dotenv
load_dotenv('/root/.openclaw/workspace/deer-flow-analysis/backend/.env')

import dashscope
from dashscope import Generation

# 设置API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# 导入公司数据库
import sys
sys.path.insert(0, str(Path(__file__).parent))
from crawler.company_db import COMPANY_IR_DATABASE


def verify_ir_url(company_name: str, ir_url: str) -> dict:
    """
    使用百炼搜索验证IR链接是否正确
    
    Returns:
        {
            "valid": bool,
            "correct_url": str or None,
            "reason": str
        }
    """
    prompt = f"""请验证以下公司的投资者关系(IR)网页链接是否正确。

公司名称: {company_name}
提供的IR链接: {ir_url}

请检查：
1. 这个链接是否是该公司的官方投资者关系页面？
2. 如果不正确，请提供正确的IR链接。

请以JSON格式回复：
{{
    "is_correct": true/false,
    "correct_url": "正确的URL（如果原链接错误）",
    "reason": "判断理由"
}}
"""
    
    try:
        response = Generation.call(
            model='qwen-plus',
            prompt=prompt,
            result_format='message',
            enable_search=True,  # 启用搜索
            search_options={
                "enable_source": True,
                "search_strategy": "standard"
            }
        )
        
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            
            # 尝试解析JSON
            try:
                # 提取JSON部分
                json_match = content[content.find('{'):content.rfind('}')+1]
                result = json.loads(json_match)
                return {
                    "valid": result.get("is_correct", False),
                    "correct_url": result.get("correct_url"),
                    "reason": result.get("reason", ""),
                    "raw_response": content
                }
            except:
                return {
                    "valid": None,
                    "correct_url": None,
                    "reason": "无法解析响应",
                    "raw_response": content
                }
        else:
            return {
                "valid": None,
                "correct_url": None,
                "reason": f"API错误: {response.code} - {response.message}",
                "raw_response": None
            }
            
    except Exception as e:
        return {
            "valid": None,
            "correct_url": None,
            "reason": str(e),
            "raw_response": None
        }


def main():
    """验证所有预设公司的IR链接"""
    print("=" * 60)
    print("验证预设公司IR链接")
    print("=" * 60)
    
    results = []
    
    for company_key, info in COMPANY_IR_DATABASE.items():
        company_name = info["company_name"]
        ir_url = info["ir_url"]
        market = info["market"]
        
        print(f"\n🔍 验证: {company_name} ({market})")
        print(f"   链接: {ir_url}")
        
        result = verify_ir_url(company_name, ir_url)
        
        status = "✅" if result["valid"] else "❌" if result["valid"] is False else "⚠️"
        print(f"   状态: {status} {result['reason']}")
        
        if result.get("correct_url"):
            print(f"   正确链接: {result['correct_url']}")
        
        results.append({
            "company": company_name,
            "market": market,
            "original_url": ir_url,
            "is_valid": result["valid"],
            "correct_url": result.get("correct_url"),
            "reason": result["reason"]
        })
        
        # 避免API限流
        time.sleep(2)
    
    # 输出汇总
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    valid_count = sum(1 for r in results if r["is_valid"] == True)
    invalid_count = sum(1 for r in results if r["is_valid"] == False)
    unknown_count = sum(1 for r in results if r["is_valid"] is None)
    
    print(f"\n✅ 正确: {valid_count}")
    print(f"❌ 错误: {invalid_count}")
    print(f"⚠️ 未知: {unknown_count}")
    
    # 输出需要修正的
    if invalid_count > 0:
        print("\n需要修正的链接:")
        for r in results:
            if r["is_valid"] == False:
                print(f"  - {r['company']}: {r['original_url']}")
                if r.get("correct_url"):
                    print(f"    → {r['correct_url']}")
    
    # 保存结果
    output_file = Path(__file__).parent / "ir_verification_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {output_file}")


if __name__ == "__main__":
    main()