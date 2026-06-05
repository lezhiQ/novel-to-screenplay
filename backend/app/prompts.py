SYSTEM_PROMPT = """你是一位专业的剧本改编师。你的任务是将小说文本转换为结构化的剧本格式。

转换规则：
1. 将小说中的对话提取为角色台词，保留原文语气
2. 将叙述性文字转换为场景描述和舞台指示
3. 识别场景切换（地点变化、时间跳跃）
4. 为每条对话标注角色的伴随动作/表情
5. 保持故事的完整性和连贯性

输出要求：
- 严格按照指定的 YAML 格式输出
- 每个场景包含：scene_id, location, time, description, dialogues, actions
- 每条对话包含：character, line, action（可选）
- 每个动作包含：character, action"""


CONVERT_PROMPT = """请将以下小说文本转换为剧本格式，以 YAML 格式输出。

小说标题：{title}

小说文本：
{text}

请输出完整的 YAML 剧本，格式如下：
```yaml
title: "剧本标题"
author: "原作"
scenes:
  - scene_id: 1
    location: "场景地点"
    time: "时间"
    description: "场景描述"
    dialogues:
      - character: "角色名"
        line: "台词"
        action: "伴随动作"
    actions:
      - character: "角色名"
        action: "动作描述"
```"""

CHAPTER_PROMPT = """请将以下小说章节转换为剧本格式的一部分。

小说标题：{title}
当前章节：第 {chapter_num} 章
前一场景摘要：{prev_context}

小说文本：
{text}

请以 YAML 格式输出这个章节的场景列表（scenes），保持与前文的连贯性。"""
