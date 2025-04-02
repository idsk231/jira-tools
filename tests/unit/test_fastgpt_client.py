#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch, MagicMock
from jirabug.core.fastgpt_client import FastGPTClient

class TestFastGPTClient(unittest.TestCase):
    def setUp(self):
        # 创建FastGPT客户端实例
        self.client = FastGPTClient(
            api_key='test_api_key',
            api_base='https://api.test.com/v1',
            model_name='gpt-3.5-turbo'
        )

    @patch('openai.OpenAI')
    def test_analyze_bug(self, mock_openai):
        """测试分析Bug与特性的关联"""
        # 模拟OpenAI API响应
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(
                    content="""特性ID: TEST-1
相关度: 高
理由: 该bug与特性TEST-1的功能直接相关"""
                )
            )
        ]
        mock_openai.return_value.chat.completions.create.return_value = mock_completion

        # 测试数据
        bug_title = "测试Bug标题"
        bug_description = "测试Bug描述"
        feature_list = [
            {"key": "TEST-1", "summary": "测试特性1"},
            {"key": "TEST-2", "summary": "测试特性2"}
        ]

        # 执行测试
        feature_id, analysis_result = self.client.analyze_bug(
            bug_title,
            bug_description,
            feature_list
        )

        # 验证结果
        self.assertEqual(feature_id, "TEST-1")
        self.assertIn("相关度: 高", analysis_result)
        self.assertIn("理由:", analysis_result)

    @patch('openai.OpenAI')
    def test_analyze_bug_with_feedback(self, mock_openai):
        """测试带反馈的Bug分析"""
        # 模拟反馈管理器
        mock_feedback_manager = MagicMock()
        mock_feedback_manager.get_feedback_prompt.return_value = "历史反馈提示"

        # 创建带反馈管理器的客户端
        client = FastGPTClient(
            api_key='test_api_key',
            api_base='https://api.test.com/v1',
            feedback_manager=mock_feedback_manager
        )

        # 模拟OpenAI API响应
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(
                    content="""特性ID: TEST-1
相关度: 高
理由: 该bug与特性TEST-1的功能直接相关"""
                )
            )
        ]
        mock_openai.return_value.chat.completions.create.return_value = mock_completion

        # 测试数据
        bug_title = "测试Bug标题"
        bug_description = "测试Bug描述"
        feature_list = [
            {"key": "TEST-1", "summary": "测试特性1"},
            {"key": "TEST-2", "summary": "测试特性2"}
        ]

        # 执行测试
        feature_id, analysis_result = client.analyze_bug(
            bug_title,
            bug_description,
            feature_list
        )

        # 验证结果
        self.assertEqual(feature_id, "TEST-1")
        self.assertIn("相关度: 高", analysis_result)
        self.assertIn("理由:", analysis_result)
        mock_feedback_manager.get_feedback_prompt.assert_called_once()

    def test_parse_analysis_result(self):
        """测试解析分析结果"""
        # 测试数据
        analysis_result = """特性ID: TEST-1
相关度: 高
理由: 该bug与特性TEST-1的功能直接相关"""

        # 执行测试
        feature_id, confidence, reason = self.client.parse_analysis_result(analysis_result)

        # 验证结果
        self.assertEqual(feature_id, "TEST-1")
        self.assertEqual(confidence, "高")
        self.assertEqual(reason, "该bug与特性TEST-1的功能直接相关")

    def test_parse_analysis_result_invalid(self):
        """测试解析无效的分析结果"""
        # 测试数据
        analysis_result = "无效的分析结果"

        # 执行测试
        feature_id, confidence, reason = self.client.parse_analysis_result(analysis_result)

        # 验证结果
        self.assertEqual(feature_id, "未确定")
        self.assertEqual(confidence, "未知")
        self.assertEqual(reason, "")

if __name__ == '__main__':
    unittest.main()