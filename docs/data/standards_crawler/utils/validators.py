import re

def normalize_standard_code(code):
    """标准化标准号: GB/T 19001-2016 -> GB_T_19001_2016（用于文件名）"""
    code = code.strip().upper()
    # 替换斜杠和空格为下划线
    code = re.sub(r'[/\s]+', '_', code)
    # 移除其他非法文件名字符
    code = re.sub(r'[\\:*?"<>|]', '', code)
    return code

def extract_ics_class(text):
    """从文本中提取ICS分类（如 31.080）"""
    match = re.search(r'\b31\.\d{3}\b', text)
    if match:
        return match.group()
    return None

def is_crawled_standard(code, output_dir):
    """检查标准是否已经生成过YAML，避免重复处理"""
    from pathlib import Path
    safe = normalize_standard_code(code)
    yaml_file = Path(output_dir) / f"{safe}.yaml"
    return yaml_file.exists()