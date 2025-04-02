#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from unittest.mock import patch
from jirabug.core.config import load_config, create_sample_config

class TestConfig(unittest.TestCase):
    def setUp(self):
        # 创建临时配置文件
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = os.path.join(self.temp_dir.name, 'test_config.ini')

    def tearDown(self):
        # 清理临时文件
        self.temp_dir.cleanup()

    def test_create_sample_config(self):
        """测试创建示例配置文件"""
        create_sample_config(self.config_file)

        # 验证文件是否存在
        self.assertTrue(os.path.exists(self.config_file))

        # 验证文件内容
        with open(self.config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('[Jira]', content)
            self.assertIn('[FastGPT]', content)
            self.assertIn('[Filters]', content)

    def test_load_config_valid(self):
        """测试加载有效的配置文件"""
        # 创建有效的配置文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write("""
[Jira]
url = https://test.atlassian.net
username = test@example.com
token = test_token

[FastGPT]
api_key = test_api_key
api_base = https://api.test.com/v1

[Filters]
bug_filter = project = TEST AND issuetype = Bug
feature_filter = project = TEST AND issuetype = Feature
""")

        config = load_config(self.config_file)
        self.assertIsNotNone(config)
        self.assertEqual(config['Jira']['url'], 'https://test.atlassian.net')
        self.assertEqual(config['FastGPT']['api_key'], 'test_api_key')

    def test_load_config_missing_section(self):
        """测试加载缺少必要部分的配置文件"""
        # 创建缺少必要部分的配置文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write("""
[Jira]
url = https://test.atlassian.net
username = test@example.com
token = test_token
""")

        config = load_config(self.config_file)
        self.assertIsNone(config)

    def test_load_config_missing_option(self):
        """测试加载缺少必要选项的配置文件"""
        # 创建缺少必要选项的配置文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write("""
[Jira]
url = https://test.atlassian.net
username = test@example.com

[FastGPT]
api_key = test_api_key
api_base = https://api.test.com/v1

[Filters]
bug_filter = project = TEST AND issuetype = Bug
feature_filter = project = TEST AND issuetype = Feature
""")

        config = load_config(self.config_file)
        self.assertIsNone(config)

    def test_load_config_nonexistent(self):
        """测试加载不存在的配置文件"""
        config = load_config('nonexistent.ini')
        self.assertIsNone(config)

if __name__ == '__main__':
    unittest.main()