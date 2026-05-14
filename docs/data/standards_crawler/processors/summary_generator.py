import re

def extract_section(text, section_keywords):
    """
    根据关键词列表提取章节内容
    section_keywords: 列表，如 ['范围', '适用范围', 'Scope']
    返回第一个匹配到的段落（不超过500字）
    """
    if not text:
        return ""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        for kw in section_keywords:
            if kw in line:
                # 提取从该行开始的连续段落（最多500字）
                start = i
                end = min(i+20, len(lines))  # 最多20行
                summary = '\n'.join(lines[start:end])
                # 限制长度
                if len(summary) > 500:
                    summary = summary[:500] + "..."
                return summary.strip()
    # 如果没找到，返回前500字符
    return text[:500].strip()

def generate_summary(pdf_text, lang='zh'):
    """
    生成标准摘要（200-500字）
    lang: 'zh' 或 'en'
    """
    if not pdf_text:
        return ""
    if lang == 'zh':
        keywords = ['范围', '适用范围', '标准范围', '本文件规定了', '本部分规定了']
        summary = extract_section(pdf_text, keywords)
        if len(summary) < 50:
            # 后备：取前300字符
            summary = pdf_text[:300].strip()
    else:
        keywords = ['scope', 'general', 'this document specifies', 'purpose']
        summary = extract_section(pdf_text, keywords)
        if len(summary) < 50:
            summary = pdf_text[:300].strip()
    return summary

def extract_section_titles(pdf_text):
    """
    提取章节标题（用于section字段）
    返回第一个主要章节的标题，如 "第5章 焊接"
    """
    if not pdf_text:
        return ""
    # 匹配中文章节模式
    pattern_ch = r'(第[一二三四五六七八九十\d]+章\s*[^\n]+)'
    match = re.search(pattern_ch, pdf_text)
    if match:
        return match.group(1).strip()
    # 匹配英文 Chapter X
    pattern_en = r'(Chapter\s+\d+[\.\s]+[^\n]+)'
    match = re.search(pattern_en, pdf_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # 匹配数字编号章节如 5.1 Introduction
    pattern_num = r'^(\d+(\.\d+)*\s+[^\n]+)' 
    lines = pdf_text.split('\n')
    for line in lines[:50]:
        if re.match(pattern_num, line):
            return line.strip()
    return ""