import csv
from utils.validators import normalize_standard_code, is_crawled_standard
from utils.standard_metadata import enrich_standard_record
from output.yaml_generator import generate_yaml
from config import ISO_CSV_PATH, OUTPUT_DIR

def crawl_iso_from_csv():
    """从手动下载的ISO公开CSV读取元数据生成YAML（无PDF）"""
    try:
        with open(ISO_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                std_code = row.get('Reference number', '')
                if not std_code.startswith('ISO'):
                    continue
                if is_crawled_standard(std_code, OUTPUT_DIR):
                    continue
                std_name_en = row.get('Title', '')
                abstract_en = row.get('Abstract', '')[:500]
                yaml_data = enrich_standard_record({
                    "standard_code": std_code,
                    "standard_name": std_name_en,
                    "section": "",
                    "summary": abstract_en if abstract_en else "ISO 官网开放数据元数据，未包含标准正文；需按模板补充章节摘要。",
                    "tags": "ISO标准",
                    "related_process": ""
                }, default_related_process="质量管理")
                generate_yaml(yaml_data, OUTPUT_DIR)
                print(f"已生成ISO元数据: {std_code}")
    except FileNotFoundError:
        print(f"ISO CSV文件未找到: {ISO_CSV_PATH}，请手动从ISO官网下载开放数据并放置于此路径")
