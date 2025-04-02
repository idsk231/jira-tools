#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Jira客户端模块 - 负责与Jira API交互，获取和缓存数据
"""

import os
import json
import time
import pickle
from typing import Optional, List, Dict, Any


class JiraClient:
    def __init__(self, jira_url: str, username: str, token: str,
                 cache_dir: str = "jira_cache"):
        """
        初始化Jira客户端

        参数:
            jira_url (str): Jira服务器URL
            username (str): Jira用户名
            token (str): Jira API令牌
        """
        self.jira = JIRA(server=jira_url, basic_auth=(username, token))
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jira_cache')

        # 确保缓存目录存在
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # 缓存字段名称
        self._cache_field_names()

    def _cache_field_names(self):
        """缓存Jira自定义字段的ID"""
        self.severity_field = None

        try:
            # 获取所有字段
            fields = self.jira.fields()

            # 查找严重程度字段 - 有些Jira实例用"Severity"，有些用"严重程度"等
            for field in fields:
                if field['name'].lower() in ['severity', '严重程度', 'severity level']:
                    self.severity_field = field['id']
                    break
        except Exception as e:
            print(f"获取Jira字段失败: {str(e)}")

    def get_issues(self, jql_query, start_at=0, max_results=100, fields=None):
        """
        使用JQL查询拉取Jira问题

        参数:
            jql_query (str): JQL查询条件
            start_at (int): 起始位置
            max_results (int): 最大结果数
            fields (list): 要获取的字段列表

        返回:
            list: 问题列表
        """
        if fields is None:
            fields = ["key", "summary", "description", "issuetype", "created", "status"]

        try:
            issues = self.jira.search_issues(
                jql_query,
                startAt=start_at,
                maxResults=max_results,
                fields=",".join(fields)
            )
            return issues
        except Exception as e:
            print(f"获取Jira问题失败: {str(e)}")
            return None

    def get_all_issues(self, jql_query, fields=None, cache_key=None):
        """
        获取JQL查询的所有结果（处理分页），支持缓存

        参数:
            jql_query (str): JQL查询条件
            fields (list): 要获取的字段列表
            cache_key (str): 缓存键名，如果为None则不使用缓存

        返回:
            list: 问题列表
        """
        # 如果提供了缓存键，检查缓存文件是否存在
        cache_file = None
        if cache_key:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pickle")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'rb') as f:
                        cached_data = pickle.load(f)
                        print(f"从缓存加载到 {len(cached_data)} 个Issues ({cache_key})")
                        return cached_data
                except Exception as e:
                    print(f"读取缓存文件失败: {str(e)}")

        all_issues = []
        start_at = 0
        max_results = 100

        while True:
            issues = self.get_issues(jql_query, start_at, max_results, fields)

            if not issues:
                break

            all_issues.extend(issues)

            if len(issues) < max_results:
                break

            start_at += max_results
            time.sleep(1)  # 避免API请求过快

        # 保存到缓存文件
        if cache_key and all_issues:
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(all_issues, f)
                print(f"已将 {len(all_issues)} 个Issues保存到缓存 ({cache_key})")
            except Exception as e:
                print(f"保存缓存文件失败: {str(e)}")

        return all_issues

    def get_issue_links(self, issue_key):
        """
        获取指定问题的所有链接

        参数:
            issue_key (str): 问题ID

        返回:
            list: 链接列表
        """
        try:
            issue = self.jira.issue(issue_key, fields="issuelinks")
            return issue.fields.issuelinks
        except Exception as e:
            print(f"获取问题链接失败: {str(e)}")
            return []

    def create_link(self, from_issue, to_issue, link_type="Relates"):
        """
        在两个问题之间创建链接

        参数:
            from_issue (str): 源问题ID
            to_issue (str): 目标问题ID
            link_type (str): 链接类型

        返回:
            bool: 成功返回True，失败返回False
        """
        try:
            # 获取链接类型ID
            link_types = self.jira.issue_link_types()
            link_type_id = None

            for lt in link_types:
                if lt.name == link_type:
                    link_type_id = lt.id
                    break

            if not link_type_id:
                print(f"找不到链接类型: {link_type}")
                print(f"可用的链接类型: {[lt.name for lt in link_types]}")
                return False

            # 创建链接
            self.jira.create_issue_link(
                type=link_type_id,
                inwardIssue=to_issue,
                outwardIssue=from_issue
            )
            return True
        except Exception as e:
            print(f"创建链接异常: {str(e)}")
            return False

    def clear_cache(self, cache_key=None):
        """
        清除缓存文件

        参数:
            cache_key (str): 特定缓存键，None表示清除所有缓存
        """
        if cache_key:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pickle")
            if os.path.exists(cache_file):
                os.remove(cache_file)
                print(f"已清除缓存: {cache_key}")
        else:
            # 清除所有缓存文件
            for file in os.listdir(self.cache_dir):
                if file.endswith('.pickle'):
                    os.remove(os.path.join(self.cache_dir, file))
            print("已清除所有缓存")

def save_issues_to_json(issues: List[Any], output_file: str) -> List[Dict[str, Any]]:
    """
    将jira-python库返回的Issue对象保存为JSON文件

    参数:
        issues (list): Jira问题列表
        output_file (str): 输出文件路径

    返回:
        list: 序列化后的问题列表
    """
    # 将Issue对象转换为可序列化的字典
    serializable_issues = []
    for issue in issues:
        issue_dict = {
            'key': issue.key,
            'summary': issue.fields.summary,
            'status': issue.fields.status.name if hasattr(issue.fields, 'status') else None,
            'created': str(issue.fields.created) if hasattr(issue.fields, 'created') else None,
        }

        # 保存描述，如果有的话
        if hasattr(issue.fields, 'description') and issue.fields.description:
            # Jira API可能返回复杂的富文本描述对象
            # 这里简化处理，仅提取纯文本
            if isinstance(issue.fields.description, str):
                issue_dict['description'] = issue.fields.description
            else:
                # 尝试处理富文本
                issue_dict['description'] = "复杂描述，请在Jira中查看"
        else:
            issue_dict['description'] = ""

        # 添加用于分析的其他字段
        if hasattr(issue.fields, 'priority') and issue.fields.priority:
            issue_dict['priority'] = issue.fields.priority.name

        # 保存类型
        issue_dict['issuetype'] = issue.fields.issuetype.name if hasattr(issue.fields, 'issuetype') else None

        serializable_issues.append(issue_dict)

    # 保存为JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_issues, f, ensure_ascii=False, indent=2)

    print(f"已保存 {len(serializable_issues)} 个issues到文件 {output_file}")

    return serializable_issues

if __name__ == "__main__":
    # 测试代码
    print("这是Jira客户端模块，请勿直接运行")
