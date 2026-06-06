import pytest
from backend.app.models import NovelInput, Dialogue, Action, Scene, ScreenplayOutput


class TestNovelInput:
    def test_valid_input(self):
        inp = NovelInput(text="这是一段足够长的小说文本内容用于测试")
        assert inp.title == "未命名作品"
        assert len(inp.text) >= 10

    def test_custom_title(self):
        inp = NovelInput(text="这是一段足够长的小说文本内容", title="自定义标题")
        assert inp.title == "自定义标题"

    def test_text_too_short(self):
        with pytest.raises(Exception):
            NovelInput(text="太短")


class TestDialogue:
    def test_basic_dialogue(self):
        d = Dialogue(character="林小雨", line="你好")
        assert d.type == "dialogue"
        assert d.action == ""

    def test_with_action(self):
        d = Dialogue(character="陈默", line="坐吧", action="微笑")
        assert d.action == "微笑"


class TestAction:
    def test_basic_action(self):
        a = Action(character="林小雨", action="推开门")
        assert a.type == "action"
        assert a.character == "林小雨"


class TestScene:
    def test_scene_with_items(self):
        scene = Scene(
            scene_id=1,
            location="咖啡馆",
            items=[
                {"type": "action", "character": "A", "action": "走进来"},
                {"type": "dialogue", "character": "A", "line": "你好"},
            ]
        )
        assert len(scene.items) == 2
        assert scene.items[0].type == "action"
        assert scene.items[1].type == "dialogue"

    def test_scene_defaults(self):
        scene = Scene(scene_id=1)
        assert scene.location == ""
        assert scene.time == ""
        assert scene.items == []
        assert scene.dialogues == []
        assert scene.actions == []

    def test_scene_backward_compat(self):
        """旧格式 actions+dialogues 仍然可用"""
        scene = Scene(
            scene_id=1,
            actions=[{"character": "A", "action": "走路"}],
            dialogues=[{"character": "A", "line": "你好"}]
        )
        assert len(scene.actions) == 1
        assert len(scene.dialogues) == 1


class TestScreenplayOutput:
    def test_full_output(self):
        output = ScreenplayOutput(
            title="测试剧本",
            scenes=[
                Scene(scene_id=1, location="A"),
                Scene(scene_id=2, location="B"),
            ]
        )
        assert len(output.scenes) == 2
        assert output.author == ""

    def test_model_dump(self):
        output = ScreenplayOutput(title="测试", scenes=[])
        data = output.model_dump()
        assert isinstance(data, dict)
        assert data["title"] == "测试"
