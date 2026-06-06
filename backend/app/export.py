import json
import re
import yaml
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from backend.app.models import ScreenplayOutput


# 标准化时间格式映射
TIME_MAP = {
    "白天": "日", "早晨": "清晨", "早上": "清晨", "上午": "清晨",
    "中午": "午后", "下午": "午后", "傍晚": "傍晚", "黄昏": "黄昏",
    "晚上": "夜", "夜晚": "夜", "深夜": "深夜", "凌晨": "清晨",
    "日": "日", "夜": "夜",
}

# 标准化时间列表
VALID_TIMES = {"日", "夜", "黄昏", "清晨", "午后", "傍晚", "深夜"}


def normalize_time(time_str: str) -> str:
    """标准化时间格式"""
    if not time_str:
        return "日"
    time_str = time_str.strip()
    if time_str in VALID_TIMES:
        return time_str
    return TIME_MAP.get(time_str, "日")


def normalize_location(location: str, time_str: str = "") -> str:
    """确保 location 包含 INT./EXT. 前缀"""
    if not location:
        return f"INT. 未知地点"

    location = location.strip()

    # 已经有 INT./EXT. 前缀
    if re.match(r'^(INT\.|EXT\.)\s', location, re.IGNORECASE):
        # 标准化为大写
        location = re.sub(r'^(INT\.|EXT\.)', lambda m: m.group(1).upper(), location, flags=re.IGNORECASE)
        return location

    # 根据场景描述推断 INT./EXT.
    ext_keywords = ["室外", "户外", "街上", "操场", "花园", "公园", "广场", "海滩", "山", "森林", "天空", "马路", "街道"]
    is_ext = any(kw in location for kw in ext_keywords)
    prefix = "EXT." if is_ext else "INT."

    return f"{prefix} {location}"


def format_scene_heading(location: str, time: str) -> str:
    """格式化场景标题为好莱坞标准格式"""
    normalized_loc = normalize_location(location)
    normalized_time = normalize_time(time)
    return f"{normalized_loc} - {normalized_time}"


def export_yaml(screenplay: ScreenplayOutput) -> str:
    """导出为 YAML 格式字符串（标准化格式）"""
    data = screenplay.model_dump()

    # 标准化每个场景的 location 和 time
    for scene in data.get("scenes", []):
        scene["location"] = normalize_location(scene.get("location", ""), scene.get("time", ""))
        scene["time"] = normalize_time(scene.get("time", ""))

    return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)


def export_json(screenplay: ScreenplayOutput) -> str:
    """导出为 JSON 格式字符串（标准化格式）"""
    data = screenplay.model_dump()

    # 标准化每个场景的 location 和 time
    for scene in data.get("scenes", []):
        scene["location"] = normalize_location(scene.get("location", ""), scene.get("time", ""))
        scene["time"] = normalize_time(scene.get("time", ""))

    return json.dumps(data, ensure_ascii=False, indent=2)


def export_docx(screenplay: ScreenplayOutput) -> bytes:
    """导出为好莱坞标准格式的 DOCX 剧本文档"""
    doc = Document()

    # 设置页面边距（标准剧本格式）
    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(3.7)   # 左边距较大（装订侧）
        section.right_margin = Cm(2.54)

    # 设置默认字体
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Courier New'  # 标准剧本使用等宽字体
    font.size = Pt(12)

    # 添加页眉（剧本标题）
    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        header_para = header.paragraphs[0]
        header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = header_para.add_run(screenplay.title or "剧本")
        run.font.size = Pt(10)
        run.font.name = 'Courier New'
        run.font.color.rgb = RGBColor(128, 128, 128)

    # 添加页脚（页码）
    for section in doc.sections:
        footer = section.footer
        footer.is_linked_to_previous = False
        footer_para = footer.paragraphs[0]
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # 使用 Word 域代码插入页码
        run = footer_para.add_run()
        run.font.size = Pt(10)
        run.font.name = 'Courier New'
        from docx.oxml.ns import qn
        fldChar1 = run._element.makeelement(qn('w:fldChar'), {qn('w:fldCharType'): 'begin'})
        run._element.append(fldChar1)
        instrText = run._element.makeelement(qn('w:instrText'), {})
        instrText.text = ' PAGE '
        run._element.append(instrText)
        fldChar2 = run._element.makeelement(qn('w:fldChar'), {qn('w:fldCharType'): 'end'})
        run._element.append(fldChar2)

    # 标题页
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_para.space_before = Pt(120)
    title_run = title_para.add_run(screenplay.title or "剧本")
    title_run.bold = True
    title_run.font.size = Pt(24)
    title_run.font.name = 'Courier New'

    # 作者信息
    if screenplay.author:
        author_para = doc.add_paragraph()
        author_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        author_para.space_before = Pt(24)
        author_run = author_para.add_run(f"原作：{screenplay.author}")
        author_run.font.size = Pt(14)
        author_run.font.name = 'Courier New'

    # "剧本正文" 分隔
    doc.add_page_break()

    # 遍历场景
    for i, scene in enumerate(screenplay.scenes):
        # 场景标题（好莱坞标准格式：INT./EXT. 地点 - 时间）
        scene_heading = format_scene_heading(scene.location or "", scene.time or "")

        heading_para = doc.add_paragraph()
        heading_para.space_before = Pt(24) if i > 0 else Pt(12)
        heading_para.space_after = Pt(12)
        heading_run = heading_para.add_run(scene_heading)
        heading_run.bold = True
        heading_run.font.size = Pt(12)
        heading_run.font.name = 'Courier New'

        # 场景描述（斜体）
        if scene.description:
            p = doc.add_paragraph()
            p.space_after = Pt(6)
            run = p.add_run(scene.description)
            run.italic = True
            run.font.size = Pt(12)
            run.font.name = 'Courier New'

        # 处理 items 列表（有序）
        if scene.items:
            for item in scene.items:
                if item.type == "dialogue":
                    # 角色名：大写、居中偏左（标准剧本缩进）
                    char_para = doc.add_paragraph()
                    char_para.paragraph_format.left_indent = Cm(5.0)
                    char_para.space_before = Pt(6)
                    char_para.space_after = Pt(0)
                    char_run = char_para.add_run(item.character.upper())
                    char_run.bold = True
                    char_run.font.size = Pt(12)
                    char_run.font.name = 'Courier New'

                    # 括号内动作（如果有）
                    if item.action:
                        paren_para = doc.add_paragraph()
                        paren_para.paragraph_format.left_indent = Cm(4.0)
                        paren_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        paren_para.space_before = Pt(0)
                        paren_para.space_after = Pt(0)
                        paren_run = paren_para.add_run(f"({item.action})")
                        paren_run.font.size = Pt(12)
                        paren_run.font.name = 'Courier New'

                    # 台词：左对齐，标准缩进
                    line_para = doc.add_paragraph()
                    line_para.paragraph_format.left_indent = Cm(3.0)
                    line_para.paragraph_format.right_indent = Cm(3.0)
                    line_para.space_before = Pt(0)
                    line_para.space_after = Pt(6)
                    line_run = line_para.add_run(item.line or "")
                    line_run.font.size = Pt(12)
                    line_run.font.name = 'Courier New'

                else:  # action
                    p = doc.add_paragraph()
                    p.space_before = Pt(6)
                    p.space_after = Pt(6)
                    # 动作描写：斜体，无方括号
                    action_text = item.action or ""
                    if item.character:
                        action_text = f"{item.character} {action_text}"
                    run = p.add_run(action_text)
                    run.italic = True
                    run.font.size = Pt(12)
                    run.font.name = 'Courier New'
        else:
            # 兼容旧格式：分别处理 actions 和 dialogues
            for action in scene.actions:
                p = doc.add_paragraph()
                p.space_before = Pt(6)
                p.space_after = Pt(6)
                action_text = action.action or ""
                if action.character:
                    action_text = f"{action.character} {action_text}"
                run = p.add_run(action_text)
                run.italic = True
                run.font.size = Pt(12)
                run.font.name = 'Courier New'

            for dialogue in scene.dialogues:
                # 角色名
                char_para = doc.add_paragraph()
                char_para.paragraph_format.left_indent = Cm(5.0)
                char_para.space_before = Pt(6)
                char_para.space_after = Pt(0)
                char_run = char_para.add_run(dialogue.character.upper())
                char_run.bold = True
                char_run.font.size = Pt(12)
                char_run.font.name = 'Courier New'

                # 括号内动作
                if dialogue.action:
                    paren_para = doc.add_paragraph()
                    paren_para.paragraph_format.left_indent = Cm(4.0)
                    paren_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    paren_para.space_before = Pt(0)
                    paren_para.space_after = Pt(0)
                    paren_run = paren_para.add_run(f"({dialogue.action})")
                    paren_run.font.size = Pt(12)
                    paren_run.font.name = 'Courier New'

                # 台词
                line_para = doc.add_paragraph()
                line_para.paragraph_format.left_indent = Cm(3.0)
                line_para.paragraph_format.right_indent = Cm(3.0)
                line_para.space_before = Pt(0)
                line_para.space_after = Pt(6)
                line_run = line_para.add_run(dialogue.line or "")
                line_run.font.size = Pt(12)
                line_run.font.name = 'Courier New'

        # 场景间分隔线（最后一个场景不加）
        if i < len(screenplay.scenes) - 1:
            sep_para = doc.add_paragraph()
            sep_para.space_before = Pt(12)
            sep_para.space_after = Pt(12)
            sep_run = sep_para.add_run("─" * 30)
            sep_run.font.size = Pt(10)
            sep_run.font.color.rgb = RGBColor(180, 180, 180)

    # "FADE OUT." 结尾
    fade_para = doc.add_paragraph()
    fade_para.space_before = Pt(24)
    fade_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    fade_run = fade_para.add_run("FADE OUT.")
    fade_run.bold = True
    fade_run.font.size = Pt(12)
    fade_run.font.name = 'Courier New'

    # 保存到内存
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
