# AI 小说转剧本工具

将小说文本自动转换为结构化 YAML 剧本的 AI 工具。

## 功能特性

### 核心功能
- **智能解析**：自动识别章节、对话、动作描写
- **AI 转换**：基于小米 MiMo 大模型，将小说转为标准剧本格式
- **YAML 输出**：输出结构化、可编辑的 YAML 剧本文件
- **在线预览**：Web 界面实时预览转换结果
- **多格式导出**：支持 YAML / JSON / DOCX 文件下载

### 高级功能
- **流式输出**：实时显示 AI 生成过程，支持进度显示
- **分场景导航**：左侧场景列表，点击快速跳转
- **左右分屏**：桌面端支持拖拽调整分屏宽度
- **在线编辑**：支持在预览界面直接编辑剧本内容
- **角色管理**：自动提取角色信息，统计出场和台词
- **多章节处理**：支持长篇小说自动分章处理
- **文件上传**：支持 .txt / .docx / .pdf 格式文件上传
- **API 自定义**：支持用户自定义 API Key 和模型

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | Python + FastAPI |
| LLM 模型 | 小米 MiMo (mimo-v2.5-pro) |
| 前端 | HTML + CSS + JavaScript |
| 数据格式 | YAML / JSON |
| 文档导出 | python-docx (DOCX 格式) |
| 流式通信 | Server-Sent Events (SSE) |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

复制 `.env.example` 为 `.env`，填入你的小米 API Key：

```bash
cp .env.example .env
# 编辑 .env，填入 MIMO_API_KEY
```

### 3. 启动服务

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问

打开浏览器访问 http://localhost:8000

## 项目结构

```
novel-to-screenplay/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置管理
│   │   ├── models.py        # 数据模型
│   │   ├── parser.py        # 小说文本解析
│   │   ├── converter.py     # LLM 转换引擎
│   │   ├── prompts.py       # Prompt 模板
│   │   ├── character.py     # 角色提取
│   │   └── export.py        # 导出功能
│   └── tests/               # 测试用例
├── frontend/
│   ├── index.html           # Web 界面
│   ├── style.css            # 样式
│   └── app.js               # 前端逻辑
├── schema/
│   └── screenplay_schema.md # YAML Schema 设计文档
├── docs/
│   └── voiceover/           # 视频配音文件
├── samples/
│   ├── sample_novel.txt     # 示例小说
│   ├── sample_novel.docx    # 示例小说 (DOCX)
│   ├── sample_novel.pdf     # 示例小说 (PDF)
│   ├── 阿Q正傳.txt           # 示例小说
│   ├── 浮生六記.txt          # 示例小说
│   └── 狂人日記.txt          # 示例小说
├── requirements.txt
└── README.md
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |
| POST | /api/convert | 非流式转换 |
| POST | /api/convert/stream | 流式转换 (SSE) |
| POST | /api/export/yaml | 导出 YAML |
| POST | /api/export/json | 导出 JSON |
| POST | /api/export/docx | 导出 DOCX |
| POST | /api/upload | 文件上传 |
| POST | /api/characters | 角色提取 |

## 依赖说明

- **fastapi**: Web 框架
- **uvicorn**: ASGI 服务器
- **openai**: 小米 API 客户端（兼容 OpenAI 协议）
- **pyyaml**: YAML 解析
- **pydantic**: 数据校验
- **python-dotenv**: 环境变量管理
- **python-multipart**: 文件上传支持
- **sse-starlette**: Server-Sent Events 支持
- **python-docx**: DOCX 文件生成
- **PyPDF2**: PDF 文件解析
- **pytest**: 测试框架
- **httpx**: HTTP 客户端（用于测试）

## YAML Schema

详细的 Schema 设计文档请参见 [schema/screenplay_schema.md](schema/screenplay_schema.md)。

### Schema 设计亮点

1. **时序性**：使用 `items` 列表保持动作和对话的时间顺序
2. **兼容性**：保留旧格式的 `dialogues` 和 `actions` 字段
3. **专业性**：采用好莱坞标准格式（INT./EXT.）
4. **扩展性**：支持未来添加灯光、音效等字段

## 开发过程

### PR 记录

| PR | 标题 | 分支 | 状态 |
|----|------|------|------|
| #1 | 修复流式输出场景解析和动作对话排序问题 | feat/streaming-fix | ✅ 已合并 |
| #2 | 支持上传 .txt/.docx/.pdf 文件 | feat/file-upload | ✅ 已合并 |
| #3 | 添加单元测试覆盖核心模块 | feat/tests | ✅ 已合并 |
| #4 | 支持用户自定义 API Key | feat/custom-api-key | ✅ 已合并 |
| #5 | 添加剧本编辑功能和 DOCX 导出 | feat/edit-and-docx-export | ✅ 已合并 |
| #6 | 添加分场景导航和左右分屏预览 | feat/frontend-ux | ✅ 已合并 |
| #7 | 将剧本格式标准化为好莱坞专业格式 | feat/standard-format | ✅ 已合并 |
| #8 | 添加角色管理功能 | feat/character-management | ✅ 已合并 |
| #9 | 多章节分批处理，支持实时进度显示 | feat/batch-processing | ✅ 已合并 |

### Commit 分布

项目采用持续开发模式，从开题至今保持稳定的 commit 频率。

## 测试

### 运行测试

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 运行所有测试
python -m pytest backend/tests/ -v

# 运行特定测试
python -m pytest backend/tests/test_parser.py -v
```

### 测试覆盖

- **test_parser.py**: 小说文本解析测试
- **test_models.py**: 数据模型测试
- **test_export.py**: 导出功能测试
- **test_api.py**: API 接口测试
- **test_character.py**: 角色提取测试

## 演示视频

Demo 视频链接：[B 站](https://www.bilibili.com/video/BV1KcE46AEp7/)

## 复盘与反思

### 路演面试回顾

项目在路演面试环节因技术问题回答不足而未能通过。核心教训：

1. **不能脱离计算机基础谈项目**。用操作系统、计算机网络、数据结构等 408 知识来分析项目中的设计取舍，而非仅描述功能实现。
2. **需要提前准备技术深挖方向**。例如：
   - **并发与异步**：SSE 流式输出的底层原理是什么？与 WebSocket 相比为什么选 SSE？
   - **系统设计**：FastAPI 的异步模型如何工作？uvicorn 的事件循环机制是怎样的？
   - **数据结构**：小说文本解析中使用的正则匹配与状态机策略，时间复杂度如何分析？
   - **网络协议**：HTTP/HTTPS、OpenAI 兼容协议的握手流程、API Key 的安全存储与传输。
   - **数据库/存储**：如果后续引入持久化，如何选择存储方案？
3. **做一份项目 Q&A 手册感觉挺有必要的**。把可能被问到的技术问题整理成文档，提前准备答案和延伸讨论点。

### 改进计划

- 在项目中补充 `docs/interview_qa.md`，系统梳理 408 知识点与项目的对应关系
- 每个技术选型都要能说出"为什么选它"和"为什么不选其他方案"
- 下次面试前至少模拟答辩 2-3 次

## 许可证

MIT License
