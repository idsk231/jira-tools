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
from ..service.quality_service import analyze_quality_from_jira, analyze_quality_from_files, print_summary_statistics


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
                results = analyze_quality_from_jira(jira_client, jql, args.use_cache)

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
                results = analyze_quality_from_files(
                    features_file=features_file,
                    bugs_file=bugs_file if bugs_file and os.path.exists(bugs_file) else None,
                    relation_file=relation_file if relation_file and os.path.exists(relation_file) else None
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


if __name__ == "__main__":
    sys.exit(main())