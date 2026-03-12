---
name: ir-crawler
description: 上市公司IR网页爬取工具 - 自动搜索、分析、下载投资者关系文件（年报、季报、演示文稿等）
version: 1.0.0
author: winterswang
triggers:
  - pattern: "爬取IR"
    command: "python3 /root/.openclaw/workspace/ir-crawler/skill.py"
  - pattern: "IR文件"
    command: "python3 /root/.openclaw/workspace/ir-crawler/skill.py"
  - pattern: "下载财报"
    command: "python3 /root/.openclaw/workspace/ir-crawler/skill.py"
---

# IR Crawler Skill

上市公司投资者关系(IR)网页爬取工具。

## 功能

| 功能 | 说明 |
|------|------|
| IR搜索 | Tavily搜索公司IR主页 |
| 本地缓存 | 缓存公司→IR网址映射 |
| 网页分析 | Playwright解析文件链接（支持滚动） |
| 文件下载 | 异步下载PDF/XLSX/PPT等 |
| 清单生成 | Markdown格式文件列表 |

## 使用方式

```
爬取IR 腾讯控股
IR文件 AAPL
下载财报 https://investor.apple.com
```

## 文件优先级

| 优先级 | 类型 |
|--------|------|
| P0 | 年报、季报 |
| P1 | 投资者演示、电话会议纪要 |
| P2 | 公告、ESG报告 |

## 目录结构

```
ir-crawler/
├── skill.py              # Skill 入口
├── crawler/
│   ├── search.py         # Tavily IR搜索
│   ├── analyzer.py       # Playwright 网页分析
│   ├── downloader.py     # 文件下载
│   └── manifest.py       # 清单生成
├── cache/
│   └── ir_mapping.json   # 公司→IR网址缓存
├── downloads/            # 下载文件
└── manifests/            # 文件清单
```