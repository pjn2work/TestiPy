import yaml
import json


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds*1000:.1f}ms"
    if seconds < 60:
        return f"{seconds:.3f}sec"

    secs = seconds % 60
    minutes = int(seconds // 60) % 60
    if seconds < 3600:
        return f"{minutes:02d}:{secs:02.0f}min"

    hours = int(seconds // 3600)
    return f"{hours}:{minutes:02d}:{secs:02.0f}hrs"


def prettify(json_obj, as_yaml: bool = False, indent: int = 3) -> str:
    """prettify json to string"""
    try:
        if isinstance(json_obj, str):
            json_obj = json.loads(json_obj)
        if isinstance(json_obj, (dict, list, tuple, set)):
            if as_yaml:
                return yaml.dump(json_obj, allow_unicode=True).replace("\\n", "\n")
            return json.dumps(json_obj, indent=indent).replace("\\n", "\n")
    except:
        pass
    return _dict2pstr(json_obj, indent=indent)


def _dict2pstr(data, sp: str = "", indent: int = 3):
    """prettify dicts to string"""
    if isinstance(data, dict):
        if len(data) == 0:
            return "{}"

        res = "{\n"
        for k, v in data.items():
            if isinstance(k, str):
                k = f'"{k}"'
            res += sp + " " * indent + f"{k}: " + _dict2pstr(v, sp=sp + " " * indent, indent=indent) + ",\n"

        return res + sp + "}"
    elif isinstance(data, (list, tuple, set)):
        if len(data) == 0:
            return "[]"

        res = "[\n"
        for v in data:
            res += sp + " " * indent + _dict2pstr(v, sp=sp + " " * indent, indent=indent) + ",\n"

        return res + sp + "]"
    elif isinstance(data, str):
        return f'"{data}"'

    return str(data)

