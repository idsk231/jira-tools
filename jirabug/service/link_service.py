"""链接创建服务，负责在Jira中创建Bug与特性之间的链接关系。"""

import pandas as pd
from typing import Dict, Any, List, Tuple
import time
from tqdm import tqdm

from ..core.jira_client import JiraClient


def create_links_from_analysis(
    jira_client: JiraClient,
    analysis_file: str,
    bug_col: str = "Bug ID",
    feature_col: str = "相关特性",
    link_type: str = "Relates",
    dry_run: bool = False,
    skip_existing: bool = False,
    debug: bool = False
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
        debug: 是否启用调试模式

    Returns:
        成功计数, 跳过计数, 错误计数的元组
    """
    success_count = 0
    skip_count = 0
    error_count = 0

    try:
        # 加载关联关系表
        df = pd.read_excel(analysis_file)
        print(f"已加载 {len(df)} 条关联关系记录")

        # 检查必要的列是否存在
        if bug_col not in df.columns or feature_col not in df.columns:
            raise ValueError(f"输入文件缺少必要的列: {bug_col} 或 {feature_col}")

        print(f"开始创建链接, 链接类型: {link_type}")

        for _, row in tqdm(df.iterrows(), total=len(df)):
            bug_id = row[bug_col]
            feature_id = row[feature_col]

            # 跳过空值或"未确定"
            if pd.isna(bug_id) or pd.isna(feature_id) or feature_id == "未确定":
                skip_count += 1
                continue

            # 检查是否已存在链接
            link_exists = False
            if skip_existing:
                try:
                    # 获取issue的链接
                    issue_links = jira_client.get_issue_links(bug_id)

                    # 检查是否已链接到特性
                    for link in issue_links:
                        linked_key = None
                        if hasattr(link, 'outwardIssue'):
                            linked_key = link.outwardIssue.key
                        elif hasattr(link, 'inwardIssue'):
                            linked_key = link.inwardIssue.key

                        if linked_key == feature_id:
                            link_exists = True
                            break
                except Exception as e:
                    if debug:
                        print(f"检查链接时发生错误: {str(e)}")

            if link_exists:
                if debug:
                    print(f"跳过已存在的链接: {bug_id} -> {feature_id}")
                skip_count += 1
                continue

            # 干运行模式
            if dry_run:
                print(f"将创建链接: {bug_id} -> {feature_id}")
                success_count += 1
                continue

            # 创建链接
            if jira_client.create_link(bug_id, feature_id, link_type):
                success_count += 1
            else:
                error_count += 1
                if debug:
                    print(f"创建链接失败: {bug_id} -> {feature_id}")

            # 添加短暂延迟，避免API限制
            time.sleep(0.5)

    except Exception as e:
        if debug:
            import traceback
            traceback.print_exc()
        raise e

    return success_count, skip_count, error_count