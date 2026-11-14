"""JSON 工具：解析响应体、按路径取值

原来的 json_util.py 是空文件（0 字节），框架里引用了却没有实现，
这里补齐两个最常用的能力，供用例叠加在响应断言之上使用。
"""
import json


def to_json(text):
    """字符串转字典，解析失败返回 None 而不是抛异常"""
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return None


def get_value(data, path, default=None):
    """按 "a.b.0.c" 形式的路径取值，任意一级取不到就返回 default

    例：get_value(res_json, "data.list.0.title")
    """
    current = data
    for part in str(path).split("."):
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (IndexError, ValueError):
                return default
        elif isinstance(current, dict):
            if part not in current:
                return default
            current = current[part]
        else:
            return default
    return current


def extract_list(data, path="data.list"):
    """取列表字段，取不到返回空列表"""
    value = get_value(data, path, default=[])
    return value if isinstance(value, list) else []
