import json
import yaml
from backend.app.models import ScreenplayOutput, Scene, Dialogue, Action
from backend.app.export import export_yaml, export_json


def make_sample_screenplay():
    return ScreenplayOutput(
        title="测试剧本",
        scenes=[
            Scene(
                scene_id=1,
                location="咖啡馆",
                time="日",
                description="开场场景",
                items=[
                    Action(type="action", character="林小雨", action="推开门"),
                    Dialogue(type="dialogue", character="林小雨", line="你好"),
                ],
                dialogues=[
                    Dialogue(character="林小雨", line="你好"),
                ],
                actions=[
                    Action(character="林小雨", action="推开门"),
                ],
            )
        ],
    )


class TestExportYaml:
    def test_returns_string(self):
        result = export_yaml(make_sample_screenplay())
        assert isinstance(result, str)

    def test_valid_yaml(self):
        result = export_yaml(make_sample_screenplay())
        data = yaml.safe_load(result)
        assert data["title"] == "测试剧本"
        assert len(data["scenes"]) == 1

    def test_preserves_unicode(self):
        result = export_yaml(make_sample_screenplay())
        assert "咖啡馆" in result
        assert "林小雨" in result


class TestExportJson:
    def test_returns_string(self):
        result = export_json(make_sample_screenplay())
        assert isinstance(result, str)

    def test_valid_json(self):
        result = export_json(make_sample_screenplay())
        data = json.loads(result)
        assert data["title"] == "测试剧本"
        assert data["scenes"][0]["scene_id"] == 1

    def test_unicode_not_escaped(self):
        result = export_json(make_sample_screenplay())
        assert "咖啡馆" in result
        assert "\\u" not in result
