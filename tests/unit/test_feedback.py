#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from jirabug.analysis.feedback import FeedbackManager

class TestFeedbackManager(unittest.TestCase):
    def setUp(self):
        # 创建临时目录和文件
        self.temp_dir = tempfile.TemporaryDirectory()
        self.feedback_file = os.path.join(self.temp_dir.name, 'test_feedback.csv')
        self.manager = FeedbackManager(self.feedback_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_feedback(self):
        """测试保存反馈"""
        # 测试数据
        bug_id = "TEST-1"
        bug_title = "测试Bug标题"
        predicted_feature = "TEST-2"
        correct_feature = "TEST-3"
        reason = "测试原因"

        # 执行测试
        result = self.manager.save_feedback(
            bug_id=bug_id,
            bug_title=bug_title,
            predicted_feature=predicted_feature,
            correct_feature=correct_feature,
            reason=reason
        )

        # 验证结果
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.feedback_file))

        # 验证文件内容
        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(bug_id, content)
            self.assertIn(bug_title, content)
            self.assertIn(predicted_feature, content)
            self.assertIn(correct_feature, content)
            self.assertIn(reason, content)

    def test_get_relevant_feedback(self):
        """测试获取相关反馈"""
        # 添加测试反馈
        self.manager.save_feedback(
            bug_id="TEST-1",
            bug_title="测试Bug标题1",
            predicted_feature="TEST-2",
            correct_feature="TEST-3",
            reason="测试原因1"
        )
        self.manager.save_feedback(
            bug_id="TEST-4",
            bug_title="测试Bug标题2",
            predicted_feature="TEST-5",
            correct_feature="TEST-6",
            reason="测试原因2"
        )

        # 测试获取相关反馈
        relevant_feedback = self.manager.get_relevant_feedback(
            bug_title="测试Bug标题1",
            bug_description="测试Bug描述"
        )

        # 验证结果
        self.assertEqual(len(relevant_feedback), 1)
        self.assertEqual(relevant_feedback[0]['bug_id'], "TEST-1")
        self.assertEqual(relevant_feedback[0]['bug_title'], "测试Bug标题1")

    def test_calculate_similarity(self):
        """测试计算相似度"""
        # 测试数据
        text1 = "测试Bug标题 描述"
        text2 = "测试Bug标题 详细描述"

        # 执行测试
        similarity = self.manager._calculate_similarity(text1, text2)

        # 验证结果
        self.assertGreater(similarity, 0)
        self.assertLessEqual(similarity, 1)

    def test_get_feedback_prompt(self):
        """测试获取反馈提示"""
        # 添加测试反馈
        self.manager.save_feedback(
            bug_id="TEST-1",
            bug_title="测试Bug标题1",
            predicted_feature="TEST-2",
            correct_feature="TEST-3",
            reason="测试原因1"
        )

        # 测试获取反馈提示
        prompt = self.manager.get_feedback_prompt(
            bug_title="测试Bug标题1",
            bug_description="测试Bug描述"
        )

        # 验证结果
        self.assertIn("历史反馈案例", prompt)
        self.assertIn("TEST-1", prompt)
        self.assertIn("测试Bug标题1", prompt)

    def test_load_feedback(self):
        """测试加载反馈"""
        # 创建测试反馈文件
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            f.write("""bug_id,bug_title,predicted_feature,correct_feature,reason,timestamp
TEST-1,测试Bug标题1,TEST-2,TEST-3,测试原因1,2024-01-01 00:00:00
TEST-4,测试Bug标题2,TEST-5,TEST-6,测试原因2,2024-01-02 00:00:00
""")

        # 创建新的反馈管理器实例
        new_manager = FeedbackManager(self.feedback_file)

        # 验证结果
        self.assertEqual(len(new_manager.feedback_data), 2)
        self.assertEqual(new_manager.feedback_data[0]['bug_id'], "TEST-1")
        self.assertEqual(new_manager.feedback_data[1]['bug_id'], "TEST-4")

if __name__ == '__main__':
    unittest.main()