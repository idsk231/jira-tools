#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
链接创建工具命令行接口。
提供命令行界面来创建Jira issues之间的链接关系。
"""

import os
import sys
import argparse
import pandas as pd
from tqdm import tqdm
import time

from ..core.config import load_config
from ..core.jira_client import JiraClient


def main():
    """命令行入口函数。"""
    parser = argparse.ArgumentParser(description='根据关联关系表创建Jira issues之间的链接')
    parser.add_argument('--config', default='config.ini', help='配置文件路径')
    parser.add_argument('--input', help='关联关系输入文件(Excel)，默认使用配置文件中的output_file')
    parser.add_argument('--bug-col', default='Bug ID', help='Bug ID列名')
    parser.add_argument('--feature-col', default='相关特性', help='特性ID列名')
    parser.add_argument('--link-type', default='Relates', help='链接类型')
    parser.add_argument('--dry-run', action='store_true', help='干运行模式，不实际创建链接')
    parser.add_argument('--skip-existing', action='store_true', help='跳过已存在的链接')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    if not config:
        return 1

    try:
        # 从配置文件获取Jira设置
        jira_url = config['Jira']['url']
        jira_username = config['Jira']['username']
        jira_token = config['Jira']['token']

        # 处理输入文件参数
        input_file = args.input
        if not input_file and 'Output' in config and 'output_file' in config['Output']:
            input_file = config['Output']['output_file']

        if not input_file:
            print("错误: 未指定输入文件，请使用--input参数或在配置文件中设置output_file")
            return 1

        if not os.path.exists(input_file):
            print(f"错误: 输入文件 {input_file} 不存在")
            return 1
    except KeyError as e:
        print(f"配置错误: 缺少必要的配置项 {e}")
        return 1

    # 初始化客户端
    try:
        jira_client = JiraClient(jira_url, jira_username, jira_token)
        print("已连接到Jira服务器")
    except Exception as e:
        print(f"连接Jira服务器失败: {str(e)}")
        return 1

    # 加载关联关系表
    try:
        df = pd.read_excel(input_file)
        print(f"已加载 {len(df)} 条关联关系记录")

        # 检查必要的列是否存在
        if args.bug_col not in df.columns or args.feature_col not in df.columns:
            print(f"输入文件缺少必要的列: {args.bug_col} 或 {args.feature_col}")
            return 1
    except Exception as e:
        print(f"加载关联关系表失败: {str(e)}")
        return 1

    # 创建链接
    success_count = 0
    skip_count = 0
    error_count = 0

    print(f"开始创建链接, 链接类型: {args.link_type}")

    try:
        for _, row in tqdm(df.iterrows(), total=len(df)):
            bug_id = row[args.bug_col]
            feature_id = row[args.feature_col]

            # 跳过空值或"未确定"
            if pd.isna(bug_id) or pd.isna(feature_id) or feature_id == "未确定":
                skip_count += 1
                continue

            # 检查是否已存在链接
            link_exists = False
            if args.skip_existing:
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
                    if args.debug:
                        print(f"检查链接时发生错误: {str(e)}")

            if link_exists:
                if args.debug:
                    print(f"跳过已存在的链接: {bug_id} -> {feature_id}")
                skip_count += 1
                continue

            # 干运行模式
            if args.dry_run:
                print(f"将创建链接: {bug_id} -> {feature_id}")
                success_count += 1
                continue

            # 创建链接
            if jira_client.create_link(bug_id, feature_id, args.link_type):
                success_count += 1
            else:
                error_count += 1
                if args.debug:
                    print(f"创建链接失败: {bug_id} -> {feature_id}")

            # 添加短暂延迟，避免API限制
            time.sleep(0.5)
    except Exception as e:
        print(f"处理过程出错: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

    # 输出结果
    print(f"\n链接创建完成:")
    print(f"  成功: {success_count}")
    print(f"  跳过: {skip_count}")
    print(f"  错误: {error_count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())