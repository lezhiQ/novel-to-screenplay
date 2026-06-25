# 408 知识点与项目对应问答手册

> **面试考察维度提醒**：
> - **技术深度** — 能否用 408 理论解释技术选型的理由（如 SSE vs WebSocket、异步 I/O 原理）
> - **产品思维** — 是否理解目标用户、痛点、功能价值与差异化优势（如 Q3）
> - **工程能力** — 代码组织、容错设计、测试覆盖、性能优化意识（如 DOCX 内存管理、YAML 三级降级）
>
> 目标：面试时能用 408（操作系统、计算机网络、数据结构与算法、组成原理）的知识来分析项目中的设计取舍，而不是只讲功能。
>
> 每条回答结构：结论 → 理论 → 项目实践 → 延伸

---

## 1. 并发与异步：SSE 为什么比 WebSocket 更适合这个场景？

**结论**：SSE 是单向流（服务端→客户端），刚好匹配"LLM 流式生成剧本"这一场景；WebSocket 是双向的，引入不必要的复杂性。

**理论（计算机网络）**：
- SSE 基于 HTTP，使用长连接 + 分块传输（Chunked Transfer），服务端通过 `text/event-stream` MIME 类型持续推送事件。客户端用 `EventSource` API 监听，自动处理重连。
- WebSocket 是全双工协议，需要在 HTTP 升级后建立独立的双向通道。
- SSE 是服务端推，WebSocket 可双向传。

**项目实践**：
- 我们的场景是"用户提交小说 → LLM 逐步生成剧本 → 前端逐步展示"，完全是单向数据流。
- `main.py` 中用 `sse-starlette` 的 `EventSourceResponse` 包装异步生成器 `event_generator()`，每收到 LLM 的一个 chunk 就通过 SSE 推送给前端。
- 前端 `app.js` 用 `fetch` + `ReadableStream` 逐块解析，边收边渲染，同时更新进度条。
- 如果用 WebSocket，我们需要额外维护连接状态、心跳、消息协议格式——而这些对单向推送场景来说是过度设计。

**延伸（面试官可能追问）**：
- SSE 不支持双向通信，如果需要前端同时回传编辑内容怎么办？→ 可以 SSE 用于进度展示 + 普通 POST 用于编辑提交，两者走不同的通道，互不干扰。
- SSE 的重连机制是什么？→ 客户端可以通过 `Last-Event-ID` 头告知服务端上次收到的位置，服务端可以从该位置继续推送。

---

## 2. FastAPI 的异步模型是怎么工作的？

**结论**：FastAPI 基于 Starlette + uvicorn（ASGI 服务器），利用 Python 的 `async/await` 和事件循环实现高并发，I/O 密集型操作（如 LLM API 调用）不会阻塞其他请求。

**理论（操作系统 + 计算机网络）**：
- 同步 I/O：请求线程在处理 LLM API 调用时会被阻塞，直到网络响应回来才能处理下一个请求，线程资源浪费在等待上。
- 异步 I/O：使用事件循环（Event Loop），I/O 操作通过 `await` 挂起当前协程，事件循环去处理其他就绪请求，I/O 完成后回调恢复协程。本质是用户态的协作式多任务。
- uvicorn 是 ASGI 服务器，底层用 `uvloop`（libuv 的 Python 绑定）实现高效的异步事件通知机制（epoll/kqueue）。

**项目实践**：
- `convert_stream` 接口用 `async def` 声明为异步端点，内部的 `event_generator()` 是异步生成器，通过 `yield` 逐个产出数据块。
- LLM 调用 `call_llm_stream()` 用 OpenAI SDK 的 `stream=True` 参数，SDK 内部也是异步读取网络流，不阻塞事件循环。
- 文件上传接口 `upload_file` 是同步的，因为文件解析（docx/pdf）是 CPU 密集型操作，同步执行即可，不会影响异步端点。

**延伸**：
- 什么时候该用 `async def`，什么时候用普通 `def`？→ I/O 密集型（网络请求、数据库查询）用 async，CPU 密集型（正则匹配、文件解析）用普通 def，避免阻塞事件循环。
- Python GIL 对异步有什么影响？→ GIL 限制的是多线程并行计算，不影响异步协程，因为异步是单线程内的协作式调度。

---

## 3. 小说文本解析的算法复杂度分析

**结论**：使用正则表达式按章节分割，时间复杂度 O(n)，n 为文本长度；角色提取也用正则匹配，同样 O(n)。

**理论（数据结构与算法）**：
- `re.split(pattern, text)` 会对文本做一次线性扫描，正则引擎使用回溯法匹配。对于我们写的章节模式 `((?:第[一二三四五六七八九十百千\d]+章|Chapter\s*\d+)...)`，没有嵌套量词和重叠捕获组，不会触发指数级回溯。
- 拆分后遍历 `parts` 数组构建章节字典，这是 O(n) 的线性遍历。
- 总体时间复杂度 O(n)，空间复杂度 O(n)（存储拆分后的字符串数组）。

**项目实践**：
- `parser.py` 的 `split_chapters()` 用 `re.split()` 按章节标题分割文本，支持"第一章"、"Chapter 1"等多种格式。
- 如果文本中没有检测到章节标记，整个文本作为一个章节处理（fallback），保证鲁棒性。
- `extract_characters()` 用正则 `[一-龥]{1,4}(?:说|道|问|...)` 匹配中文名字+说话动词的模式，启发式提取角色列表。

**延伸**：
- 如果想更精确地解析，可以用有限状态机（FSM）替代正则。状态包括：IN_TITLE、IN_BODY、IN_DIALOGUE，遇到章节标题模式时进入新状态。这样能处理嵌套和边界情况，但实现复杂度更高。
- 正则回溯问题：如果模式写成 `(第.+章)` 这种贪婪匹配，在长文本中可能导致性能退化。我们应该尽量用非贪婪和精确字符集。

---

## 4. YAML 数据结构的存储与解析

**结论**：YAML 作为中间数据格式，本质是用嵌套列表和字典来表示树状结构，Python 的 `yaml.safe_load` 安全解析，时间复杂度 O(n)。

**理论（数据结构）**：
- YAML 的剧本结构是一棵树：根节点（title/scenes）→ 场景节点（scene_id/location/items）→ 子元素节点（dialogue/action）。
- Python 中解析后映射为嵌套的 `list` 和 `dict`，在内存中就是一棵多叉树。
- `yaml.safe_load` 比 `yaml.load` 安全，因为它只允许基本的 YAML 标签，不会执行任意 Python 对象反序列化（防止代码注入）。

**项目实践**：
- `models.py` 用 Pydantic Model 定义数据类型：`ScreenplayOutput` 包含 `title` 和 `scenes: list[Scene]`，`Scene` 包含 `items: list[Union[Action, Dialogue]]`。
- LLM 输出 YAML 字符串后，`converter.py` 先通过正则提取代码块内容，再用 `yaml.safe_load` 解析为字典。
- 解析失败时有三级降级策略：预处理修复引号问题 → 修复缩进/冒号格式 → 宽松正则解析。最终如果都不成功则返回 None。

**延伸**：
- 为什么不直接用 JSON？→ JSON 不支持注释，人类可读性不如 YAML；但 JSON 解析更快且不会有格式歧义。YAML 更适合剧本这种需要人工编辑的场景。
- Pydantic 的校验开销是多少？→ 每次解析后用 `ScreenplayOutput(**data)` 做类型校验，这是 O(m)，m 为场景数量，校验失败会抛出 `ValidationError` 被 try-catch 捕获。

---

## 5. Prompt 工程与 Token 管理

**结论**：SYSTEM_PROMPT 约 1500 字，CONVERT_PROMPT 约 500 字，CHAPTER_PROMPT 约 600 字。通过将长篇小说拆分为章节，控制单次请求的 token 数在模型上下文窗口内。

**理论（计算机系统 / 编译原理角度）**：
- LLM API 有最大上下文长度限制（如小米 MiMo 通常是 8K/32K token）。超过限制的请求会被截断或报错。
- Tokenization 将文本切分为 subword 单元，中文大约 1 字 ≈ 1~2 token。
- 这是一个典型的"分治法"问题：当问题规模超过模型上下文窗口时，将任务拆分为多个子任务，逐个处理后再合并结果。

**项目实践**：
- `parser.py` 的 `split_chapters()` 将长篇小说按章节拆分成多个小块，每章独立调用 LLM。
- `converter.py` 的 `convert_novel()` 中维护 `prev_context` 变量，将上一章最后一个场景的描述传递给下一章，保证章节间的连贯性。这类似于编译器中的"跨函数优化"——局部独立，全局协调。
- 非流式调用 `call_llm()` 一次性返回，流式调用 `call_llm_stream()` 边生成边返回。两者共享同一个 Prompt 模板。

**延伸**：
- 如果小说只有 3 章但每章很长怎么办？→ 可以在章节内部再按段落或固定 token 数拆分，即"章内分块"。
- 温度参数设为 0.3 的原因？→ 剧本转换需要格式稳定性和准确性，不需要创造性，所以用较低的温度。

---

## 6. DOCX 导出的内存管理与文件结构

**结论**：DOCX 本质是 ZIP 压缩包内的 XML 文件集合。我们用 `python-docx` 在内存中构建文档树，最后通过 `BytesIO` 输出字节流，不写磁盘。

**理论（操作系统 / 文件系统）**：
- DOCX 是 Office Open XML 格式，底层是 ZIP 压缩的目录结构，包含 `word/document.xml`（正文）、`word/styles.xml`（样式）等。
- 传统做法是先写临时文件再读取发送，涉及磁盘 I/O。我们用 `BytesIO` 在内存中完成整个构建过程，避免磁盘操作。
- `buffer.seek(0)` 将文件指针重置到开头，供 `Response` 读取。这是标准的流式内存操作。

**项目实践**：
- `export.py` 的 `export_docx()` 接收 `ScreenplayOutput` 对象，用 `Document()` 创建空白文档。
- 设置页面边距（2.54cm 上下，3.7cm 左，2.54cm 右）、默认字体（Courier New 12pt），符合好莱坞剧本标准格式。
- 页眉放剧本标题（灰色小字），页脚用 Word 域代码实现自动页码（`{ PAGE }`）。
- 遍历 `screenplay.scenes`，每个场景按 Hollywood 格式输出：场景标题（粗体）→ 描述（斜体）→ items（对话角色名大写 + 台词 + 动作斜体）。
- 最后 `FADE OUT.` 右对齐结尾，`doc.save(buffer)` 写入内存，返回字节串。

**延伸**：
- 如果剧本非常大（几百个场景），`BytesIO` 的内存占用会很高。可以改用分块生成 + 流式 ZIP 打包来降低峰值内存。
- 为什么选择 `python-docx` 而不是直接生成 XML？→ 抽象层次更高，代码更易读，但对于精细排版控制（如剧本的特殊缩进）需要额外调试。

---

## 7. 前后端通信与 RESTful API 设计

**结论**：遵循 REST 风格，资源（小说、剧本、角色）通过 URL 路径表达，操作通过 HTTP 方法表达，数据交换用 JSON/YAML。

**理论（计算机网络）**：
- RESTful 设计原则：名词性 URL 路径（`/api/convert`）、幂等的 GET/PUT/DELETE、非幂等的 POST、正确的状态码（200/400/500）。
- CORS（跨域资源共享）：前端和后端在不同端口运行时，浏览器会先发 OPTIONS 预检请求，后端通过 `CORSMiddleware` 允许跨域。
- 文件上传用 `multipart/form-data` 编码，`UploadFile` 类型自动解析请求体。

**项目实践**：
- `main.py` 中定义了 8 个 API 端点：`/health`（GET，健康检查）、`/api/convert`（POST，非流式转换）、`/api/convert/stream`（POST，SSE 流式转换）、`/api/export/{yaml,json,docx}`（POST，导出）、`/api/upload`（POST，文件上传）、`/api/characters`（POST，角色提取）。
- 所有端点共享 `NovelInput` 数据模型做请求体验证，Pydantic 自动做类型检查和字段校验。
- 前端通过 `app.js` 的 `fetch()` 调用 API，流式接口用 `response.body.getReader()` 逐块读取。
- CORS 配置为 `allow_origins=["*"]`（开发环境），生产环境应限制为具体域名。

**延伸**：
- 如果要做认证怎么办？→ 加 JWT Token，在 `main.py` 中创建依赖项（Depends）验证 Token，放到所有需要认证的端点之前。
- API 版本管理：URL 中用 `/api/v1/` 前缀，向后兼容。

---

## 8. 项目整体架构与 408 知识点对应速查表

| 408 科目 | 知识点 | 项目中的体现 |
|----------|--------|-------------|
| **计算机网络** | HTTP/HTTPS 协议 | RESTful API 通信，文件上传的 multipart/form-data |
| | SSE (Server-Sent Events) | 流式转换进度推送，`text/event-stream` |
| | CORS 跨域 | FastAPI CORSMiddleware 配置 |
| | WebSocket vs SSE | 单向推送选 SSE 的理由 |
| **操作系统** | 进程/线程/协程 | uvicorn 事件循环，async/await 异步协程 |
| | I/O 模型 | 异步非阻塞 I/O（LLM API 调用）vs 同步阻塞 I/O（文件解析） |
| | 内存管理 | BytesIO 内存中构建 DOCX，避免磁盘 I/O |
| | 文件 I/O | 文件上传解析 txt/docx/pdf，UTF-8 编码处理 |
| **数据结构与算法** | 树形结构 | YAML 剧本的嵌套结构（场景→items→对话/动作） |
| | 正则表达式 | 章节分割、角色提取、YAML 内容抽取 |
| | 时间复杂度 | split_chapters O(n)，角色提取 O(n)，YAML 解析 O(n) |
| | 分治法 | 长篇小说按章节拆分，逐章处理再合并 |
| | 状态机 | parser 中维护 current_title/current_text 的状态切换 |
| **计算机组成** | 缓存思想 | prev_context 缓存上一章末尾场景，保证连贯性 |
| **软件工程** | 模块化设计 | backend/app 下每个文件单一职责 |
| | 数据校验 | Pydantic Model 做 API 输入输出校验 |
| | 容错设计 | YAML 解析三级降级策略 |
| | 测试 | pytest 覆盖 parser/models/export/API/character 各模块 |
