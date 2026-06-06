from backend.app.models import ScreenplayOutput, Scene, Dialogue, Action
from backend.app.character import extract_characters


def make_sample_screenplay():
    return ScreenplayOutput(
        title="测试剧本",
        scenes=[
            Scene(
                scene_id=1,
                location="INT. 咖啡馆",
                time="日",
                items=[
                    Action(type="action", character="林小雨", action="推开门"),
                    Dialogue(type="dialogue", character="林小雨", line="你好", action="微笑"),
                    Action(type="action", character="陈默", action="抬起头"),
                    Dialogue(type="dialogue", character="陈默", line="请坐"),
                ],
            ),
            Scene(
                scene_id=2,
                location="INT. 咖啡馆",
                time="夜",
                items=[
                    Dialogue(type="dialogue", character="林小雨", line="再见"),
                    Dialogue(type="dialogue", character="陈默", line="再见"),
                    Dialogue(type="dialogue", character="林小雨", line="保重"),
                ],
            ),
            Scene(
                scene_id=3,
                location="EXT. 街道",
                time="日",
                items=[
                    Dialogue(type="dialogue", character="张三", line="你好"),
                ],
            ),
        ],
    )


class TestExtractCharacters:
    def test_returns_list(self):
        result = extract_characters(make_sample_screenplay())
        assert isinstance(result, list)

    def test_extracts_all_characters(self):
        result = extract_characters(make_sample_screenplay())
        names = [c.name for c in result]
        assert "林小雨" in names
        assert "陈默" in names
        assert "张三" in names

    def test_scene_count(self):
        result = extract_characters(make_sample_screenplay())
        by_name = {c.name: c for c in result}
        assert by_name["林小雨"].scene_count == 2
        assert by_name["陈默"].scene_count == 2
        assert by_name["张三"].scene_count == 1

    def test_dialogue_count(self):
        result = extract_characters(make_sample_screenplay())
        by_name = {c.name: c for c in result}
        assert by_name["林小雨"].dialogue_count == 3  # 你好 + 再见 + 保重
        assert by_name["陈默"].dialogue_count == 2  # 请坐 + 再见
        assert by_name["张三"].dialogue_count == 1

    def test_actions_collected(self):
        result = extract_characters(make_sample_screenplay())
        by_name = {c.name: c for c in result}
        assert "推开门" in by_name["林小雨"].actions
        assert "微笑" in by_name["林小雨"].actions
        assert "抬起头" in by_name["陈默"].actions

    def test_first_appearance(self):
        result = extract_characters(make_sample_screenplay())
        by_name = {c.name: c for c in result}
        assert by_name["林小雨"].first_appearance == "场景 1"
        assert by_name["张三"].first_appearance == "场景 3"

    def test_empty_screenplay(self):
        sp = ScreenplayOutput(title="空剧本", scenes=[])
        result = extract_characters(sp)
        assert result == []

    def test_no_characters_in_scene(self):
        sp = ScreenplayOutput(
            title="测试",
            scenes=[Scene(scene_id=1, location="INT. 空房间", time="日", items=[])],
        )
        result = extract_characters(sp)
        assert result == []

    def test_actions_limited_to_five(self):
        items = [
            Dialogue(type="dialogue", character="A", line="1", action=f"动作{i}")
            for i in range(10)
        ]
        sp = ScreenplayOutput(
            title="测试",
            scenes=[Scene(scene_id=1, location="INT. 测试", time="日", items=items)],
        )
        result = extract_characters(sp)
        by_name = {c.name: c for c in result}
        assert len(by_name["A"].actions) == 5


class TestExtractCharactersOldFormat:
    """测试兼容旧格式（dialogues/actions 列表）"""

    def test_old_format_dialogues(self):
        sp = ScreenplayOutput(
            title="测试",
            scenes=[
                Scene(
                    scene_id=1,
                    location="INT. 测试",
                    time="日",
                    dialogues=[
                        Dialogue(character="林小雨", line="你好", action="挥手"),
                    ],
                    actions=[
                        Action(character="陈默", action="走过来"),
                    ],
                )
            ],
        )
        result = extract_characters(sp)
        by_name = {c.name: c for c in result}
        assert "林小雨" in by_name
        assert "陈默" in by_name
        assert by_name["林小雨"].dialogue_count == 1
        assert by_name["林小雨"].scene_count == 1
        assert "挥手" in by_name["林小雨"].actions
        assert "走过来" in by_name["陈默"].actions
