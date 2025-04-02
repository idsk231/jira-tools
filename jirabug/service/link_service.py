"""链接创建服务，负责在Jira中创建Bug与特性之间的链接关系。"""

import pandas as pd
from typing import Dict, Any, List, Tuple

from ..core.jira_client import JiraClient


def create_links_from_analysis(
    jira_client: JiraClient,
    analysis_file: str,
    bug_col: str = "Bug ID",
    feature_col: str = "相关特性",
    link_type: str = "Relates",
    dry_run: bool = False,
    skip_existing: bool = False
) -> Tuple[int, int, int]:
    """
    根据分析结果创建Jira链接

    Args:
        jira_client: Jira客户端
        analysis_file: 分析结果文件路径
        bug_col: Bug ID列名
        feature_col: 特性ID列名
        link_type: 链接类型
        dry_run: 是否仅模拟运行
        skip_existing: 是否跳过已存在的链接

    Returns:
        成功计数, 跳过计数, 错误计数的元组
    """
    # 从原jira_link_creator_main.py中提取逻辑...

    success_count = 0
    skip_count = 0
    error_count = 0

    # 实现链接创建逻辑...

    return success_count, skip_count, error_count