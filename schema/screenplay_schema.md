# 剧本 YAML Schema 设计文档

## 概述

本文档定义了 AI 小说转剧本工具输出的 YAML Schema 规范。该 Schema 用于描述从小说文本自动转换而来的结构化剧本数据。

## 设计目标

1. **可读性**：编剧和创作者能直接阅读和编辑
2. **结构化**：便于程序解析和后续处理
3. **完整性**：覆盖剧本的核心要素（场景、对话、动作）
4. **扩展性**：支持未来添加新字段（如音效、灯光等）

## Schema 定义

```yaml
# 顶层结构
title: string          # 必填 - 剧本标题
author: string         # 可选 - 原作/编剧
scenes:                # 必填 - 场景列表
  - scene_id: integer  # 必填 - 场景编号（从 1 开始递增）
    location: string   # 必填 - 场景地点
    time: string       # 可选 - 时间（白天/夜晚/早晨等）
    description: string # 可选 - 场景概述
    dialogues:         # 对话列表
      - character: string  # 必填 - 角色名称
        line: string       # 必填 - 台词内容
        action: string     # 可选 - 伴随动作/表情
    actions:           # 动作/舞台指示列表
      - character: string  # 可选 - 相关角色
        action: string     # 必填 - 动作或场景描述
```

## 设计理由

### 1. 为什么将 dialogue 和 action 分开？

剧本的核心是**对话**和**动作指示**两种不同性质的内容：
- **dialogue** 是角色说出的话，需要精确归属到具体角色
- **action** 是叙述性描述（如"推开门"、"看了看窗外"），用于指导表演

将它们分开可以：
- 方便后续处理（如提取纯对话用于配音）
- 结构更清晰，便于编辑
- 符合标准剧本格式惯例

### 2. 为什么需要 scene_id？

- 场景编号是剧本的基本组织单位
- 便于引用和修改（"第 5 场需要改一下"）
- 支持后续功能：场景排序、场景跳转、分章节管理

### 3. 为什么 dialogue 中有可选的 action 字段？

对话中的伴随动作（如"笑着说"、"叹了口气"）是小说中常见的表达方式。将其作为 dialogue 的子字段而非独立 action，是因为：
- 它与特定台词紧密关联
- 便于演员理解表演意图
- 保持对话流的完整性

### 4. 为什么 location 和 time 是场景级字段？

场景切换是剧本的基本结构单位。地点和时间定义了场景的"容器"，场景内的所有对话和动作都发生在这个容器中。

### 5. 字段类型说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 剧本标题 |
| author | string | 否 | 原作者或编剧 |
| scenes | array | 是 | 场景列表 |
| scene_id | integer | 是 | 场景编号 |
| location | string | 是 | 场景地点 |
| time | string | 否 | 时间信息 |
| description | string | 否 | 场景概述 |
| dialogues | array | 否 | 对话列表 |
| dialogues[].character | string | 是 | 角色名称 |
| dialogues[].line | string | 是 | 台词内容 |
| dialogues[].action | string | 否 | 伴随动作 |
| actions | array | 否 | 动作列表 |
| actions[].character | string | 否 | 相关角色 |
| actions[].action | string | 是 | 动作描述 |

## 示例

```yaml
title: "咖啡馆之恋"
author: "AI 改编"
scenes:
  - scene_id: 1
    location: "咖啡馆 - 室内"
    time: "清晨"
    description: "林小雨走进咖啡馆，遇到陈默"
    dialogues:
      - character: "林小雨"
        line: "请问这里有人吗？"
        action: "指着对面的椅子"
      - character: "陈默"
        line: "没有，请坐。"
        action: "抬起头，愣了一下"
    actions:
      - character: "林小雨"
        action: "推开门，风铃发出清脆的声响"
      - character: "林小雨"
        action: "放下背包，坐下"
```
