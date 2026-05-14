import re
from bs4 import BeautifulSoup
from utils.request_utils import fetch
from utils.validators import normalize_standard_code
from utils.standard_metadata import enrich_standard_record
from processors.pdf_processor import download_pdf, extract_text_from_pdf
from processors.summary_generator import generate_summary, extract_section_titles
from output.yaml_generator import generate_yaml
from config import JEDEC_BASE_URL, JEDEC_SEARCH_URL, OUTPUT_DIR

# 预定义需要采集的JEDEC标准列表（可扩充）
JEDEC_STD_LIST = [
    "JESD22-A104", "JESD22-A114", "JESD22-A115", "JESD22-A110",
    "JESD22-B101", "JESD22-C101", "JESD51", "JESD209"
]

def crawl_jedec_standards(std_list=JEDEC_STD_LIST):
    for std_code in std_list:
        # 搜索
        params = {'keys': std_code}
        resp = fetch(JEDEC_SEARCH_URL, params=params)
        if not resp:
            continue
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 找到搜索结果中的详情链接
        link = soup.select_one('a[href*="/standards-documents/results/"]')
        if not link:
            continue
        detail_url = JEDEC_BASE_URL + link.get('href')
        detail_resp = fetch(detail_url)
        if not detail_resp:
            continue
        detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
        # 寻找PDF下载链接（通常是 a[href$=".pdf"]）
        pdf_link = detail_soup.select_one('a[href$=".pdf"]')
        if not pdf_link:
            print(f"未找到PDF: {std_code}")
            continue
        pdf_url = pdf_link.get('href')
        if not pdf_url.startswith('http'):
            pdf_url = JEDEC_BASE_URL + pdf_url
        filename = f"{normalize_standard_code(std_code)}.pdf"
        pdf_path = download_pdf(pdf_url, filename)
        if not pdf_path:
            continue
        pdf_text = extract_text_from_pdf(pdf_path)
        if not pdf_text:
            continue
        # 提取英文摘要和章节
        summary_en = generate_summary(pdf_text, 'en')
        section = extract_section_titles(pdf_text)
        # 获取标准名称（从页面title）
        title_tag = detail_soup.find('title')
        std_name_en = title_tag.text.strip() if title_tag else std_code
        yaml_data = enrich_standard_record({
            "standard_code": std_code,
            "standard_name": std_name_en,
            "section": section,
            "summary": summary_en,
            "tags": "JEDEC标准",
            "related_process": ""
        }, default_related_process="元器件存储,焊接")
        generate_yaml(yaml_data, OUTPUT_DIR)
        print(f"已处理 JEDEC: {std_code}")
