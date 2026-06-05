"""
剧本 YAML Schema 定义与校验
"""
import yaml
from backend.app.models import ScreenplayOutput


def validate_screenplay(data: dict) -> tuple[bool, str]:
    """校验剧本数据是否符合 Schema"""
    try:
        ScreenplayOutput(**data)
        return True, "校验通过"
    except Exception as e:
        return False, str(e)


def to_yaml(screenplay: ScreenplayOutput) -> str:
    """将剧本对象转为 YAML 字符串"""
    data = screenplay.model_dump()
    return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)


def parse_yaml(yaml_str: str) -> dict:
    """解析 YAML 字符串为字典"""
    return yaml.safe_load(yaml_str)
