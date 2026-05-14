from urllib.parse import quote

from output.yaml_generator import generate_yaml
from utils.standard_metadata import enrich_standard_record, infer_process_tags
from config import OUTPUT_DIR


SOURCE_SEARCH_URLS = {
    "IPC": "https://www.ipc.org/search?search=",
    "ISO": "https://www.iso.org/search.html?q=",
    "IEC": "https://webstore.iec.ch/search?query=",
    "JEDEC": "https://www.jedec.org/search/node/",
    "GB": "https://openstd.samr.gov.cn/bzgk/std/std_list?p.p2=",
    "SJ/T": "https://hbba.sac.gov.cn/stdSearchList",
}


OFFICIAL_CATALOG_STANDARDS = [
    ("IPC", "IPC-A-610", "Acceptability of Electronic Assemblies", "SMT,焊接,品质验收,IPC标准", "回流焊,波峰焊,手工焊"),
    ("IPC", "IPC-J-STD-001", "Requirements for Soldered Electrical and Electronic Assemblies", "SMT,焊接,IPC标准", "焊接工艺,回流焊,波峰焊,手工焊"),
    ("IPC", "IPC-7711/7721", "Rework, Modification and Repair of Electronic Assemblies", "返修,维修,IPC标准", "返修,手工焊,检验"),
    ("IPC", "IPC-A-600", "Acceptability of Printed Boards", "PCB来料检验,IPC标准", "PCB来料检验"),
    ("IPC", "IPC-6012", "Qualification and Performance Specification for Rigid Printed Boards", "PCB制造,IPC标准", "PCB制造"),
    ("IPC", "IPC-2221", "Generic Standard on Printed Board Design", "PCB设计,IPC标准", "PCB设计"),
    ("IPC", "IPC-2222", "Sectional Design Standard for Rigid Organic Printed Boards", "PCB设计,IPC标准", "PCB设计"),
    ("IPC", "IPC-7351", "Generic Requirements for Surface Mount Design and Land Pattern Standard", "SMT,PCB设计,IPC标准", "PCB设计,贴片"),
    ("IPC", "IPC-7095", "Design and Assembly Process Implementation for BGAs", "BGA,SMT,IPC标准", "贴片,回流焊,检验"),
    ("IPC", "IPC-9701", "Performance Test Methods and Qualification Requirements for Surface Mount Solder Attachments", "SMT,可靠性,IPC标准", "回流焊,可靠性试验"),
    ("IPC", "IPC-1752A", "Materials Declaration Management", "环保合规,材料声明,IPC标准", "供应链质量,环保合规"),
    ("IPC", "IPC-1601", "Printed Board Handling and Storage Guidelines", "PCB存储,IPC标准", "PCB来料检验,仓储"),
    ("IPC", "IPC-4552", "Specification for Electroless Nickel/Immersion Gold Plating for Printed Boards", "PCB表面处理,IPC标准", "PCB制造,来料检验"),
    ("IPC", "IPC-4553", "Specification for Immersion Silver Plating for Printed Boards", "PCB表面处理,IPC标准", "PCB制造,来料检验"),
    ("IPC", "IPC-4554", "Specification for Immersion Tin Plating for Printed Boards", "PCB表面处理,IPC标准", "PCB制造,来料检验"),
    ("IPC", "IPC-6013", "Qualification and Performance Specification for Flexible/Rigid-Flexible Printed Boards", "柔性板,PCB制造,IPC标准", "PCB制造,来料检验"),
    ("JEDEC", "J-STD-020", "Moisture/Reflow Sensitivity Classification for Nonhermetic Surface Mount Devices", "元器件,湿敏等级,回流焊,JEDEC标准", "元器件存储,回流焊"),
    ("JEDEC", "J-STD-033", "Handling, Packing, Shipping and Use of Moisture/Reflow Sensitive Surface Mount Devices", "元器件,湿敏等级,JEDEC标准", "元器件存储,贴片"),
    ("JEDEC", "JESD22-A104", "Temperature Cycling", "可靠性,温度循环,JEDEC标准", "可靠性试验"),
    ("JEDEC", "JESD22-A110", "Highly Accelerated Temperature and Humidity Stress Test", "可靠性,湿热试验,JEDEC标准", "可靠性试验"),
    ("JEDEC", "JESD22-A113", "Preconditioning of Nonhermetic Surface Mount Devices Prior to Reliability Testing", "元器件,预处理,JEDEC标准", "元器件存储,可靠性试验"),
    ("JEDEC", "JESD22-A114", "Electrostatic Discharge Sensitivity Testing Human Body Model", "ESD,可靠性,JEDEC标准", "ESD防护,可靠性试验"),
    ("JEDEC", "JESD22-A115", "Electrostatic Discharge Sensitivity Testing Machine Model", "ESD,可靠性,JEDEC标准", "ESD防护,可靠性试验"),
    ("JEDEC", "JESD22-C101", "Field-Induced Charged-Device Model Test Method", "ESD,CDM,JEDEC标准", "ESD防护,可靠性试验"),
    ("JEDEC", "JESD47", "Stress-Test-Driven Qualification of Integrated Circuits", "集成电路,可靠性,JEDEC标准", "元器件选型,可靠性试验"),
    ("JEDEC", "JESD78", "IC Latch-Up Test", "集成电路,可靠性,JEDEC标准", "元器件选型,可靠性试验"),
    ("JEDEC", "JESD625", "Requirements for Handling Electrostatic-Discharge-Sensitive Devices", "ESD防护,元器件,JEDEC标准", "ESD防护,元器件存储"),
    ("JEDEC", "JESD51", "Methodology for the Thermal Measurement of Component Packages", "热测试,元器件,JEDEC标准", "元器件选型,可靠性试验"),
    ("ISO", "ISO 9001", "Quality management systems - Requirements", "质量管理,ISO标准", "全流程品质"),
    ("ISO", "ISO 14001", "Environmental management systems - Requirements with guidance for use", "环境管理,ISO标准", "环保合规,全流程管理"),
    ("ISO", "ISO 45001", "Occupational health and safety management systems - Requirements with guidance for use", "职业健康安全,ISO标准", "EHS管理"),
    ("ISO", "ISO 10012", "Measurement management systems - Requirements for measurement processes and measuring equipment", "计量管理,ISO标准", "计量管理,质量管理"),
    ("ISO", "ISO 2859-1", "Sampling procedures for inspection by attributes", "抽样检验,ISO标准", "来料检验,出货检验"),
    ("ISO", "ISO 14644-1", "Cleanrooms and associated controlled environments - Classification of air cleanliness by particle concentration", "洁净室,ISO标准", "洁净室管理,生产装配"),
    ("IEC", "IEC 60068-2-1", "Environmental testing - Part 2-1: Tests - Test A: Cold", "环境试验,低温,IEC标准", "可靠性试验"),
    ("IEC", "IEC 60068-2-2", "Environmental testing - Part 2-2: Tests - Test B: Dry heat", "环境试验,高温,IEC标准", "可靠性试验"),
    ("IEC", "IEC 60068-2-14", "Environmental testing - Part 2-14: Tests - Test N: Change of temperature", "环境试验,温度变化,IEC标准", "可靠性试验"),
    ("IEC", "IEC 60068-2-30", "Environmental testing - Part 2-30: Tests - Test Db: Damp heat, cyclic", "环境试验,湿热,IEC标准", "可靠性试验"),
    ("IEC", "IEC 60068-2-78", "Environmental testing - Part 2-78: Tests - Test Cab: Damp heat, steady state", "环境试验,湿热,IEC标准", "可靠性试验"),
    ("IEC", "IEC 61000-4-2", "Electromagnetic compatibility - Testing and measurement techniques - Electrostatic discharge immunity test", "EMC,ESD,IEC标准", "EMC测试,ESD防护"),
    ("IEC", "IEC 61000-4-3", "Electromagnetic compatibility - Radiated, radio-frequency, electromagnetic field immunity test", "EMC,射频抗扰度,IEC标准", "EMC测试"),
    ("IEC", "IEC 61000-4-4", "Electromagnetic compatibility - Electrical fast transient/burst immunity test", "EMC,抗扰度,IEC标准", "EMC测试"),
    ("IEC", "IEC 61000-4-5", "Electromagnetic compatibility - Surge immunity test", "EMC,浪涌,IEC标准", "EMC测试"),
    ("IEC", "IEC 61340-5-1", "Electrostatics - Protection of electronic devices from electrostatic phenomena", "ESD防护,IEC标准", "ESD防护,生产装配"),
    ("IEC", "IEC 61191-1", "Printed board assemblies - Part 1: Generic specification", "电子组装,IEC标准", "生产装配,检验"),
    ("IEC", "IEC 61191-2", "Printed board assemblies - Part 2: Sectional specification for surface mount soldered assemblies", "SMT,焊接,IEC标准", "贴片,回流焊"),
    ("IEC", "IEC 61191-3", "Printed board assemblies - Part 3: Sectional specification for through-hole mount soldered assemblies", "通孔焊接,IEC标准", "波峰焊,手工焊"),
    ("GB", "GB/T 4588.3", "印制板的设计和使用", "PCB设计,GB标准", "PCB设计"),
    ("GB", "GB/T 4728", "电气简图用图形符号", "电路设计,图形符号,GB标准", "电路设计"),
    ("GB", "GB/T 19001", "质量管理体系 要求", "质量管理,GB标准,ISO9001", "全流程品质"),
    ("GB", "GB/T 24001", "环境管理体系 要求及使用指南", "环境管理,GB标准,ISO14001", "环保合规,全流程管理"),
    ("GB", "GB/T 2423.1", "环境试验 第2部分：试验方法 试验A：低温", "环境试验,GB标准", "可靠性试验"),
    ("GB", "GB/T 2423.2", "环境试验 第2部分：试验方法 试验B：高温", "环境试验,GB标准", "可靠性试验"),
    ("GB", "GB/T 2423.3", "环境试验 第2部分：试验方法 试验Cab：恒定湿热试验", "环境试验,GB标准", "可靠性试验"),
    ("GB", "GB/T 2423.22", "环境试验 第2部分：试验方法 试验N：温度变化", "环境试验,GB标准", "可靠性试验"),
    ("GB", "GB/T 17626.2", "电磁兼容 试验和测量技术 静电放电抗扰度试验", "EMC,ESD,GB标准", "EMC测试,ESD防护"),
    ("GB", "GB/T 2828.1", "计数抽样检验程序 第1部分：按接收质量限检索的逐批检验抽样计划", "抽样检验,GB标准", "来料检验,出货检验"),
    ("SJ/T", "SJ/T 10533", "电子设备制造防静电技术要求", "ESD防护,电子制造,SJ/T标准", "ESD防护,生产装配"),
    ("SJ/T", "SJ/T 11363", "电子信息产品中有毒有害物质的限量要求", "环保合规,SJ/T标准", "环保合规,来料检验"),
    ("SJ/T", "SJ/T 11364", "电子信息产品污染控制标识要求", "环保合规,SJ/T标准", "环保合规,出货检验"),
]


def _source_url(source, code):
    base = SOURCE_SEARCH_URLS[source]
    return base + quote(code)


def _summary(source, code, name, source_url):
    return (
        f"本条目依据行业规范录入格式.md 列出的 {source} 官方来源建立，标准号为 {code}，"
        f"标准名称为《{name}》。该条目用于电子制造知识库的规范索引，可结合企业实际工艺补充"
        f"适用章节、验收等级、检验频次和记录要求。来源检索：{source_url}"
    )


def crawl_official_catalog(limit=None):
    """生成来自文档指定官网来源的标准目录元数据。"""
    processed = 0
    for source, code, name, tags, related_process in OFFICIAL_CATALOG_STANDARDS:
        if limit and processed >= limit:
            break
        source_url = _source_url(source, code)
        inferred = infer_process_tags(name)
        yaml_data = enrich_standard_record(
            {
                "standard_code": code,
                "standard_name": name,
                "section": "",
                "summary": _summary(source, code, name, source_url),
                "tags": tags or inferred["tags"],
                "related_process": related_process or inferred["related_process"],
            },
            source_tag=f"{source}标准" if source not in ("GB", "SJ/T") else "",
            default_related_process="电子制造",
        )
        generate_yaml(yaml_data, OUTPUT_DIR)
        processed += 1
        print(f"已生成官方目录条目: {code} {name}")
    print(f"官方目录元数据生成完成，共处理 {processed} 条")
