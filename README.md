# AI 小说转剧本工具

将小说文本自动转换为结构化 YAML 剧本的 AI 工具。

## 功能

- **智能解析**：自动识别章节、对话、动作描写
- **AI 转换**：基于小米 MiMo 大模型，将小说转为标准剧本格式
- **YAML 输出**：输出结构化、可编辑的 YAML 剧本文件
- **在线预览**：Web 界面实时预览转换结果
- **多格式导出**：支持 YAML / JSON 文件下载

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | Python + FastAPI |
| LLM 模型 | 小米 MiMo (mimo-v2.5-pro) |
| 前端 | HTML + CSS + JavaScript |
| 数据格式 | YAML / JSON |

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
│   │   ├── schema.py        # Schema 校验
│   │   └── export.py        # 导出功能
│   └── tests/               # 测试用例
├── frontend/
│   ├── index.html           # Web 界面
│   ├── style.css            # 样式
│   └── app.js               # 前端逻辑
├── schema/
│   └── screenplay_schema.md # YAML Schema 设计文档
├── samples/
│   └── sample_novel.txt     # 示例小说
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

## 依赖说明

- **fastapi**: Web 框架
- **uvicorn**: ASGI 服务器
- **openai**: 小米 API 客户端（兼容 OpenAI 协议）
- **pyyaml**: YAML 解析
- **pydantic**: 数据校验
- **python-dotenv**: 环境变量管理
- **python-multipart**: 文件上传支持
- **sse-starlette**: Server-Sent Events 支持

## 许可证

MIT License
