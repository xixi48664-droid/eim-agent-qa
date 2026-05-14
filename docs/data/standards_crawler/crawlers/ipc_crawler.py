from bs4 import BeautifulSoup
from utils.request_utils import fetch
from utils.standard_metadata import enrich_standard_record
from output.yaml_generator import generate_yaml
from config import IPC_CATALOG_URL, OUTPUT_DIR

def crawl_ipc_catalog():
    """爬取IPC标准目录，仅生成不含summary的YAML"""
    resp = fetch(IPC_CATALOG_URL)
    if not resp:
        return
    soup = BeautifulSoup(resp.text, 'html.parser')
    # 根据实际页面结构找到标准列表（示例选择器）
    std_items = soup.select('.standards-list li')
    for item in std_items:
        link = item.find('a')
        if not link:
            continue
        std_code = link.text.strip()
        if not std_code.startswith('IPC-'):
            continue
        std_name = item.find('span', class_='title')
        std_name = std_name.text.strip() if std_name else ""
        yaml_data = enrich_standard_record({
            "standard_code": std_code,
            "standard_name": std_name,
            "section": "",
            "summary": "IPC 官网目录元数据，未包含付费标准正文；需按模板补充章节摘要。",
            "tags": "IPC标准",
            "related_process": ""
        }, default_related_process="电子制造")
        generate_yaml(yaml_data, OUTPUT_DIR)
        print(f"已生成IPC元数据: {std_code}")
