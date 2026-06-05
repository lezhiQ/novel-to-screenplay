import re


def split_chapters(text: str) -> list[dict]:
    """将小说文本按章节拆分"""
    # 匹配常见章节格式：第一章、第1章、Chapter 1 等
    pattern = r'((?:第[一二三四五六七八九十百千\d]+章|Chapter\s*\d+|CHAPTER\s*\d+)[^\n]*)'
    parts = re.split(pattern, text)

    chapters = []
    current_title = "序章"
    current_text = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if re.match(pattern, part):
            # 保存前一个章节
            if current_text.strip():
                chapters.append({"title": current_title, "text": current_text.strip()})
            current_title = part
            current_text = ""
        else:
            current_text += part + "\n"

    # 保存最后一个章节
    if current_text.strip():
        chapters.append({"title": current_title, "text": current_text.strip()})

    # 如果没有检测到章节，把整篇当作一个章节
    if not chapters:
        chapters.append({"title": "全文", "text": text.strip()})

    return chapters


def extract_characters(text: str) -> list[str]:
    """从文本中提取可能的角色名"""
    # 匹配引号内的对话，提取说话人
    # 简单启发式：匹配 "XXX说" / "XXX道" / "XXX问" 等模式
    pattern = r'[一-龥]{1,4}(?:说|道|问|答|喊|叫|笑|叹|吼|低语|回答|嘟囔)'
    matches = re.findall(pattern, text)
    characters = list(set(m[:-1] for m in matches))
    return characters
