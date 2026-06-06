import re
import yaml
from openai import OpenAI
from backend.app.config import MIMO_API_BASE, MIMO_API_KEY, MIMO_MODEL
from backend.app.models import ScreenplayOutput, Scene, Dialogue, Action
from backend.app.prompts import SYSTEM_PROMPT, CONVERT_PROMPT, CHAPTER_PROMPT
from backend.app.parser import split_chapters


def get_client() -> OpenAI:
    return OpenAI(base_url=MIMO_API_BASE, api_key=MIMO_API_KEY)


def call_llm(user_prompt: str) -> str:
    """调用小米 MiMo API"""
    client = get_client()
    response = client.chat.completions.create(
        model=MIMO_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def call_llm_stream(user_prompt: str):
    """流式调用小米 MiMo API"""
    client = get_client()
    stream = client.chat.completions.create(
        model=MIMO_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def extract_yaml_from_response(text: str) -> dict:
    """从 LLM 响应中提取 YAML 内容，支持多种格式和错误处理"""
    if not text:
        return None

    # 尝试提取 ```yaml ... ``` 代码块
    match = re.search(r'```yaml\s*\n(.*?)```', text, re.DOTALL)
    if match:
        yaml_content = match.group(1).strip()
    else:
        # 尝试提取 ``` ... ``` 代码块（不带 yaml 标记）
        match = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
        if match:
            yaml_content = match.group(1).strip()
        else:
            # 尝试直接解析整个文本
            yaml_content = text.strip()

    # 尝试解析 YAML
    try:
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        # 如果解析失败，尝试修复常见问题
        print(f"YAML 解析错误: {e}")
        print(f"原始 YAML:\n{yaml_content[:500]}...")

        # 尝试修复常见问题
        fixed_yaml = fix_common_yaml_issues(yaml_content)
        try:
            return yaml.safe_load(fixed_yaml)
        except yaml.YAMLError:
            # 如果还是失败，尝试更宽松的解析
            return try_parse_yaml_lenient(yaml_content)


def fix_common_yaml_issues(yaml_str: str) -> str:
    """修复常见的 YAML 格式问题"""
    lines = yaml_str.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines):
        # 修复缺少空格的冒号
        if ':' in line and not line.strip().startswith('#'):
            # 检查冒号后面是否有空格
            colon_pos = line.find(':')
            if colon_pos > 0 and colon_pos < len(line) - 1:
                if line[colon_pos + 1] != ' ' and line[colon_pos + 1] != '\n':
                    line = line[:colon_pos + 1] + ' ' + line[colon_pos + 1:]

        # 修复不正确的缩进（假设使用 2 空格缩进）
        if line.strip() and not line.startswith(' '):
            # 顶级元素，保持原样
            pass

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def try_parse_yaml_lenient(yaml_str: str) -> dict:
    """更宽松的 YAML 解析，尝试提取关键信息"""
    try:
        # 尝试用更宽松的方式解析
        import re

        # 提取 title
        title_match = re.search(r'title:\s*["\']?([^"\']+)["\']?', yaml_str)
        title = title_match.group(1) if title_match else "未知标题"

        # 提取 scenes
        scenes = []
        scene_pattern = r'-\s*scene_id:\s*(\d+)'
        scene_matches = re.finditer(scene_pattern, yaml_str)

        for scene_match in scene_matches:
            scene_id = int(scene_match.group(1))
            # 尝试提取这个场景的内容
            scene_start = scene_match.start()
            # 找到下一个场景或文本结束
            next_scene = re.search(r'-\s*scene_id:', yaml_str[scene_start + 1:])
            scene_end = scene_start + 1 + next_scene.start() if next_scene else len(yaml_str)
            scene_text = yaml_str[scene_start:scene_end]

            # 提取场景属性
            location = re.search(r'location:\s*["\']?([^"\']+)["\']?', scene_text)
            time = re.search(r'time:\s*["\']?([^"\']+)["\']?', scene_text)
            description = re.search(r'description:\s*["\']?([^"\']+)["\']?', scene_text)

            scene_data = {
                'scene_id': scene_id,
                'location': location.group(1) if location else "",
                'time': time.group(1) if time else "",
                'description': description.group(1) if description else "",
                'dialogues': [],
                'actions': []
            }

            # 提取对话
            dialogue_pattern = r'character:\s*["\']?([^"\']+)["\']?\s*\n\s*line:\s*["\']?([^"\']+)["\']?'
            dialogue_matches = re.finditer(dialogue_pattern, scene_text)
            for d_match in dialogue_matches:
                scene_data['dialogues'].append({
                    'character': d_match.group(1),
                    'line': d_match.group(2),
                    'action': ""
                })

            scenes.append(scene_data)

        if scenes:
            return {'title': title, 'scenes': scenes}

    except Exception as e:
        print(f"宽松解析也失败: {e}")

    return None


def convert_novel(title: str, text: str) -> ScreenplayOutput:
    """将小说文本转换为剧本（非流式）"""
    chapters = split_chapters(text)
    all_scenes = []
    scene_counter = 0
    prev_context = ""

    for i, chapter in enumerate(chapters):
        # 使用 CHAPTER_PROMPT 并传递前文上下文
        prompt = CHAPTER_PROMPT.format(
            title=title,
            chapter_num=i + 1,
            prev_context=prev_context,
            text=chapter["text"]
        )
        response = call_llm(prompt)
        data = extract_yaml_from_response(response)

        if data and "scenes" in data:
            for scene_data in data["scenes"]:
                scene_counter += 1
                scene_data["scene_id"] = scene_counter

                # 确保所有必需字段都有默认值
                scene_data.setdefault("location", "")
                scene_data.setdefault("time", "")
                scene_data.setdefault("description", "")
                scene_data.setdefault("dialogues", [])
                scene_data.setdefault("actions", [])

                # 确保 dialogues 中的每个元素都有必需字段
                for dialogue in scene_data.get("dialogues", []):
                    dialogue.setdefault("character", "")
                    dialogue.setdefault("line", "")
                    dialogue.setdefault("action", "")

                # 确保 actions 中的每个元素都有必需字段
                for action in scene_data.get("actions", []):
                    action.setdefault("character", "")
                    action.setdefault("action", "")

                try:
                    all_scenes.append(Scene(**scene_data))
                except Exception as e:
                    print(f"场景 {scene_counter} 解析失败: {e}")
                    print(f"场景数据: {scene_data}")
                    # 跳过这个场景，继续处理
                    continue

            # 更新前文上下文（取最后一个场景的描述）
            if data["scenes"]:
                last_scene = data["scenes"][-1]
                prev_context = f"场景{last_scene.get('scene_id', '')}: {last_scene.get('description', '')}"

    return ScreenplayOutput(title=title, scenes=all_scenes)


def convert_novel_stream(title: str, text: str):
    """流式转换：逐步返回 YAML 文本"""
    chapters = split_chapters(text)
    all_scenes = []
    scene_counter = 0
    prev_context = ""

    for i, chapter in enumerate(chapters):
        # 使用 CHAPTER_PROMPT 并传递前文上下文
        prompt = CHAPTER_PROMPT.format(
            title=title,
            chapter_num=i + 1,
            prev_context=prev_context,
            text=chapter["text"]
        )
        full_response = ""
        for chunk in call_llm_stream(prompt):
            full_response += chunk
            yield chunk

        # 解析本章结果
        data = extract_yaml_from_response(full_response)
        if data and "scenes" in data:
            for scene_data in data["scenes"]:
                scene_counter += 1
                scene_data["scene_id"] = scene_counter

                # 确保所有必需字段都有默认值
                scene_data.setdefault("location", "")
                scene_data.setdefault("time", "")
                scene_data.setdefault("description", "")
                scene_data.setdefault("dialogues", [])
                scene_data.setdefault("actions", [])

                # 确保 dialogues 中的每个元素都有必需字段
                for dialogue in scene_data.get("dialogues", []):
                    dialogue.setdefault("character", "")
                    dialogue.setdefault("line", "")
                    dialogue.setdefault("action", "")

                # 确保 actions 中的每个元素都有必需字段
                for action in scene_data.get("actions", []):
                    action.setdefault("character", "")
                    action.setdefault("action", "")

                try:
                    all_scenes.append(Scene(**scene_data))
                except Exception as e:
                    print(f"场景 {scene_counter} 解析失败: {e}")
                    print(f"场景数据: {scene_data}")
                    # 跳过这个场景，继续处理
                    continue

            # 更新前文上下文（取最后一个场景的描述）
            if data["scenes"]:
                last_scene = data["scenes"][-1]
                prev_context = f"场景{last_scene.get('scene_id', '')}: {last_scene.get('description', '')}"

    return ScreenplayOutput(title=title, scenes=all_scenes)
