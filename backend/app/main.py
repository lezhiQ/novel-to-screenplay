import json
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
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


def _api_params(input_data: NovelInput) -> dict:
    return {"api_key": input_data.api_key, "api_base": input_data.api_base, "model": input_data.model}


@app.post("/api/convert")
def convert(input_data: NovelInput):
    """非流式转换：一次性返回完整剧本"""
    result = convert_novel(input_data.title, input_data.text, **_api_params(input_data))
    return {"success": True, "data": result.model_dump()}


@app.post("/api/convert/stream")
async def convert_stream(input_data: NovelInput):
    """流式转换：逐步返回 YAML 文本"""
    params = _api_params(input_data)

    async def event_generator():
        result = None
        for chunk in convert_novel_stream(input_data.title, input_data.text, **params):
            if isinstance(chunk, str):
                yield {"data": json.dumps({"chunk": chunk}, ensure_ascii=False)}
            else:
                result = chunk
        done_payload = {"done": True}
        if result:
            done_payload["result"] = result.model_dump()
        yield {"data": json.dumps(done_payload, ensure_ascii=False)}

    return EventSourceResponse(event_generator())


@app.post("/api/export/yaml")
def export_as_yaml(input_data: NovelInput):
    """转换并导出 YAML 文件"""
    result = convert_novel(input_data.title, input_data.text, **_api_params(input_data))
    yaml_content = export_yaml(result)
    return {"success": True, "content": yaml_content, "filename": f"{input_data.title}.yaml"}


@app.post("/api/export/json")
def export_as_json(input_data: NovelInput):
    """转换并导出 JSON 文件"""
    result = convert_novel(input_data.title, input_data.text, **_api_params(input_data))
    json_content = export_json(result)
    return {"success": True, "content": json_content, "filename": f"{input_data.title}.json"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件并提取文本内容，支持 .txt/.docx/.pdf"""
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "txt":
        content = await file.read()
        text = content.decode("utf-8", errors="replace")
    elif ext == "docx":
        import docx
        content = await file.read()
        doc = docx.Document(BytesIO(content))
        text = "\n".join(p.text for p in doc.paragraphs)
    elif ext == "pdf":
        from PyPDF2 import PdfReader
        content = await file.read()
        reader = PdfReader(BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: .{ext}，请上传 .txt/.docx/.pdf 文件")

    if not text.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")

    return {"success": True, "text": text, "filename": filename}


# 挂载前端静态文件
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def index():
    return FileResponse("frontend/index.html")
