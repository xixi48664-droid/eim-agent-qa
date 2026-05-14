RECOMMENDED_STANDARDS = {
    "IPC-A-610": {
        "standard_name": "电子组件的可接受性",
        "tags": "SMT,焊接,品质验收,IPC标准",
        "related_process": "回流焊,波峰焊,手工焊",
    },
    "IPC-J-STD-001": {
        "standard_name": "焊接的电气和电子组件要求",
        "tags": "SMT,焊接,IPC标准",
        "related_process": "焊接工艺,回流焊,波峰焊,手工焊",
    },
    "IPC-7711/7721": {
        "standard_name": "电子组件的返工与维修",
        "tags": "返修,维修,IPC标准",
        "related_process": "返修,手工焊,检验",
    },
    "GB/T 4588.3": {
        "standard_name": "印制板的设计和使用",
        "tags": "PCB设计,GB标准",
        "related_process": "PCB设计",
    },
    "GB/T 4728": {
        "standard_name": "电气简图用图形符号",
        "tags": "电路设计,图形符号,GB标准",
        "related_process": "电路设计",
    },
    "SJ/T 10533": {
        "standard_name": "电子设备制造防静电技术要求",
        "tags": "ESD防护,电子制造,SJ/T标准",
        "related_process": "ESD防护,生产装配",
    },
    "JEDEC J-STD-020": {
        "standard_name": "塑封集成电路湿度/回流焊敏感度",
        "tags": "元器件,湿敏等级,回流焊,JEDEC标准",
        "related_process": "元器件存储,回流焊",
    },
    "IPC-6012": {
        "standard_name": "刚性印制板的鉴定与性能规范",
        "tags": "PCB制造,IPC标准",
        "related_process": "PCB制造",
    },
    "IPC-A-600": {
        "standard_name": "印制板的可接受性",
        "tags": "PCB来料检验,IPC标准",
        "related_process": "PCB来料检验",
    },
    "ISO 9001": {
        "standard_name": "质量管理体系",
        "tags": "质量管理,ISO标准",
        "related_process": "全流程品质",
    },
}


PROCESS_KEYWORDS = (
    ("印制板|PCB|线路板", "PCB设计,PCB制造,来料检验", "PCB设计,PCB制造,PCB来料检验"),
    ("焊|回流|波峰|电子束", "焊接,SMT,工艺检验", "回流焊,波峰焊,手工焊"),
    ("静电|ESD", "ESD防护,电子制造", "ESD防护,生产装配"),
    ("半导体|集成电路|芯片|器件", "半导体,元器件,可靠性", "元器件选型,元器件存储,来料检验"),
    ("电磁兼容|EMC|抗扰度|射频", "EMC,测试,可靠性", "EMC测试,整机测试"),
    ("环境试验|温度|湿热|振动|冲击|可靠性", "可靠性,环境试验,测试", "可靠性试验,环境试验"),
    ("质量|抽样|检验|管理体系", "质量管理,检验,体系", "质量管理,来料检验,过程检验"),
    ("图形符号|电气简图|电路", "电路设计,图形符号", "电路设计,原理图设计"),
)


def infer_process_tags(text):
    """根据标准名称推断录入模板中的标签和关联工艺。"""
    import re

    tags = []
    processes = []
    for pattern, tag_text, process_text in PROCESS_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            tags.extend(tag_text.split(","))
            processes.extend(process_text.split(","))

    if not tags:
        tags = ["电子制造", "行业规范"]
    if not processes:
        processes = ["电子制造"]

    return {
        "tags": ",".join(dict.fromkeys(tags)),
        "related_process": ",".join(dict.fromkeys(processes)),
    }


def enrich_standard_record(record, source_tag="", default_related_process=""):
    """为爬取记录补齐文档推荐规范中的名称、标签和关联工艺。"""
    code = record.get("standard_code", "").strip()
    matched = None
    for prefix, metadata in RECOMMENDED_STANDARDS.items():
        if code.upper().startswith(prefix.upper()):
            matched = metadata
            break

    enriched = dict(record)
    if matched:
        for field in ("standard_name", "tags", "related_process"):
            if not enriched.get(field):
                enriched[field] = matched[field]

    if source_tag and source_tag not in enriched.get("tags", ""):
        enriched["tags"] = ",".join(filter(None, [enriched.get("tags", ""), source_tag]))
    if default_related_process and not enriched.get("related_process"):
        enriched["related_process"] = default_related_process
    return enriched
