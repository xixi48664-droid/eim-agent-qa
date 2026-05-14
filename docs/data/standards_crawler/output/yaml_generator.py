import os
from pathlib import Path

import yaml

from utils.validators import normalize_standard_code


TEMPLATE_FIELDS = (
    "standard_code",
    "standard_name",
    "section",
    "summary",
    "tags",
    "related_process",
)


def _stringify(value):
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("zh", "cn", "en"):
            if value.get(key):
                return str(value[key]).strip()
        return next((str(v).strip() for v in value.values() if v), "")
    if isinstance(value, (list, tuple, set)):
        return ",".join(str(item).strip() for item in value if item)
    return str(value).strip()


def _limit_summary(summary):
    summary = _stringify(summary)
    if len(summary) <= 500:
        return summary
    return summary[:497].rstrip() + "..."


def normalize_standard_record(standard_dict):
    """转换为行业规范录入格式.md 规定的 6 个字符串字段。"""
    record = {field: _stringify(standard_dict.get(field, "")) for field in TEMPLATE_FIELDS}
    record["summary"] = _limit_summary(record["summary"])
    return record


def normalize_standard_records(standard_dict):
    """支持一个规范按多个真实章节生成同一 YAML 内的多条记录。"""
    sections = standard_dict.get("sections")
    if not sections:
        return [normalize_standard_record(standard_dict)]

    records = []
    for section in sections:
        item = dict(standard_dict)
        item.pop("sections", None)
        item["section"] = section
        records.append(normalize_standard_record(item))
    return records


def generate_yaml(standard_dict, output_dir):
    """按模板输出 YAML；多个真实章节写入同一个 YAML 文档。"""
    records = normalize_standard_records(standard_dict)
    if not records[0]["standard_name"]:
        raise ValueError("standard_name 是必填字段，无法生成 YAML")

    os.makedirs(output_dir, exist_ok=True)
    safe_code = normalize_standard_code(records[0]["standard_code"] or records[0]["standard_name"])
    filepath = Path(output_dir) / f"{safe_code}.yaml"

    with open(filepath, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            records,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=120,
        )
    print(f"生成YAML: {filepath}")
    return filepath
