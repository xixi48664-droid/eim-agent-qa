import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import OUTPUT_DIR


FAKE_SECTION_PREFIXES = ("重点章节", "重点关注章节")


def is_verified_section(section):
    """只接受类似“第 5 章 — 焊接”或“Chapter 5 Soldering”的真实章节写法。"""
    section = (section or "").strip()
    if not section:
        return False
    if section.startswith(FAKE_SECTION_PREFIXES):
        return False
    return bool(
        re.search(r"第\s*[\d一二三四五六七八九十百]+\s*章", section)
        or re.search(r"\bChapter\s+\d+\b", section, re.IGNORECASE)
        or re.search(r"^\d+(?:\.\d+)*\s+[\w\u4e00-\u9fff]", section)
    )


def _pick_focus(name, tags, related_process):
    text = f"{name},{tags},{related_process}"
    if re.search(r"印制板|PCB|线路板", text, re.I):
        return "PCB 设计、制板、来料检验和组装件质量确认"
    if re.search(r"焊|SMT|Solder|Welding|BGA", text, re.I):
        return "SMT 贴装、回流焊、波峰焊、手工焊和焊点验收"
    if re.search(r"静电|ESD|Electrostatic", text, re.I):
        return "ESD 防护区建设、人员接地、敏感器件包装转运和实时监控"
    if re.search(r"半导体|集成电路|芯片|器件|IC", text, re.I):
        return "半导体器件选型、来料验证、湿敏/可靠性控制和失效判定"
    if re.search(r"电磁兼容|EMC|抗扰度|浪涌|射频", text, re.I):
        return "整机和模块的 EMC 设计验证、抗扰度测试和整改闭环"
    if re.search(r"环境试验|温度|湿热|可靠性|振动|冲击", text, re.I):
        return "电子产品可靠性验证、环境应力筛选和试验报告判定"
    if re.search(r"质量|抽样|检验|管理体系|Sampling", text, re.I):
        return "来料检验、过程质量控制、抽样判定和质量体系运行"
    if re.search(r"洁净室|受控环境", text, re.I):
        return "洁净生产环境分级、粒子监测、静电控制和现场审核"
    return "电子信息制造过程的设计、生产、检验、可靠性验证和质量闭环"


def make_summary(record):
    name = record.get("standard_name", "")
    section = record.get("section", "").strip()
    focus = _pick_focus(name, record.get("tags", ""), record.get("related_process", ""))

    source_match = re.search(r"(https?://\S+)", record.get("summary", ""))
    source = source_match.group(1).rstrip("。") if source_match else ""
    source_sentence = f" 来源：{source}" if source else ""

    if section:
        section_sentence = f"本条记录对应章节为“{section}”，应结合该章节条款提炼"
    else:
        section_sentence = "当前未获取到官网 PDF/正文目录中的真实章节号和章节名称，section 按录入规则留空；应用时应从正式标准文本提炼"

    return (
        f"该规范在电子信息制造业中重点用于{focus}。{section_sentence}工艺参数、试验条件、"
        f"验收判据、记录要求和不合格处置要求，并转换为作业指导书、检验规范、设备点检项目或质量审核清单。"
        f"对涉及客户等级、产品等级、可靠性等级或法规合规的条款，应在项目导入、首件确认、量产巡检和出货评审中保持一致引用。"
        f"{source_sentence}"
    )


def enrich_file(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        return False

    changed = False
    for record in data:
        section = record.get("section", "")
        if section and not is_verified_section(section):
            record["section"] = ""
            changed = True
        new_summary = make_summary(record)
        if record.get("summary") != new_summary:
            record["summary"] = new_summary
            changed = True

    if changed:
        path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120),
            encoding="utf-8",
        )
    return True


def main():
    count = 0
    for path in sorted(Path(OUTPUT_DIR).glob("*.yaml")):
        if enrich_file(path):
            count += 1
    print(f"已清理非真实 section 并重写 summary: {count} 个 YAML")


if __name__ == "__main__":
    main()
