# 剧本 YAML Schema 设计文档

## 概述

本文档定义了 AI 小说转剧本工具输出的 YAML Schema 规范。该 Schema 用于描述从小说文本自动转换而来的结构化剧本数据。

## 设计目标

1. **可读性**：编剧和创作者能直接阅读和编辑
2. **结构化**：便于程序解析和后续处理
3. **完整性**：覆盖剧本的核心要素（场景、对话、动作）
4. **时序性**：保持动作和对话的时间顺序
5. **扩展性**：支持未来添加新字段（如音效、灯光等）

## Schema 定义

```yaml
# 顶层结构
title: string          # 必填 - 剧本标题
author: string         # 可选 - 原作/编剧
scenes:                # 必填 - 场景列表
  - scene_id: integer  # 必填 - 场景编号（从 1 开始递增）
    location: string   # 必填 - 场景地点（INT./EXT. 格式）
    time: string       # 可选 - 时间（日/夜/黄昏等）
    description: string # 可选 - 场景概述
    items:             # 必填 - 有序的动作和对话列表（新格式）
      - type: string   # 必填 - 类型标识："action" 或 "dialogue"
        character: string  # 必填（dialogue）/ 可选（action）- 角色名称
        line: string       # 必填（dialogue）- 台词内容
        action: string     # 可选 - 伴随动作/表情
    dialogues:         # 对话列表（兼容旧格式）
      - character: string  # 必填 - 角色名称
        line: string       # 必填 - 台词内容
        action: string     # 可选 - 伴随动作/表情
    actions:           # 动作/舞台指示列表（兼容旧格式）
      - character: string  # 可选 - 相关角色
        action: string     # 必填 - 动作或场景描述
```

## 设计理由

### 1. 为什么使用 items 列表？

传统的剧本格式将对话（dialogues）和动作（actions）分开存储，但这会导致**时序信息丢失**。在实际剧本中，动作和对话是交替发生的：

```
林小雨推开门（动作）
林小雨："请问这里有人吗？"（对话）
陈默抬起头（动作）
陈默："没有，请坐。"（对话）
林小雨放下背包（动作）
```

使用 `items` 列表可以：
- **保持时间顺序**：动作和对话按发生顺序排列
- **便于演员理解**：演员可以按顺序阅读，理解场景 flow
- **支持复杂场景**：一个场景可能包含多个角色的交替动作和对话
- **便于编辑**：用户可以在预览界面直接编辑，保持顺序

### 2. 为什么保留 dialogues 和 actions 字段？

为了**向后兼容**，我们保留了旧格式的 `dialogues` 和 `actions` 字段。系统会优先使用 `items` 列表，如果为空则回退到旧格式。

### 3. 为什么需要 scene_id？

- 场景编号是剧本的基本组织单位
- 便于引用和修改（"第 5 场需要改一下"）
- 支持后续功能：场景排序、场景跳转、分章节管理
- 用于分场景导航功能

### 4. 为什么 dialogue 中有可选的 action 字段？

对话中的伴随动作（如"笑着说"、"叹了口气"）是小说中常见的表达方式。将其作为 dialogue 的子字段而非独立 action，是因为：
- 它与特定台词紧密关联
- 便于演员理解表演意图
- 保持对话流的完整性

### 5. 为什么 location 使用 INT./EXT. 格式？

采用好莱坞标准格式（INT./EXT. 地点 - 时间）可以：
- **专业性**：符合行业标准，便于专业编剧使用
- **可读性**：一眼就能看出是室内还是室外场景
- **导出友好**：导出 DOCX 时可以直接使用标准格式

### 6. 字段类型说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 剧本标题 |
| author | string | 否 | 原作者或编剧 |
| scenes | array | 是 | 场景列表 |
| scene_id | integer | 是 | 场景编号 |
| location | string | 是 | 场景地点（INT./EXT. 格式） |
| time | string | 否 | 时间信息（日/夜/黄昏等） |
| description | string | 否 | 场景概述 |
| items | array | 是 | 有序的动作和对话列表 |
| items[].type | string | 是 | 类型标识："action" 或 "dialogue" |
| items[].character | string | 视类型 | 角色名称（dialogue 必填，action 可选） |
| items[].line | string | 视类型 | 台词内容（dialogue 必填） |
| items[].action | string | 否 | 伴随动作或表情 |
| dialogues | array | 否 | 对话列表（兼容旧格式） |
| actions | array | 否 | 动作列表（兼容旧格式） |

## 示例

```yaml
title: "咖啡馆之恋"
author: "AI 改编"
scenes:
  - scene_id: 1
    location: "INT. 咖啡馆角落 - 清晨"
    time: "清晨"
    description: "林小雨走进咖啡馆，遇到陈默"
    items:
      - type: action
        character: "林小雨"
        action: "推开门，风铃发出清脆的声响"
      - type: action
        character: "林小雨"
        action: "环顾四周，发现只有一个人坐在窗边"
      - type: dialogue
        character: "林小雨"
        line: "请问这里有人吗？"
        action: "指着对面的椅子"
      - type: action
        character: "陈默"
        action: "抬起头，愣了一下"
      - type: dialogue
        character: "陈默"
        line: "没有，请坐。"
        action: "微笑"
      - type: action
        character: "林小雨"
        action: "放下背包，坐了下来"
```

## 与旧格式的兼容

系统支持两种格式：

### 新格式（推荐）
使用 `items` 列表，保持动作和对话的时间顺序。

### 旧格式（兼容）
使用分开的 `dialogues` 和 `actions` 列表。系统会自动将旧格式转换为新格式进行显示。

## 扩展性

Schema 支持未来添加新字段：

```yaml
scenes:
  - scene_id: 1
    location: "INT. 咖啡馆角落 - 清晨"
    # 未来可扩展字段：
    lighting: "柔和的晨光"      # 灯光指示
    sound: "轻柔的背景音乐"     # 音效指示
    camera: "中景"              # 镜头指示
    mood: "温馨"                # 氛围指示
```

## 使用场景

1. **编剧编辑**：直接在 YAML 文件中编辑剧本
2. **程序解析**：前端/后端程序解析 YAML 进行显示和处理
3. **格式转换**：导出为 DOCX、PDF 等格式
4. **数据分析**：统计角色出场、台词数量等
5. **版本管理**：YAML 格式便于 Git 版本控制
