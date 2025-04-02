"""质量分析服务，负责分析特性质量并生成报告。"""

from typing import List, Dict, Any, Optional

from ..core.jira_client import JiraClient
from ..analysis.feature_analyzer import FeatureQualityAnalyzer


def analyze_quality_from_jira(
    jira_client: JiraClient,
    jql: str,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    """
    直接从Jira分析特性质量

    Args:
        jira_client: Jira客户端
        jql: 特性筛选JQL
        use_cache: 是否使用缓存

    Returns:
        分析结果列表
    """
    # 从原feature_quality_analyzer_main.py中提取相关逻辑...

    # 获取特性与关联的bug...

    # 分析质量...

    return results


def analyze_quality_from_files(
    features_file: str,
    bugs_file: Optional[str] = None,
    relation_file: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    从文件分析特性质量

    Args:
        features_file: 特性数据文件
        bugs_file: Bug数据文件
        relation_file: 关系数据文件

    Returns:
        分析结果列表
    """
    # 从原feature_quality_analyzer_main.py中提取相关逻辑...

    analyzer = FeatureQualityAnalyzer()
    results = analyzer.analyze_features_from_files(
        features_file=features_file,
        bugs_file=bugs_file,
        bugs_relation_file=relation_file
    )

    return results