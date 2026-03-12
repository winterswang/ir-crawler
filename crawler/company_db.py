"""
公司数据库 - 内置知名公司 IR 网址，提高搜索准确性
"""

# 常见公司 IR 网址预设
COMPANY_IR_DATABASE = {
    # 港股
    "腾讯": {
        "names": ["腾讯", "腾讯控股", "Tencent", "00700", "00700.HK"],
        "ir_url": "https://www.tencent.com/en-us/investors.html",
        "company_name": "Tencent Holdings Limited",
        "market": "HK"
    },
    "阿里巴巴": {
        "names": ["阿里巴巴", "阿里", "Alibaba", "BABA", "09988", "09988.HK"],
        "ir_url": "https://investor.alibabagroup.com",
        "company_name": "Alibaba Group Holding Limited",
        "market": "US/HK"
    },
    "美团": {
        "names": ["美团", "Meituan", "03690", "03690.HK"],
        "ir_url": "https://ir.meituan.com",
        "company_name": "Meituan",
        "market": "HK"
    },
    "小米": {
        "names": ["小米", "Xiaomi", "01810", "01810.HK"],
        "ir_url": "https://ir.mi.com",
        "company_name": "Xiaomi Corporation",
        "market": "HK"
    },
    "京东": {
        "names": ["京东", "JD", "JD.com", "09618", "09618.HK"],
        "ir_url": "https://ir.jd.com",
        "company_name": "JD.com, Inc.",
        "market": "US/HK"
    },
    "网易": {
        "names": ["网易", "NetEase", "NTES", "09999", "09999.HK"],
        "ir_url": "https://ir.netease.com",
        "company_name": "NetEase, Inc.",
        "market": "US/HK"
    },
    "百度": {
        "names": ["百度", "Baidu", "BIDU", "09888", "09888.HK"],
        "ir_url": "https://ir.baidu.com",
        "company_name": "Baidu, Inc.",
        "market": "US/HK"
    },
    "快手": {
        "names": ["快手", "Kuaishou", "01024", "01024.HK"],
        "ir_url": "https://ir.kuaishou.com",
        "company_name": "Kuaishou Technology",
        "market": "HK"
    },
    "哔哩哔哩": {
        "names": ["哔哩哔哩", "B站", "Bilibili", "BILI", "09626", "09626.HK"],
        "ir_url": "https://ir.bilibili.com",
        "company_name": "Bilibili Inc.",
        "market": "US/HK"
    },
    "拼多多": {
        "names": ["拼多多", "PDD", "Pinduoduo"],
        "ir_url": "https://investor.pddholdings.com",
        "company_name": "PDD Holdings Inc.",
        "market": "US"
    },
    
    # 瑞幸咖啡
    "瑞幸咖啡": {
        "names": ["瑞幸咖啡", "瑞幸", "Luckin Coffee", "LKNCY"],
        "ir_url": "https://investor.luckincoffee.com",
        "company_name": "Luckin Coffee Inc.",
        "market": "US"
    },
    
    # 迈瑞医疗
    "迈瑞医疗": {
        "names": ["迈瑞医疗", "迈瑞", "Mindray", "300760"],
        "ir_url": "https://www.mindray.com/cn/investor.html",
        "company_name": "深圳迈瑞生物医疗电子股份有限公司",
        "market": "CN"
    },
    
    # 任天堂
    "任天堂": {
        "names": ["任天堂", "Nintendo", "7974", "NTDOY"],
        "ir_url": "https://www.nintendo.co.jp/ir/en/",
        "company_name": "Nintendo Co., Ltd.",
        "market": "JP"
    },
    
    # 美股
    "苹果": {
        "names": ["苹果", "Apple", "AAPL"],
        "ir_url": "https://investor.apple.com",
        "company_name": "Apple Inc.",
        "market": "US"
    },
    "微软": {
        "names": ["微软", "Microsoft", "MSFT"],
        "ir_url": "https://www.microsoft.com/en-us/investor",
        "company_name": "Microsoft Corporation",
        "market": "US"
    },
    "谷歌": {
        "names": ["谷歌", "Google", "GOOGL", "GOOG", "Alphabet"],
        "ir_url": "https://abc.xyz/investor",
        "company_name": "Alphabet Inc.",
        "market": "US"
    },
    "亚马逊": {
        "names": ["亚马逊", "Amazon", "AMZN"],
        "ir_url": "https://ir.aboutamazon.com",
        "company_name": "Amazon.com, Inc.",
        "market": "US"
    },
    "特斯拉": {
        "names": ["特斯拉", "Tesla", "TSLA"],
        "ir_url": "https://ir.tesla.com",
        "company_name": "Tesla, Inc.",
        "market": "US"
    },
    "英伟达": {
        "names": ["英伟达", "NVIDIA", "NVDA"],
        "ir_url": "https://investor.nvidia.com",
        "company_name": "NVIDIA Corporation",
        "market": "US"
    },
    "Meta": {
        "names": ["Meta", "Facebook", "FB", "META"],
        "ir_url": "https://investor.fb.com/",
        "company_name": "Meta Platforms, Inc.",
        "market": "US"
    },
    "奈飞": {
        "names": ["奈飞", "Netflix", "NFLX"],
        "ir_url": "https://ir.netflix.net",
        "company_name": "Netflix, Inc.",
        "market": "US"
    },
    
    # A股
    "贵州茅台": {
        "names": ["茅台", "贵州茅台", "600519"],
        "ir_url": "https://www.moutai.com.cn/ir/index.shtml",
        "company_name": "贵州茅台酒股份有限公司",
        "market": "CN"
    },
    "中国平安": {
        "names": ["平安", "中国平安", "601318"],
        "ir_url": "https://www.pingan.cn/ir/index.shtml",
        "company_name": "Ping An Insurance",
        "market": "CN/HK"
    },
    "招商银行": {
        "names": ["招行", "招商银行", "600036"],
        "ir_url": "https://www.cmbchina.com/investor",
        "company_name": "China Merchants Bank",
        "market": "CN/HK"
    },
}


def lookup_company(query: str) -> dict:
    """
    查询公司 IR 信息
    
    Args:
        query: 公司名/股票代码/别名
        
    Returns:
        公司信息字典，未找到返回 None
    """
    query_normalized = query.strip().upper()
    
    for company_key, info in COMPANY_IR_DATABASE.items():
        # 检查所有别名
        for name in info["names"]:
            if name.upper() == query_normalized or query_normalized in name.upper():
                return {
                    "company_key": company_key,
                    "company_name": info["company_name"],
                    "ir_url": info["ir_url"],
                    "market": info["market"],
                    "source": "database"
                }
    
    return None


def get_all_companies() -> list:
    """获取所有预设公司列表"""
    return [
        {
            "key": key,
            "name": info["company_name"],
            "market": info["market"],
            "ir_url": info["ir_url"]
        }
        for key, info in COMPANY_IR_DATABASE.items()
    ]


if __name__ == "__main__":
    # 测试
    test_queries = ["腾讯", "AAPL", "阿里巴巴", "茅台", "不存在"]
    for q in test_queries:
        result = lookup_company(q)
        if result:
            print(f"✅ {q} → {result['company_name']} ({result['market']})")
        else:
            print(f"❌ {q} 未找到")