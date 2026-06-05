import json
import yaml
from backend.app.models import ScreenplayOutput


def export_yaml(screenplay: ScreenplayOutput) -> str:
    """导出为 YAML 格式字符串"""
    data = screenplay.model_dump()
    return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)


def export_json(screenplay: ScreenplayOutput) -> str:
    """导出为 JSON 格式字符串"""
    data = screenplay.model_dump()
    return json.dumps(data, ensure_ascii=False, indent=2)
