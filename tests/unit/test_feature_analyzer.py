#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from datetime import datetime, timedelta
from jirabug.analysis.feature_analyzer import FeatureQualityAnalyzer

class TestFeatureQualityAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = FeatureQualityAnalyzer()

    def test_analyze_feature_quality(self):
        """测试分析特性质量"""
        # 测试数据
        feature = {
            "key": "TEST-1",
            "summary": "测试特性"
        }

        linked_bugs = [
            {
                "key": "BUG-1",
                "status": "Open",
                "severity": "Major",
                "priority": "High",
                "created": "2024-01-01T00:00:00.000+0000",
                "resolutiondate": None
            },
            {
                "key": "BUG-2",
                "status": "Resolved",
                "severity": "Minor",
                "priority": "Low",
                "created": "2024-01-02T00:00:00.000+0000",
                "resolutiondate": "2024-01-03T00:00:00.000+0000"
            }
        ]

        # 执行测试
        result = self.analyzer.analyze_feature_quality(feature, linked_bugs)

        # 验证结果
        self.assertEqual(result["feature_key"], "TEST-1")
        self.assertEqual(result["total_bugs"], 2)
        self.assertEqual(result["open_bugs"], 1)
        self.assertEqual(result["resolved_bugs"], 1)
        self.assertEqual(result["resolution_rate"], 50.0)
        self.assertIn("Major", result["severity_distribution"])
        self.assertIn("High", result["priority_distribution"])
        self.assertGreater(result["quality_score"], 0)
        self.assertLessEqual(result["quality_score"], 100)

    def test_parse_datetime(self):
        """测试解析日期时间"""
        # 测试ISO格式
        iso_date = "2024-01-01T00:00:00.000+0000"
        result = self.analyzer._parse_datetime(iso_date)
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)

        # 测试其他格式
        other_date = "2024-01-01 00:00:00"
        result = self.analyzer._parse_datetime(other_date)
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)

        # 测试无效格式
        invalid_date = "invalid date"
        result = self.analyzer._parse_datetime(invalid_date)
        self.assertIsNone(result)

    def test_calculate_quality_score(self):
        """测试计算质量分数"""
        # 测试数据
        bugs = [
            {
                "status": "Open",
                "severity": "Major"
            },
            {
                "status": "Resolved",
                "severity": "Minor"
            }
        ]

        # 执行测试
        score = self.analyzer._calculate_quality_score(bugs, 50.0)

        # 验证结果
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)

    def test_determine_quality_grade(self):
        """测试确定质量等级"""
        # 测试不同分数对应的等级
        test_cases = [
            (95, "A+"),
            (90, "A"),
            (85, "A-"),
            (80, "B+"),
            (75, "B"),
            (70, "B-"),
            (65, "C+"),
            (60, "C"),
            (55, "C-"),
            (50, "D"),
            (45, "F")
        ]

        for score, expected_grade in test_cases:
            grade = self.analyzer._determine_quality_grade(score)
            self.assertEqual(grade, expected_grade)

    def test_analyze_features_from_files(self):
        """测试从文件分析特性质量"""
        # 创建测试数据
        feature_data = {
            "key": "TEST-1",
            "summary": "测试特性",
            "status": "Open"
        }

        bug_data = {
            "key": "BUG-1",
            "summary": "测试Bug",
            "status": "Open",
            "severity": "Major",
            "priority": "High",
            "created": "2024-01-01T00:00:00.000+0000"
        }

        # 执行测试
        result = self.analyzer.analyze_features_from_files(
            features_file=None,
            bugs_file=None,
            bugs_relation_file=None,
            feature_data=[feature_data],
            bug_data=[bug_data]
        )

        # 验证结果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["feature_key"], "TEST-1")
        self.assertEqual(result[0]["total_bugs"], 1)
        self.assertEqual(result[0]["open_bugs"], 1)

if __name__ == '__main__':
    unittest.main()