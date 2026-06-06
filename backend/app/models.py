from typing import Optional, Union
from pydantic import BaseModel, Field


class NovelInput(BaseModel):
    """小说文本输入"""
    text: str = Field(..., min_length=10, description="小说文本内容")
    title: str = Field(default="未命名作品", description="作品标题")
    api_key: Optional[str] = Field(default="", description="用户自定义 API Key")
    api_base: Optional[str] = Field(default="", description="用户自定义 API Base URL")
    model: Optional[str] = Field(default="", description="用户自定义模型名称")


class Dialogue(BaseModel):
    """单条对话"""
    type: str = Field(default="dialogue", description="类型标识")
    character: str = Field(..., description="角色名称")
    line: Optional[str] = Field(default="", description="对话内容")
    action: Optional[str] = Field(default="", description="伴随动作或表情")


class Action(BaseModel):
    """舞台指示/动作描写"""
    type: str = Field(default="action", description="类型标识")
    character: Optional[str] = Field(default="", description="相关角色")
    action: Optional[str] = Field(default="", description="动作或场景描述")


class Scene(BaseModel):
    """单个场景"""
    scene_id: int = Field(..., description="场景编号")
    location: Optional[str] = Field(default="", description="场景地点")
    time: Optional[str] = Field(default="", description="时间（白天/夜晚等）")
    description: Optional[str] = Field(default="", description="场景概述")
    items: list[Union[Action, Dialogue]] = Field(default_factory=list, description="有序的动作和对话列表")
    dialogues: list[Dialogue] = Field(default_factory=list, description="对话列表（兼容旧格式）")
    actions: list[Action] = Field(default_factory=list, description="动作列表（兼容旧格式）")


class ScreenplayOutput(BaseModel):
    """完整剧本输出"""
    title: str = Field(..., description="剧本标题")
    author: Optional[str] = Field(default="", description="原作/编剧")
    scenes: list[Scene] = Field(default_factory=list, description="场景列表")
