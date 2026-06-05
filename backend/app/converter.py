import re
import yaml
from openai import OpenAI
from backend.app.config import MIMO_API_BASE, MIMO_API_KEY, MIMO_MODEL
from backend.app.models import ScreenplayOutput, Scene, Dialogue, Action
from backend.app.prompts import SYSTEM_PROMPT, CONVERT_PROMPT
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
    """从 LLM 响应中提取 YAML 内容"""
    # 尝试提取 ```yaml ... ``` 代码块
    match = re.search(r'```yaml\s*\n(.*?)```', text, re.DOTALL)
    if match:
        return yaml.safe_load(match.group(1))
    # 尝试直接解析
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        return None


def convert_novel(title: str, text: str) -> ScreenplayOutput:
    """将小说文本转换为剧本（非流式）"""
    chapters = split_chapters(text)
    all_scenes = []
    scene_counter = 0

    for i, chapter in enumerate(chapters):
        prompt = CONVERT_PROMPT.format(title=title, text=chapter["text"])
        response = call_llm(prompt)
        data = extract_yaml_from_response(response)

        if data and "scenes" in data:
            for scene_data in data["scenes"]:
                scene_counter += 1
                scene_data["scene_id"] = scene_counter
                all_scenes.append(Scene(**scene_data))

    return ScreenplayOutput(title=title, scenes=all_scenes)


def convert_novel_stream(title: str, text: str):
    """流式转换：逐步返回 YAML 文本"""
    chapters = split_chapters(text)
    all_scenes = []
    scene_counter = 0

    for chapter in chapters:
        prompt = CONVERT_PROMPT.format(title=title, text=chapter["text"])
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
                all_scenes.append(Scene(**scene_data))

    return ScreenplayOutput(title=title, scenes=all_scenes)
