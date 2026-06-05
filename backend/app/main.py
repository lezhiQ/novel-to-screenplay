import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from backend.app.models import NovelInput, ScreenplayOutput
from backend.app.converter import convert_novel, convert_novel_stream
from backend.app.export import export_yaml, export_json

app = FastAPI(title="AI 小说转剧本工具", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/convert")
def convert(input_data: NovelInput):
    """非流式转换：一次性返回完整剧本"""
    result = convert_novel(input_data.title, input_data.text)
    return {"success": True, "data": result.model_dump()}


@app.post("/api/convert/stream")
async def convert_stream(input_data: NovelInput):
    """流式转换：逐步返回 YAML 文本"""

    async def event_generator():
        for chunk in convert_novel_stream(input_data.title, input_data.text):
            yield {"data": json.dumps({"chunk": chunk}, ensure_ascii=False)}
        yield {"data": json.dumps({"done": True})}

    return EventSourceResponse(event_generator())


@app.post("/api/export/yaml")
def export_as_yaml(input_data: NovelInput):
    """转换并导出 YAML 文件"""
    result = convert_novel(input_data.title, input_data.text)
    yaml_content = export_yaml(result)
    return {"success": True, "content": yaml_content, "filename": f"{input_data.title}.yaml"}


@app.post("/api/export/json")
def export_as_json(input_data: NovelInput):
    """转换并导出 JSON 文件"""
    result = convert_novel(input_data.title, input_data.text)
    json_content = export_json(result)
    return {"success": True, "content": json_content, "filename": f"{input_data.title}.json"}


# 挂载前端静态文件
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def index():
    return FileResponse("frontend/index.html")
