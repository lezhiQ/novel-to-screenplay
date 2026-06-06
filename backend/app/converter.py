import re
import yaml
from openai import OpenAI
from backend.app.config import MIMO_API_BASE, MIMO_API_KEY, MIMO_MODEL
from backend.app.models import ScreenplayOutput, Scene, Dialogue, Action
from backend.app.prompts import SYSTEM_PROMPT, CONVERT_PROMPT, CHAPTER_PROMPT
from backend.app.parser import split_chapters


def get_client(api_key: str = "", api_base: str = "") -> OpenAI:
    return OpenAI(
        base_url=api_base or MIMO_API_BASE,
        api_key=api_key or MIMO_API_KEY,
    )


def call_llm(user_prompt: str, api_key: str = "", api_base: str = "", model: str = "") -> str:
    """调用小米 MiMo API"""
    client = get_client(api_key, api_base)
    response = client.chat.completions.create(
        model=model or MIMO_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def call_llm_stream(user_prompt: str, api_key: str = "", api_base: str = "", model: str = ""):
    """流式调用小米 MiMo API"""
    client = get_client(api_key, api_base)
    stream = client.chat.completions.create(
        model=model or MIMO_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and len(chunk.choices) > 0:
            if chunk.choices[0].delta and chunk.choices[0].delta.content:
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
            yaml_content = text.strip()

    # 尝试解析 YAML
    try:
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError:
        pass

    # 预处理：修复 AI 生成的 YAML 中常见的引号问题
    fixed_yaml = preprocess_yaml(yaml_content)
    try:
        return yaml.safe_load(fixed_yaml)
    except yaml.YAMLError:
        pass

    # 再尝试修复常见格式问题
    fixed_yaml2 = fix_common_yaml_issues(fixed_yaml)
    try:
        return yaml.safe_load(fixed_yaml2)
    except yaml.YAMLError:
        pass

    # 最后用宽松解析
    return try_parse_yaml_lenient(yaml_content)


def preprocess_yaml(yaml_str: str) -> str:
    """预处理 YAML：修复 AI 生成的常见格式问题"""
    lines = yaml_str.split('\n')
    fixed = []
    for line in lines:
        stripped = line.strip()
        # 处理 key: "value 形式（缺少右引号）
        # 匹配 action: "... 或 line: "... 等
        m = re.match(r'^(\s*(?:action|line|description|location|time):\s*)"(.+)$', line)
        if m and not stripped.endswith('"'):
            indent = m.group(1)
            value = m.group(2)
            # 转义值中的内部引号
            value = value.replace('"', '\\"')
            line = f'{indent}"{value}"'
        fixed.append(line)
    return '\n'.join(fixed)


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
        import re

        title_match = re.search(r'title:\s*["\']?([^"\']+)["\']?', yaml_str)
        title = title_match.group(1) if title_match else "未命名作品"

        scenes = []
        scene_pattern = r'-\s*scene_id:\s*(\d+)'
        scene_matches = list(re.finditer(scene_pattern, yaml_str))

        for idx, scene_match in enumerate(scene_matches):
            scene_id = int(scene_match.group(1))
            scene_start = scene_match.start()
            scene_end = scene_matches[idx + 1].start() if idx + 1 < len(scene_matches) else len(yaml_str)
            scene_text = yaml_str[scene_start:scene_end]

            location = re.search(r'location:\s*["\']?([^"\']+)["\']?', scene_text)
            time_m = re.search(r'time:\s*["\']?([^"\']+)["\']?', scene_text)
            description = re.search(r'description:\s*["\']?([^"\']+)["\']?', scene_text)

            scene_data = {
                'scene_id': scene_id,
                'location': location.group(1) if location else "",
                'time': time_m.group(1) if time_m else "",
                'description': description.group(1) if description else "",
                'items': [],
                'dialogues': [],
                'actions': []
            }

            # 提取 items（新格式）
            item_pattern = r'-\s*type:\s*(\w+)\s*\n\s*character:\s*["\']?([^"\']+)["\']?\s*\n(?:\s*line:\s*["\']?([^"\']*)["\']?\s*\n)?(?:\s*action:\s*["\']?([^"\']*)["\']?)?'
            for item_match in re.finditer(item_pattern, scene_text):
                item_type = item_match.group(1)
                character = item_match.group(2)
                line = item_match.group(3) or ""
                action = item_match.group(4) or ""
                scene_data['items'].append({
                    'type': item_type,
                    'character': character,
                    'line': line,
                    'action': action
                })

            # 如果没有 items，回退到旧格式
            if not scene_data['items']:
                dialogue_pattern = r'character:\s*["\']?([^"\']+)["\']?\s*\n\s*line:\s*["\']?([^"\']+)["\']?'
                for d_match in re.finditer(dialogue_pattern, scene_text):
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


def _ensure_scene_defaults(scene_data: dict):
    """确保场景数据中所有字段都有默认值"""
    scene_data.setdefault("location", "")
    scene_data.setdefault("time", "")
    scene_data.setdefault("description", "")
    scene_data.setdefault("items", [])
    scene_data.setdefault("dialogues", [])
    scene_data.setdefault("actions", [])
    for item in scene_data.get("items", []):
        item.setdefault("type", "action")
        item.setdefault("character", "")
        item.setdefault("action", "")
        item.setdefault("line", "")
    for dialogue in scene_data.get("dialogues", []):
        dialogue.setdefault("character", "")
        dialogue.setdefault("line", "")
        dialogue.setdefault("action", "")
    for action in scene_data.get("actions", []):
        action.setdefault("character", "")
        action.setdefault("action", "")


def convert_novel(title: str, text: str, api_key: str = "", api_base: str = "", model: str = "") -> ScreenplayOutput:
    """将小说文本转换为剧本（非流式）"""
    chapters = split_chapters(text)
    all_scenes = []
    scene_counter = 0
    prev_context = ""

    for i, chapter in enumerate(chapters):
        prompt = CHAPTER_PROMPT.format(
            title=title,
            chapter_num=i + 1,
            prev_context=prev_context,
            text=chapter["text"]
        )
        response = call_llm(prompt, api_key, api_base, model)
        data = extract_yaml_from_response(response)

        if data and "scenes" in data:
            for scene_data in data["scenes"]:
                scene_counter += 1
                scene_data["scene_id"] = scene_counter
                _ensure_scene_defaults(scene_data)
                try:
                    all_scenes.append(Scene(**scene_data))
                except Exception as e:
                    print(f"场景 {scene_counter} 解析失败: {e}")
                    continue

            if data["scenes"]:
                last_scene = data["scenes"][-1]
                prev_context = f"场景{last_scene.get('scene_id', '')}: {last_scene.get('description', '')}"

    return ScreenplayOutput(title=title, scenes=all_scenes)


def convert_novel_stream(title: str, text: str, api_key: str = "", api_base: str = "", model: str = ""):
    """流式转换：逐步返回 YAML 文本，支持进度推送"""
    chapters = split_chapters(text)
    total_chapters = len(chapters)
    all_scenes = []
    scene_counter = 0
    prev_context = ""

    for i, chapter in enumerate(chapters):
        # 推送进度
        yield {
            "type": "progress",
            "data": {
                "current": i + 1,
                "total": total_chapters,
                "percentage": int((i + 1) / total_chapters * 100),
                "status": f"正在处理第 {i + 1}/{total_chapters} 章",
            },
        }

        prompt = CHAPTER_PROMPT.format(
            title=title,
            chapter_num=i + 1,
            prev_context=prev_context,
            text=chapter["text"]
        )
        full_response = ""
        for chunk in call_llm_stream(prompt, api_key, api_base, model):
            full_response += chunk
            yield {"type": "chunk", "data": chunk}

        data = extract_yaml_from_response(full_response)
        if data and "scenes" in data:
            for scene_data in data["scenes"]:
                scene_counter += 1
                scene_data["scene_id"] = scene_counter
                _ensure_scene_defaults(scene_data)
                try:
                    all_scenes.append(Scene(**scene_data))
                except Exception as e:
                    print(f"场景 {scene_counter} 解析失败: {e}")
                    continue

            if data["scenes"]:
                last_scene = data["scenes"][-1]
                prev_context = f"场景{last_scene.get('scene_id', '')}: {last_scene.get('description', '')}"

    yield {"type": "result", "data": ScreenplayOutput(title=title, scenes=all_scenes)}
