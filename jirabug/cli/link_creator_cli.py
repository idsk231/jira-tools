#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
链接创建工具命令行接口。
提供命令行界面来创建Jira issues之间的链接关系。
"""

import os
import sys
import argparse

from ..core.config import load_config
from ..core.jira_client import JiraClient
from ..service.link_service import create_links_from_analysis


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

    try:
        # 调用服务层创建链接
        success_count, skip_count, error_count = create_links_from_analysis(
            jira_client=jira_client,
            analysis_file=input_file,
            bug_col=args.bug_col,
            feature_col=args.feature_col,
            link_type=args.link_type,
            dry_run=args.dry_run,
            skip_existing=args.skip_existing,
            debug=args.debug
        )

        # 输出结果
        print(f"\n链接创建完成:")
        print(f"  成功: {success_count}")
        print(f"  跳过: {skip_count}")
        print(f"  错误: {error_count}")

        return 0
    except Exception as e:
        print(f"处理过程出错: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())