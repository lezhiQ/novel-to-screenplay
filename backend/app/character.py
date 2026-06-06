from backend.app.models import ScreenplayOutput, CharacterInfo


def extract_characters(screenplay: ScreenplayOutput) -> list[CharacterInfo]:
    """从剧本中提取角色信息"""
    characters: dict[str, CharacterInfo] = {}

    for scene in screenplay.scenes:
        scene_characters: set[str] = set()

        # 从 items 列表提取（新格式）
        for item in scene.items:
            name = item.character
            if not name:
                continue
            scene_characters.add(name)

            if name not in characters:
                characters[name] = CharacterInfo(name=name)

            if item.type == "dialogue":
                characters[name].dialogue_count += 1

            if item.action:
                characters[name].actions.append(item.action)

        # 兼容旧格式：从 dialogues 和 actions 列表提取
        for dialogue in scene.dialogues:
            name = dialogue.character
            if not name:
                continue
            scene_characters.add(name)
            if name not in characters:
                characters[name] = CharacterInfo(name=name)
            characters[name].dialogue_count += 1
            if dialogue.action:
                characters[name].actions.append(dialogue.action)

        for action in scene.actions:
            name = action.character
            if not name:
                continue
            scene_characters.add(name)
            if name not in characters:
                characters[name] = CharacterInfo(name=name)
            if action.action:
                characters[name].actions.append(action.action)

        # 统计出场场景数
        for name in scene_characters:
            characters[name].scene_count += 1
            # 记录首次出现场景
            if characters[name].first_appearance is None:
                characters[name].first_appearance = f"场景 {scene.scene_id}"

    # 限制每个角色的动作列表，只保留前 5 个代表性动作
    for char in characters.values():
        char.actions = char.actions[:5]

    return list(characters.values())
