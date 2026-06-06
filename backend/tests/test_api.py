import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import ScreenplayOutput, Scene

client = TestClient(app)


class TestHealthEndpoint:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestConvertEndpoint:
    @patch("backend.app.main.convert_novel")
    def test_convert_success(self, mock_convert):
        mock_convert.return_value = ScreenplayOutput(
            title="测试", scenes=[Scene(scene_id=1)]
        )
        resp = client.post("/api/convert", json={
            "title": "测试", "text": "这是一段足够长的测试文本内容用于通过验证"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["title"] == "测试"

    def test_convert_empty_text(self):
        resp = client.post("/api/convert", json={"title": "t", "text": ""})
        assert resp.status_code == 422


class TestUploadEndpoint:
    def test_upload_txt(self):
        resp = client.post(
            "/api/upload",
            files={"file": ("test.txt", "第一章 测试\n\n内容".encode("utf-8"), "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "第一章" in data["text"]

    def test_upload_unsupported_format(self):
        resp = client.post(
            "/api/upload",
            files={"file": ("test.jpg", b"\xff\xd8\xff", "image/jpeg")},
        )
        assert resp.status_code == 400
        assert "不支持" in resp.json()["detail"]


class TestExportEndpoints:
    @patch("backend.app.main.convert_novel")
    def test_export_yaml(self, mock_convert):
        mock_convert.return_value = ScreenplayOutput(
            title="测试", scenes=[Scene(scene_id=1)]
        )
        resp = client.post("/api/export/yaml", json={
            "title": "测试", "text": "这是一段足够长的测试文本内容用于通过验证"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "测试" in data["content"]

    @patch("backend.app.main.convert_novel")
    def test_export_json(self, mock_convert):
        mock_convert.return_value = ScreenplayOutput(
            title="测试", scenes=[Scene(scene_id=1)]
        )
        resp = client.post("/api/export/json", json={
            "title": "测试", "text": "这是一段足够长的测试文本内容用于通过验证"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        json.loads(data["content"])  # 确保是合法 JSON
