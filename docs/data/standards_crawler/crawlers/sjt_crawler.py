import re
from bs4 import BeautifulSoup
from utils.request_utils import fetch
from utils.validators import normalize_standard_code, is_crawled_standard
from utils.standard_metadata import enrich_standard_record
from processors.pdf_processor import download_pdf, extract_text_from_pdf
from processors.summary_generator import generate_summary, extract_section_titles
from output.yaml_generator import generate_yaml
from config import OUTPUT_DIR

def crawl_sjt_standards(keyword="SJ/T", max_pages=5):
    """
    搜索 SJ/T 标准，解析 HTML 结果页
    """
    page = 1
    processed = 0
    base_url = "https://std.samr.gov.cn/search/std"
    
    while page <= max_pages:
        params = {
            "pageNum": page,
            "pageSize": 20,
            "standardType": "hangye",
            "keyword": keyword,
            "icsCode": "31"
        }
        resp = fetch(base_url, params=params, method="GET")  # 改为 GET 请求
        if not resp:
            break
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 查找标准列表容器（根据实际页面结构调整）
        items = soup.select('.std-list-item')  # 需要实际查看网页后修正
        if not items:
            # 尝试备用选择器
            items = soup.select('table tbody tr')
        if not items:
            print(f"第 {page} 页未找到标准列表，停止")
            break
        
        for item in items:
            # 提取标准号
            code_elem = item.select_one('.std-num') or item.select_one('td:nth-child(1)')
            if not code_elem:
                continue
            std_code = code_elem.text.strip()
            if not std_code.startswith("SJ/T"):
                continue
            
            # 检查是否已处理
            if is_crawled_standard(std_code, OUTPUT_DIR):
                print(f"跳过已处理: {std_code}")
                continue
            
            # 提取标准名称
            name_elem = item.select_one('.std-name') or item.select_one('td:nth-child(2)')
            std_name = name_elem.text.strip() if name_elem else ""
            
            # 提取 PDF 链接
            pdf_link = item.select_one('a[href*=".pdf"]')
            if not pdf_link:
                print(f"无PDF {std_code}")
                continue
            pdf_url = pdf_link.get('href')
            if not pdf_url.startswith('http'):
                pdf_url = "https://std.samr.gov.cn" + pdf_url
            
            # 下载并处理 PDF
            filename = f"{normalize_standard_code(std_code)}.pdf"
            pdf_path = download_pdf(pdf_url, filename)
            if not pdf_path:
                continue
            pdf_text = extract_text_from_pdf(pdf_path)
            if not pdf_text:
                continue
            
            summary_zh = generate_summary(pdf_text, 'zh')
            section = extract_section_titles(pdf_text)
            yaml_data = enrich_standard_record({
                "standard_code": std_code,
                "standard_name": std_name,
                "section": section,
                "summary": summary_zh,
                "tags": "SJ/T标准",
                "related_process": ""
            }, default_related_process="电子制造")
            generate_yaml(yaml_data, OUTPUT_DIR)
            processed += 1
            print(f"已处理 SJ/T: {std_code}")
        
        page += 1
    print(f"SJ/T爬取完成，共处理 {processed} 条")
