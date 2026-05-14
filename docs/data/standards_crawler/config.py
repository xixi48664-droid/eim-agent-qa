from pathlib import Path

CRAWLER_DIR = Path(__file__).resolve().parent
REPO_ROOT = CRAWLER_DIR.parents[2]

# 输出目录：行业规范录入格式.md 要求放入 docs/data 目录
OUTPUT_DIR = CRAWLER_DIR.parent
# 临时目录（存放下载的 PDF）
TEMP_PDF_DIR = CRAWLER_DIR / "data" / "pdfs"
# 中间数据目录
DATA_DIR = CRAWLER_DIR / "data"

# 是否删除下载后的 PDF（预留配置）
DELETE_PDF_AFTER_PROCESS = True

# ICS 分类（31：电子学）
ICS_31 = "31"

# GB/T 网站配置
GB_BASE_URL = "https://openstd.samr.gov.cn/bzgk/std"
GB_SEARCH_URL = f"{GB_BASE_URL}/std_list"
GB_DETAIL_URL = f"{GB_BASE_URL}/newGbInfo"
GB_PDF_DOWNLOAD_URL = "https://openstd.samr.gov.cn/bzgk/gb/downloadStdPdf"

# SJ/T 检索配置（全国标准信息公共服务平台）
SJT_BASE_URL = "https://std.samr.gov.cn"
SJT_SEARCH_URL = f"{SJT_BASE_URL}/search/std"

# JEDEC 配置
JEDEC_BASE_URL = "https://www.jedec.org"
JEDEC_SEARCH_URL = f"{JEDEC_BASE_URL}/search/node"

# IPC 配置（仅目录）
IPC_CATALOG_URL = "https://www.ipc.org/standards"

# ISO 开放数据 CSV（手动下载后放置于 DATA_DIR）
ISO_CSV_FILENAME = "iso_standards.csv"
ISO_CSV_PATH = DATA_DIR / ISO_CSV_FILENAME

# 请求配置
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
REQUEST_DELAY = 1
RETRY_TIMES = 3
