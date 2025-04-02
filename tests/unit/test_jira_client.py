#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from jirabug.core.jira_client import JiraClient, save_issues_to_json

class TestJiraClient(unittest.TestCase):
    def setUp(self):
        # 创建临时目录用于测试缓存
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = os.path.join(self.temp_dir.name, 'jira_cache')
        os.makedirs(self.cache_dir, exist_ok=True)

        # 模拟Jira客户端
        self.mock_jira = MagicMock()
        self.client = JiraClient(
            jira_url='https://test.atlassian.net',
            username='test@example.com',
            token='test_token',
            cache_dir=self.cache_dir
        )
        self.client.jira = self.mock_jira

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_issues(self):
        """测试获取Jira问题"""
        # 模拟Jira API响应
        mock_issues = [
            MagicMock(
                key='TEST-1',
                fields=MagicMock(
                    summary='Test Issue 1',
                    description='Test Description 1',
                    status=MagicMock(name='Open'),
                    created='2024-01-01T00:00:00.000+0000'
                )
            ),
            MagicMock(
                key='TEST-2',
                fields=MagicMock(
                    summary='Test Issue 2',
                    description='Test Description 2',
                    status=MagicMock(name='Closed'),
                    created='2024-01-02T00:00:00.000+0000'
                )
            )
        ]
        self.mock_jira.search_issues.return_value = mock_issues

        # 测试获取问题
        issues = self.client.get_issues('project = TEST')
        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0].key, 'TEST-1')
        self.assertEqual(issues[1].key, 'TEST-2')

    def test_get_issue_links(self):
        """测试获取问题链接"""
        # 模拟Jira API响应
        mock_links = [
            MagicMock(
                outwardIssue=MagicMock(key='TEST-2'),
                inwardIssue=None
            ),
            MagicMock(
                outwardIssue=None,
                inwardIssue=MagicMock(key='TEST-3')
            )
        ]
        mock_issue = MagicMock(fields=MagicMock(issuelinks=mock_links))
        self.mock_jira.issue.return_value = mock_issue

        # 测试获取链接
        links = self.client.get_issue_links('TEST-1')
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].outwardIssue.key, 'TEST-2')
        self.assertEqual(links[1].inwardIssue.key, 'TEST-3')

    def test_create_link(self):
        """测试创建问题链接"""
        # 模拟Jira API响应
        mock_link_types = [
            MagicMock(id='10000', name='Relates'),
            MagicMock(id='10001', name='Blocks')
        ]
        self.mock_jira.issue_link_types.return_value = mock_link_types

        # 测试创建链接
        result = self.client.create_link('TEST-1', 'TEST-2', 'Relates')
        self.assertTrue(result)
        self.mock_jira.create_issue_link.assert_called_once()

    def test_clear_cache(self):
        """测试清除缓存"""
        # 创建测试缓存文件
        cache_file = os.path.join(self.cache_dir, 'test_cache.pickle')
        with open(cache_file, 'w') as f:
            f.write('test data')

        # 测试清除缓存
        self.client.clear_cache()
        self.assertFalse(os.path.exists(cache_file))

    def test_save_issues_to_json(self):
        """测试保存问题到JSON文件"""
        # 创建测试问题
        mock_issues = [
            MagicMock(
                key='TEST-1',
                fields=MagicMock(
                    summary='Test Issue 1',
                    description='Test Description 1',
                    status=MagicMock(name='Open'),
                    created='2024-01-01T00:00:00.000+0000',
                    priority=MagicMock(name='High')
                )
            )
        ]

        # 创建临时文件
        temp_file = os.path.join(self.temp_dir.name, 'test_issues.json')

        # 测试保存到JSON
        result = save_issues_to_json(mock_issues, temp_file)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['key'], 'TEST-1')
        self.assertTrue(os.path.exists(temp_file))

if __name__ == '__main__':
    unittest.main()