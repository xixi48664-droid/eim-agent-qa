import os
import requests
from pathlib import Path
from config import TEMP_PDF_DIR, DELETE_PDF_AFTER_PROCESS
from utils.request_utils import fetch

def download_pdf(url, filename):
    """下载PDF到临时目录，返回本地路径"""
    os.makedirs(TEMP_PDF_DIR, exist_ok=True)
    local_path = Path(TEMP_PDF_DIR) / filename
    if local_path.exists():
        return str(local_path)
    resp = fetch(url, method="GET")
    if resp and resp.status_code == 200:
        with open(local_path, "wb") as f:
            f.write(resp.content)
        return str(local_path)
    return None

def extract_text_from_pdf(pdf_path):
    """从PDF提取文本（使用pdfplumber，更稳定）"""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"PDF文本提取失败 {pdf_path}: {e}")
        return None