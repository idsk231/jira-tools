#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bug分析工具命令行接口。
提供命令行界面来分析Jira bug单与特性需求的关联。
"""

import os
import sys
import argparse
import pandas as pd

from ..core.config import load_config
from ..core.jira_client import JiraClient, save_issues_to_json
from ..core.fastgpt_client import FastGPTClient
from ..analysis.bug_analyzer import analyze_bugs, filter_bugs
from ..analysis.feedback import FeedbackManager, interactive_feedback_mode


def main():
    """命令行入口函数。"""
    parser = argparse.ArgumentParser(description='Jira Bug-Feature Analyzer')
    parser.add_argument('--config', default='config.ini', help='配置文件路径')
    parser.add_argument('--debug', action='store_true', help='启用调试模式，输出更详细的分析信息')
    parser.add_argument('--feedback', action='store_true', help='启用交互式反馈模式（覆盖配置文件设置）')
    parser.add_argument('--no-feedback', action='store_true', help='禁用反馈模式（覆盖配置文件设置）')
    parser.add_argument('--clear-cache', action='store_true', help='清除本地缓存数据')
    parser.add_argument('--no-cache', action='store_true', help='不使用缓存数据')
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    if not config:
        return 1

    # 从配置文件获取设置
    try:
        # Jira设置
        jira_url = config['Jira']['url']
        jira_username = config['Jira']['username']
        jira_token = config['Jira']['token']

        # FastGPT设置
        fastgpt_key = config['FastGPT']['api_key']
        fastgpt_base = config['FastGPT'].get('api_base', 'https://api.fastgpt.io/v1')

        # 过滤器设置
        bug_filter = config['Filters']['bug_filter']
        feature_filter = config['Filters']['feature_filter']

        # 输出设置
        output_file = config['Output'].get('output_file', 'bug_analysis_results.xlsx')
        features_file = config['Output'].get('features_file', 'jira_features.json')
        bugs_file = config['Output'].get('bugs_file', 'jira_bugs.json')

        # 高级选项
        if 'Advanced' not in config:
            config['Advanced'] = {}

        model_name = config['Advanced'].get('model_name', 'gpt-3.5-turbo')
        max_bugs = int(config['Advanced'].get('max_bugs', '0'))  # 0表示不限制
        use_cache = config['Advanced'].getboolean('use_cache', True)
        clear_cache = config['Advanced'].getboolean('clear_cache', False) or args.clear_cache

        # 反馈配置
        enable_feedback = False
        feedback_file = 'feedback_history.csv'
        similarity_threshold = 0.7
        max_feedback_examples = 5

        if 'Feedback' in config:
            enable_feedback = config['Feedback'].getboolean('enable', fallback=False)
            feedback_file = config['Feedback'].get('feedback_file', 'feedback_history.csv')
            similarity_threshold = float(config['Feedback'].get('similarity_threshold', '0.7'))
            max_feedback_examples = int(config['Feedback'].get('max_feedback_examples', '5'))

        # 命令行参数覆盖配置文件
        if args.feedback:
            enable_feedback = True
        if args.no_feedback:
            enable_feedback = False
        if args.no_cache:
            use_cache = False
    except KeyError as e:
        print(f"配置错误: 缺少必要的配置项 {e}")
        return 1

    # 初始化反馈管理器
    feedback_manager = None
    if enable_feedback:
        feedback_manager = FeedbackManager(feedback_file)
        feedback_manager.similarity_threshold = similarity_threshold
        feedback_manager.max_feedback_examples = max_feedback_examples

    try:
        # 初始化Jira客户端
        jira_client = JiraClient(jira_url, jira_username, jira_token)
        print("已连接到Jira服务器")

        # 如果需要，清除缓存
        if clear_cache:
            jira_client.clear_cache()

        # 初始化FastGPT客户端
        fastgpt_client = FastGPTClient(
            api_key=fastgpt_key,
            api_base=fastgpt_base,
            feedback_manager=feedback_manager,
            model_name=model_name
        )

        # 调试模式
        debug_mode = args.debug
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        return 1

    try:
        # 获取数据
        print("正在获取特性需求列表...")
        features = jira_client.get_all_issues(
            feature_filter,
            fields=["key", "summary", "description", "status"],
            cache_key="features" if use_cache else None
        )
        print(f"获取到 {len(features)} 个特性需求")

        # 保存特性到JSON文件
        feature_data = save_issues_to_json(features, features_file)

        print("正在获取Bug单列表...")
        bugs = jira_client.get_all_issues(
            bug_filter,
            fields=["key", "summary", "description", "status", "created", "priority"],
            cache_key="bugs" if use_cache else None
        )
        print(f"获取到 {len(bugs)} 个Bug单")

        # 保存bug到JSON文件
        save_issues_to_json(bugs, bugs_file)

        # 过滤Bug
        filtered_bugs = filter_bugs(bugs, max_bugs)

        # 分析Bug与特性的关联
        results = analyze_bugs(
            bugs=filtered_bugs,
            features=features,
            fastgpt_client=fastgpt_client,
            debug_mode=debug_mode
        )

        # 交互式反馈
        if enable_feedback:
            print("\n分析完成，进入反馈模式...")
            results = interactive_feedback_mode(results, features, feedback_manager)

        # 保存结果到Excel
        df = pd.DataFrame(results)
        df.to_excel(output_file, index=False)
        print(f"分析完成，结果已保存到 {output_file}")

        return 0
    except Exception as e:
        print(f"处理过程出错: {str(e)}")
        if debug_mode:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())