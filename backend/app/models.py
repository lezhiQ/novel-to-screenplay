from pydantic import BaseModel, Field


class NovelInput(BaseModel):
    """小说文本输入"""
    text: str = Field(..., min_length=10, description="小说文本内容")
    title: str = Field(default="未命名作品", description="作品标题")


class Dialogue(BaseModel):
    """单条对话"""
    character: str = Field(..., description="角色名称")
    line: str = Field(..., description="对话内容")
    action: str = Field(default="", description="伴随动作或表情")


class Action(BaseModel):
    """舞台指示/动作描写"""
    character: str = Field(default="", description="相关角色")
    action: str = Field(..., description="动作或场景描述")


class Scene(BaseModel):
    """单个场景"""
    scene_id: int = Field(..., description="场景编号")
    location: str = Field(..., description="场景地点")
    time: str = Field(default="", description="时间（白天/夜晚等）")
    description: str = Field(default="", description="场景概述")
    dialogues: list[Dialogue] = Field(default_factory=list, description="对话列表")
    actions: list[Action] = Field(default_factory=list, description="动作/指示列表")


class ScreenplayOutput(BaseModel):
    """完整剧本输出"""
    title: str = Field(..., description="剧本标题")
    author: str = Field(default="", description="原作/编剧")
    scenes: list[Scene] = Field(default_factory=list, description="场景列表")
