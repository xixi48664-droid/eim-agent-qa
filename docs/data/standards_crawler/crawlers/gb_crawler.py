import re
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from utils.request_utils import fetch
from utils.standard_metadata import enrich_standard_record, infer_process_tags
from output.yaml_generator import generate_yaml
from config import GB_SEARCH_URL, GB_DETAIL_URL, OUTPUT_DIR


DEFAULT_GB_KEYWORDS = (
    "电子",
    "印制板",
    "半导体",
    "静电",
    "电子束焊",
    "电磁兼容",
    "可靠性",
    "环境试验",
    "质量管理",
    "元器件",
)


def _extract_hcno(row):
    for node in row.select("[onclick]"):
        match = re.search(r"showInfo\('([A-F0-9]+)'\)", node.get("onclick", ""))
        if match:
            return match.group(1)
    return ""


def _iter_standard_rows(soup):
    for row in soup.select("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
        if len(cells) < 5:
            continue
        code = cells[1].replace("\xa0", " ").strip()
        if code.startswith(("GB ", "GB/T ", "GB/Z ")):
            yield row, cells


def _build_summary(code, name, cells, detail_url, query_url):
    status = cells[6] if len(cells) > 6 else ""
    publish_date = cells[7] if len(cells) > 7 else ""
    implementation_date = cells[8] if len(cells) > 8 else ""
    parts = [
        f"本条目采集自国家标准全文公开系统的标准检索结果，标准号为 {code}，标准名称为《{name}》。",
    ]
    if status:
        parts.append(f"页面列出的标准状态为{status}。")
    if publish_date:
        parts.append(f"发布日期为{publish_date.split()[0]}。")
    if implementation_date:
        parts.append(f"实施日期为{implementation_date.split()[0]}。")
    parts.append("该标准可作为电子制造、质量管理、检验测试或相关工程活动的规范依据，录入后应结合企业工艺文件补充适用章节和管控要点。")
    parts.append(f"来源详情：{detail_url or query_url}")
    return "".join(parts)


def crawl_gb_standards(keywords=DEFAULT_GB_KEYWORDS, max_pages=10, per_keyword_limit=10):
    """从国家标准全文公开系统按关键词采集 GB/GB/T/GB/Z 元数据。"""
    processed = 0
    seen = set()

    for keyword in keywords:
        params = {
            "p.p1": 2,
            "p.p2": keyword,
            "p.p90": "circulation_date",
            "p.p91": "desc",
        }
        query_url = f"{GB_SEARCH_URL}?{urlencode(params)}"
        resp = fetch(GB_SEARCH_URL, params=params)
        if not resp:
            print(f"国家标准检索失败: {keyword}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        keyword_count = 0
        for row, cells in _iter_standard_rows(soup):
            code = cells[1].strip()
            name = cells[4].strip()
            if not name or code in seen:
                continue
            seen.add(code)

            hcno = _extract_hcno(row)
            detail_url = f"{GB_DETAIL_URL}?hcno={hcno}" if hcno else query_url
            inferred = infer_process_tags(name)
            yaml_data = enrich_standard_record(
                {
                    "standard_code": code,
                    "standard_name": name,
                    "section": "",
                    "summary": _build_summary(code, name, cells, detail_url, query_url),
                    "tags": ",".join(filter(None, [inferred["tags"], "GB标准,国家标准"])),
                    "related_process": inferred["related_process"],
                },
                default_related_process="电子制造",
            )
            generate_yaml(yaml_data, OUTPUT_DIR)
            keyword_count += 1
            processed += 1
            print(f"已采集国家标准: {code} {name}")
            if keyword_count >= per_keyword_limit or processed >= max_pages * per_keyword_limit:
                break

    print(f"GB/GB/T 元数据采集完成，共处理 {processed} 条")
