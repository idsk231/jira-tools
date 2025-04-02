#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
特性质量分析工具命令行接口。
提供命令行界面来分析特性单下bug单的质量指标。
"""

import os
import sys
import argparse
import time
import json

from ..core.config import load_config
from ..core.jira_client import JiraClient
from ..analysis.feature_analyzer import FeatureQualityAnalyzer


def main():
    """命令行入口函数。"""
    parser = argparse.ArgumentParser(description='特性质量分析工具')
    parser.add_argument('--config', default='config.ini', help='配置文件路径')
    parser.add_argument('--output', help='输出报告文件路径，默认使用配置文件中的设置')
    parser.add_argument('--mode', choices=['jira', 'file'], default='file',
                       help='数据来源模式: jira=直接从Jira获取, file=从本地文件获取')
    parser.add_argument('--features-file', help='特性数据JSON文件路径 (file模式)')
    parser.add_argument('--bugs-file', help='Bug数据JSON文件路径 (file模式)')
    parser.add_argument('--relation-file', help='Bug-特性关系Excel文件路径 (file模式)')
    parser.add_argument('--jql', help='特性筛选JQL语句 (jira模式)')
    parser.add_argument('--use-cache', action='store_true', help='使用缓存 (jira模式)')
    parser.add_argument('--clear-cache', action='store_true', help='清除缓存 (jira模式)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    if not config:
        return 1

    try:
        # 确定输出文件路径
        output_file = args.output
        if not output_file and 'Output' in config:
            if 'quality_report_file' in config['Output']:
                output_file = config['Output']['quality_report_file']
            elif 'output_file' in config['Output']:
                # 使用默认输出文件名但修改为质量报告
                base_name = os.path.splitext(config['Output']['output_file'])[0]
                output_file = f"{base_name}_quality_report.xlsx"

        if not output_file:
            output_file = 'feature_quality_report.xlsx'
    except Exception as e:
        print(f"配置处理错误: {str(e)}")
        return 1

    # 初始化质量分析器
    analyzer = FeatureQualityAnalyzer()

    # 根据模式处理
    results = None

    try:
        if args.mode == 'jira':
            # 从Jira获取数据
            print("从Jira服务器获取数据...")

            try:
                # 从配置文件获取Jira设置
                jira_url = config['Jira']['url']
                jira_username = config['Jira']['username']
                jira_token = config['Jira']['token']

                # 初始化Jira客户端
                jira_client = JiraClient(jira_url, jira_username, jira_token)
                print("已连接到Jira服务器")

                # 如果需要，清除缓存
                if args.clear_cache:
                    jira_client.clear_cache()

                # 获取JQL
                jql = args.jql
                if not jql and 'Filters' in config and 'feature_filter' in config['Filters']:
                    jql = config['Filters']['feature_filter']

                if not jql:
                    print("错误: 未提供特性筛选JQL。请在配置文件或命令行参数中指定")
                    return 1

                # 从Jira获取数据并分析
                results = process_jira_data(jira_client, jql, analyzer, args.use_cache, args.debug)

            except KeyError as e:
                print(f"配置错误: 缺少必要的配置项 {e}")
                return 1
            except Exception as e:
                print(f"从Jira获取数据失败: {str(e)}")
                if args.debug:
                    import traceback
                    traceback.print_exc()
                return 1

        elif args.mode == 'file':
            # 从文件加载数据
            print("从本地文件获取数据...")

            # 确定特性文件路径
            features_file = args.features_file
            if not features_file and 'Output' in config and 'features_file' in config['Output']:
                features_file = config['Output']['features_file']

            if not features_file or not os.path.exists(features_file):
                print("错误: 未找到特性文件。请在配置文件或命令行参数中指定")
                return 1

            # 确定Bug文件路径
            bugs_file = args.bugs_file
            if not bugs_file and 'Output' in config and 'bugs_file' in config['Output']:
                bugs_file = config['Output']['bugs_file']

            # 确保Bug文件存在
            if bugs_file and not os.path.exists(bugs_file):
                print(f"警告: Bug文件 {bugs_file} 不存在，将只分析特性数据")
                bugs_file = None

            # 确定关系文件路径
            relation_file = args.relation_file
            if not relation_file and 'Output' in config and 'output_file' in config['Output']:
                relation_file = config['Output']['output_file']

            # 确保关系文件存在
            if relation_file and not os.path.exists(relation_file):
                print(f"警告: 关系文件 {relation_file} 不存在，将尝试从Bug数据中获取关联关系")
                relation_file = None

            # 从文件分析特性质量
            try:
                results = analyzer.analyze_features_from_files(
                    features_file=features_file,
                    bugs_file=bugs_file if bugs_file and os.path.exists(bugs_file) else None,
                    bugs_relation_file=relation_file if relation_file and os.path.exists(relation_file) else None
                )
            except Exception as e:
                print(f"分析文件失败: {str(e)}")
                if args.debug:
                    import traceback
                    traceback.print_exc()
                return 1

        # 生成报告
        if results:
            # 生成质量报告
            analyzer.generate_quality_report(results, output_file)
            print(f"质量分析完成，报告已保存到 {output_file}")

            # 显示摘要统计
            print_summary_statistics(results)

            return 0
        else:
            print("没有分析结果生成")
            return 1
    except Exception as e:
        print(f"处理过程出错: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def process_jira_data(jira_client, jql, analyzer, use_cache=False, debug=False):
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
    from tqdm import tqdm
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


def print_summary_statistics(results):
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


if __name__ == "__main__":
    sys.exit(main())