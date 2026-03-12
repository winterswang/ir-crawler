"""
网站特定解析规则
为不同IR网站添加定制化的文件提取逻辑
"""

import re
import json
import asyncio
from typing import Optional
from playwright.async_api import async_playwright


class SiteParser:
    """网站解析基类"""
    
    def __init__(self, url: str):
        self.url = url
    
    async def parse(self) -> list:
        """解析页面，返回文件列表"""
        raise NotImplementedError


class AlibabaParser(SiteParser):
    """阿里巴巴IR解析器"""
    
    async def parse(self) -> list:
        """通过拦截API请求获取文件列表"""
        files = []
        
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()
            
            # 存储API响应
            api_responses = []
            
            async def handle_response(response):
                url = response.url
                if 'data.alibabagroup.com' in url and '.json' in url:
                    try:
                        data = await response.json()
                        api_responses.append({'url': url, 'data': data})
                    except Exception as e:
                        pass
            
            page.on('response', handle_response)
            
            try:
                await page.goto(self.url, timeout=60000)
                await asyncio.sleep(3)
                
                # 滚动加载
                for _ in range(5):
                    await page.evaluate('window.scrollBy(0, 500)')
                    await asyncio.sleep(0.5)
                
                # 从API数据中提取文件
                for api in api_responses:
                    data = api.get('data', {})
                    
                    # 尝试不同的数据结构
                    content = data.get('content', data)
                    
                    # 查找包含文件列表的字段
                    for key in ['list', 'items', 'reports', 'earnings', 'financials']:
                        if key in content:
                            items = content[key]
                            if isinstance(items, list):
                                for item in items:
                                    file_info = self._extract_file(item)
                                    if file_info:
                                        files.append(file_info)
                
                # 如果没找到，尝试从页面提取
                if not files:
                    files = await self._extract_from_page(page)
                    
            except Exception as e:
                print(f"解析错误: {e}")
            finally:
                await browser.close()
        
        return files
    
    def _extract_file(self, item: dict) -> Optional[dict]:
        """从API数据项提取文件信息"""
        # 查找PDF URL
        url_fields = ['pdfUrl', 'url', 'fileUrl', 'downloadUrl', 'link']
        file_url = None
        
        for field in url_fields:
            if field in item and item[field]:
                file_url = item[field]
                break
        
        if not file_url:
            return None
        
        # 补全URL
        if not file_url.startswith('http'):
            file_url = 'https://www.alibabagroup.com' + file_url
        
        return {
            'url': file_url,
            'title': item.get('title', item.get('name', '')),
            'date': item.get('date', item.get('publishDate', '')),
            'type': self._classify_file(file_url, item.get('title', '')),
            'filename': self._extract_filename(file_url)
        }
    
    async def _extract_from_page(self, page) -> list:
        """从页面元素直接提取"""
        files = []
        
        # 获取所有链接
        links = await page.eval_on_selector_all('a[href]', '''
            (elements) => elements.map(el => ({
                href: el.href,
                text: el.textContent.trim()
            }))
        ''')
        
        # 筛选文件链接
        for link in links:
            href = link['href']
            if any(ext in href.lower() for ext in ['.pdf', '.xlsx', '.ppt']):
                files.append({
                    'url': href,
                    'title': link['text'],
                    'date': '',
                    'type': self._classify_file(href, link['text']),
                    'filename': self._extract_filename(href)
                })
        
        return files
    
    def _classify_file(self, url: str, title: str) -> str:
        """分类文件类型"""
        text = f"{url} {title}".lower()
        
        if any(kw in text for kw in ['annual', '年报', '20-f', '10-k']):
            return 'annual'
        elif any(kw in text for kw in ['quarterly', '季报', '10-q', 'q1', 'q2', 'q3', 'q4']):
            return 'quarterly'
        elif any(kw in text for kw in ['presentation', '演示', 'slides']):
            return 'presentation'
        elif any(kw in text for kw in ['transcript', '会议纪要']):
            return 'transcript'
        return 'other'
    
    def _extract_filename(self, url: str) -> str:
        """从URL提取文件名"""
        from urllib.parse import urlparse
        from pathlib import Path
        return Path(urlparse(url).path).name or 'unknown'


class XiaomiParser(SiteParser):
    """小米IR解析器 - 需要访问子页面"""
    
    SUBPAGES = [
        '/financial-information/annual-interim-reports',
        '/financial-information/sec-filings',
        '/financial-reports',
    ]
    
    async def parse(self) -> list:
        """爬取子页面获取文件"""
        files = []
        
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            
            for subpath in self.SUBPAGES:
                subpage_url = self.url.rstrip('/') + subpath
                print(f"  检查子页面: {subpath}")
                
                try:
                    page = await browser.new_page()
                    await page.goto(subpage_url, timeout=30000)
                    await asyncio.sleep(2)
                    
                    # 滚动
                    for _ in range(5):
                        await page.evaluate('window.scrollBy(0, 500)')
                        await asyncio.sleep(0.3)
                    
                    # 提取链接
                    links = await page.eval_on_selector_all('a[href]', '''
                        (elements) => elements.map(el => ({
                            href: el.href,
                            text: el.textContent.trim()
                        }))
                    ''')
                    
                    for link in links:
                        href = link['href']
                        if any(ext in href.lower() for ext in ['.pdf', '.xlsx', '.zip']):
                            files.append({
                                'url': href,
                                'title': link['text'][:100],
                                'date': '',
                                'type': self._classify_file(href, link['text']),
                                'filename': self._extract_filename(href)
                            })
                    
                    await page.close()
                    
                except Exception as e:
                    print(f"  子页面错误: {str(e)[:50]}")
                
                await asyncio.sleep(1)
            
            await browser.close()
        
        return files
    
    def _classify_file(self, url: str, title: str) -> str:
        text = f"{url} {title}".lower()
        if any(kw in text for kw in ['annual', '年报']):
            return 'annual'
        elif any(kw in text for kw in ['quarterly', '季报', 'interim']):
            return 'quarterly'
        return 'other'
    
    def _extract_filename(self, url: str) -> str:
        from urllib.parse import urlparse
        from pathlib import Path
        return Path(urlparse(url).path).name or 'unknown'


class PDDParser(SiteParser):
    """拼多多IR解析器"""
    
    SUBPAGES = [
        '/financial-information/sec-filings',
        '/financial-information/quarterly-results',
    ]
    
    async def parse(self) -> list:
        """爬取子页面"""
        files = []
        
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            
            for subpath in self.SUBPAGES:
                subpage_url = self.url.rstrip('/') + subpath
                
                try:
                    page = await browser.new_page()
                    await page.goto(subpage_url, timeout=30000)
                    await asyncio.sleep(2)
                    
                    # 滚动
                    for _ in range(5):
                        await page.evaluate('window.scrollBy(0, 500)')
                        await asyncio.sleep(0.3)
                    
                    # 提取链接
                    links = await page.eval_on_selector_all('a[href]', '''
                        (elements) => elements.map(el => ({
                            href: el.href,
                            text: el.textContent.trim()
                        }))
                    ''')
                    
                    for link in links:
                        href = link['href']
                        if any(ext in href.lower() for ext in ['.pdf', '.xlsx']):
                            files.append({
                                'url': href,
                                'title': link['text'][:100],
                                'date': '',
                                'type': 'filing',
                                'filename': self._extract_filename(href)
                            })
                    
                    await page.close()
                    
                except Exception as e:
                    pass
                
                await asyncio.sleep(1)
            
            await browser.close()
        
        return files
    
    def _extract_filename(self, url: str) -> str:
        from urllib.parse import urlparse
        from pathlib import Path
        return Path(urlparse(url).path).name or 'unknown'


# 解析器注册表
PARSERS = {
    'alibabagroup.com': AlibabaParser,
    'ir.mi.com': XiaomiParser,
    'investor.pddholdings.com': PDDParser,
    'ir.meituan.com': XiaomiParser,  # 美团结构类似
    'investor.luckincoffee.com': XiaomiParser,  # 瑞幸结构类似
}


def get_parser(url: str) -> Optional[SiteParser]:
    """根据URL获取对应的解析器"""
    for domain, parser_class in PARSERS.items():
        if domain in url:
            return parser_class(url)
    return None


async def parse_dynamic_site(url: str) -> list:
    """
    解析动态加载的IR网站
    
    Returns:
        [{"url": str, "title": str, "date": str, "type": str, "filename": str}, ...]
    """
    parser = get_parser(url)
    
    if parser:
        print(f"📖 使用专用解析器: {parser.__class__.__name__}")
        return await parser.parse()
    
    # 默认解析器
    print("📖 使用默认解析器")
    return await default_parse(url)


async def default_parse(url: str) -> list:
    """默认解析逻辑"""
    files = []
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, timeout=60000)
            await asyncio.sleep(3)
            
            # 滚动
            for _ in range(5):
                await page.evaluate('window.scrollBy(0, 500)')
                await asyncio.sleep(0.5)
            
            # 提取链接
            links = await page.eval_on_selector_all('a[href]', '''
                (elements) => elements.map(el => ({
                    href: el.href,
                    text: el.textContent.trim()
                }))
            ''')
            
            for link in links:
                href = link['href']
                if any(ext in href.lower() for ext in ['.pdf', '.xlsx', '.ppt', '.zip']):
                    from urllib.parse import urlparse
                    from pathlib import Path
                    files.append({
                        'url': href,
                        'title': link['text'][:100],
                        'date': '',
                        'type': 'other',
                        'filename': Path(urlparse(href).path).name or 'unknown'
                    })
            
        except Exception as e:
            print(f"解析错误: {e}")
        finally:
            await browser.close()
    
    return files


if __name__ == "__main__":
    # 测试
    async def test():
        test_urls = [
            ('阿里巴巴', 'https://www.alibabagroup.com/en-US/ir-financial-reports-quarterly-results'),
            ('小米', 'https://ir.mi.com'),
            ('拼多多', 'https://investor.pddholdings.com'),
        ]
        
        for name, url in test_urls:
            print(f"\n{'='*60}")
            print(f"测试: {name}")
            print(f"URL: {url}")
            print('='*60)
            
            files = await parse_dynamic_site(url)
            print(f"\n找到 {len(files)} 个文件")
            
            for f in files[:5]:
                print(f"  [{f['type']}] {f['filename'][:50]}")
    
    asyncio.run(test())