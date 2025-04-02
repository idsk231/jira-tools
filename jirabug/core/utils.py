"""通用工具函数模块。"""

import os
import json
from typing import Any, Dict, List, Optional


def ensure_dir(directory: str) -> None:
    """
    确保目录存在，如果不存在则创建

    Args:
        directory: 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def save_json(data: Any, filepath: str, pretty: bool = True) -> None:
    """
    保存数据到JSON文件

    Args:
        data: 要保存的数据
        filepath: 文件路径
        pretty: 是否美化输出
    """
    ensure_dir(os.path.dirname(filepath))

    with open(filepath, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            json.dump(data, f, ensure_ascii=False)


def load_json(filepath: str) -> Any:
    """
    从JSON文件加载数据

    Args:
        filepath: 文件路径

    Returns:
        加载的数据
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)