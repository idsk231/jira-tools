"""质量分析服务，负责分析特性质量并生成报告。"""

from typing import List, Dict, Any, Optional
import time
from tqdm import tqdm

from ..core.jira_client import JiraClient
from ..analysis.feature_analyzer import FeatureQualityAnalyzer


def process_jira_data(
    jira_client: JiraClient,
    jql: str,
    analyzer: FeatureQualityAnalyzer,
    use_cache: bool = False,
    debug: bool = False
) -> List[Dict[str, Any]]:
    """
    从Jira处理数据并分析特性质量

    Args:
        jira_client: Jira客户端
        jql: 特性筛选JQL
        analyzer: 特性质量分析器
        use_cache: 是否使用缓存
        debug: 是否启用调试模式

    Returns:
        分析结果列表
    """
    # 获取特性列表
    print("获取特性列表...")
    features = jira_client.get_all_issues(
        jql,
        fields=["key", "summary", "description", "status"],
        cache_key="features" if use_cache else None
    )
    print(f"找到 {len(features)} 个特性")

    if not features:
        print("没有找到特性，无法进行分析")
        return None

    # 为每个特性获取链接的bug
    feature_results = []

    print("分析特性质量...")
    for feature in tqdm(features):
        # 从Jira获取特性的元数据
        feature_data = {
            "key": feature.key,
            "summary": feature.fields.summary,
            "status": feature.fields.status.name if hasattr(feature.fields, 'status') else None
        }

        # 获取关联的bug列表
        if debug:
            print(f"\n分析特性: {feature.key} - {feature.fields.summary}")

        cache_key = f"bugs_{feature.key}" if use_cache else None
        issue_links = jira_client.get_issue_links(feature.key)

        linked_bug_keys = []
        for link in issue_links:
            linked_key = None
            if hasattr(link, 'outwardIssue'):
                linked_key = link.outwardIssue.key
            elif hasattr(link, 'inwardIssue'):
                linked_key = link.inwardIssue.key

            if linked_key:
                linked_bug_keys.append(linked_key)

        # 获取Bug详情
        linked_bugs = []
        if linked_bug_keys:
            bug_jql = f'key in ({",".join(linked_bug_keys)}) AND issuetype = Bug'
            bugs = jira_client.get_all_issues(
                bug_jql,
                fields=["key", "summary", "status", "priority", "created", "resolutiondate"],
                cache_key=cache_key
            )

            # 转换成字典格式
            for bug in bugs:
                bug_data = {
                    "key": bug.key,
                    "summary": bug.fields.summary,
                    "status": bug.fields.status.name if hasattr(bug.fields, 'status') else None,
                    "priority": bug.fields.priority.name if hasattr(bug.fields, 'priority') and bug.fields.priority else "Unknown",
                    "created": str(bug.fields.created) if hasattr(bug.fields, 'created') else None,
                    "resolutiondate": str(bug.fields.resolutiondate) if hasattr(bug.fields, 'resolutiondate') else None
                }

                # 获取severity字段，如果有的话
                if hasattr(jira_client, 'severity_field') and jira_client.severity_field:
                    custom_field = getattr(bug.fields, jira_client.severity_field, None)
                    if custom_field:
                        bug_data['severity'] = custom_field.value

                linked_bugs.append(bug_data)

        if debug:
            print(f"找到 {len(linked_bugs)} 个关联的Bug")

        # 分析质量
        result = analyzer.analyze_feature_quality(feature_data, linked_bugs)
        feature_results.append(result)

        # 避免过快请求
        time.sleep(0.2)

    return feature_results


def print_summary_statistics(results: List[Dict[str, Any]]) -> None:
    """
    打印摘要统计信息

    Args:
        results: 分析结果列表
    """
    if not results:
        return

    # 计算基本统计数据
    total_features = len(results)
    total_bugs = sum(r['total_bugs'] for r in results)
    avg_bugs_per_feature = total_bugs / total_features if total_features > 0 else 0

    # 质量等级分布
    grade_counts = {}
    for result in results:
        grade = result['quality_grade']
        if grade not in grade_counts:
            grade_counts[grade] = 0
        grade_counts[grade] += 1

    # 打印统计信息
    print("\n=== 质量分析摘要 ===")
    print(f"分析的特性数量: {total_features}")
    print(f"总Bug数量: {total_bugs}")
    print(f"平均每个特性的Bug数量: {avg_bugs_per_feature:.2f}")

    print("\n质量等级分布:")
    for grade in sorted(grade_counts.keys()):
        count = grade_counts[grade]
        percentage = count / total_features * 100
        print(f"  {grade}: {count} ({percentage:.1f}%)")

    # 寻找问题最多的特性
    if results:
        most_bugs = max(results, key=lambda r: r['total_bugs'])
        print(f"\n问题最多的特性: {most_bugs['feature_key']} ({most_bugs['total_bugs']} bugs)")

        # 质量最低的特性
        lowest_quality = min(results, key=lambda r: r['quality_score'])
        print(f"质量最低的特性: {lowest_quality['feature_key']} (质量得分: {lowest_quality['quality_score']:.1f}, 等级: {lowest_quality['quality_grade']})")


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
    analyzer = FeatureQualityAnalyzer()
    return process_jira_data(jira_client, jql, analyzer, use_cache)


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
    analyzer = FeatureQualityAnalyzer()
    results = analyzer.analyze_features_from_files(
        features_file=features_file,
        bugs_file=bugs_file,
        bugs_relation_file=relation_file
    )

    return results