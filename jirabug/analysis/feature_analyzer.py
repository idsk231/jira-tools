#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
特性质量分析模块，负责分析特性单下bug单数量、状态、严重程度、优先级等信息，
评估特性质量并生成质量报告。
"""

import os
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional, Union

import pandas as pd
import numpy as np


class FeatureQualityAnalyzer:
    """特性质量分析器，负责评估特性质量。"""

    def __init__(self):
        """初始化分析器，设置评估权重和状态分类。"""
        # 定义严重程度权重
        self.severity_weights = {
            "Blocker": 5,
            "Critical": 4,
            "Major": 3,
            "Normal": 2,
            "Minor": 1,
            "Trivial": 0.5
        }

        # 定义优先级权重
        self.priority_weights = {
            "Highest": 5,
            "High": 4,
            "Medium": 3,
            "Low": 2,
            "Lowest": 1
        }

        # 定义状态分类
        self.status_categories = {
            # 未解决
            "Open": "Open",
            "In Progress": "Open",
            "Reopened": "Open",
            "To Do": "Open",
            # 已解决
            "Resolved": "Resolved",
            "Closed": "Resolved",
            "Done": "Resolved",
            # 其他
            "Backlog": "Other"
        }

    def analyze_feature_quality(self, feature: Dict[str, Any], linked_bugs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析特性质量，基于关联的bug情况评估特性质量。

        Args:
            feature: 特性信息字典，包含key和summary等字段
            linked_bugs: 关联的bug列表，每个bug为一个字典

        Returns:
            质量分析结果字典，包含质量评分和各种统计指标
        """
        feature_key = feature["key"]
        feature_summary = feature["summary"]

        # 基本统计信息
        total_bugs = len(linked_bugs)

        # 按状态分类统计
        status_counts = defaultdict(int)
        for bug in linked_bugs:
            status = bug.get("status", "Unknown")
            category = self.status_categories.get(status, "Other")
            status_counts[category] += 1

        open_bugs = status_counts.get("Open", 0)
        resolved_bugs = status_counts.get("Resolved", 0)

        # 按严重程度分类统计
        severity_counts = defaultdict(int)
        for bug in linked_bugs:
            # 获取严重程度
            severity = bug.get("severity", "Unknown")
            severity_counts[severity] += 1

        # 按优先级分类统计
        priority_counts = defaultdict(int)
        for bug in linked_bugs:
            priority = bug.get("priority", "Unknown")
            priority_counts[priority] += 1

        # 计算严重性得分
        severity_score = 0
        total_weight = 0
        for severity, count in severity_counts.items():
            weight = self.severity_weights.get(severity, 1)  # 默认权重为1
            severity_score += weight * count
            total_weight += count

        avg_severity = severity_score / total_weight if total_weight > 0 else 0

        # 计算解决率
        resolution_rate = (resolved_bugs / total_bugs * 100) if total_bugs > 0 else 100

        # 计算最近1个月的bug数量
        month_ago = (datetime.now() - timedelta(days=30)).isoformat()
        recent_bugs = sum(1 for bug in linked_bugs if bug.get("created", "") > month_ago)

        # 计算平均解决时间（仅考虑已解决的bug）
        resolution_times = []
        for bug in linked_bugs:
            if bug.get("resolutiondate"):
                try:
                    # 处理不同格式的日期字符串
                    created = self._parse_datetime(bug["created"])
                    resolved = self._parse_datetime(bug["resolutiondate"])
                    if created and resolved:
                        resolution_times.append((resolved - created).days)
                except Exception as e:
                    pass  # 忽略日期解析错误

        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

        # 计算质量分数 (0-100)
        quality_score = self._calculate_quality_score(linked_bugs, resolution_rate)

        # 计算质量等级
        quality_grade = self._determine_quality_grade(quality_score)

        # 生成分析结果
        result = {
            "feature_key": feature_key,
            "feature_summary": feature_summary,
            "total_bugs": total_bugs,
            "open_bugs": open_bugs,
            "resolved_bugs": resolved_bugs,
            "resolution_rate": resolution_rate,
            "avg_resolution_time": avg_resolution_time,
            "recent_bugs": recent_bugs,
            "severity_distribution": dict(severity_counts),
            "priority_distribution": dict(priority_counts),
            "avg_severity": avg_severity,
            "quality_score": quality_score,
            "quality_grade": quality_grade
        }

        return result

    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """
        解析不同格式的日期时间字符串

        Args:
            datetime_str: 日期时间字符串

        Returns:
            解析后的datetime对象，失败返回None
        """
        try:
            # 处理ISO格式日期
            if 'Z' in datetime_str:
                return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            elif 'T' in datetime_str:
                return datetime.fromisoformat(datetime_str)
            else:
                # 尝试其他常见格式
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y/%m/%d %H:%M:%S",
                    "%d-%m-%Y %H:%M:%S",
                    "%Y-%m-%d"
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(datetime_str, fmt)
                    except ValueError:
                        continue
            return None
        except Exception:
            return None

    def _calculate_quality_score(self, bugs: List[Dict[str, Any]], resolution_rate: float) -> float:
        """
        计算质量分数，基于bug严重程度和解决率

        Args:
            bugs: bug列表
            resolution_rate: 解决率百分比

        Returns:
            质量分数 (0-100)
        """
        quality_score = 100

        # 根据open bug扣分
        for bug in bugs:
            status = bug.get("status", "")
            category = self.status_categories.get(status, "Other")

            if category == "Open":
                severity = bug.get("severity", "Normal")  # 默认严重程度

                # 基于严重程度扣分
                deduction = self.severity_weights.get(severity, 1) * 2
                quality_score -= deduction

        # 应用解决率影响，解决率低于80%时开始显著影响得分
        if resolution_rate < 80:
            quality_score *= (0.5 + resolution_rate / 160)  # 线性调整

        # 确保分数在0-100之间
        quality_score = max(0, min(100, quality_score))

        return quality_score

    def _determine_quality_grade(self, quality_score: float) -> str:
        """
        根据质量分数确定质量等级

        Args:
            quality_score: 质量分数 (0-100)

        Returns:
            质量等级字母等级 (A+到F)
        """
        if quality_score >= 95:
            return "A+"
        elif quality_score >= 90:
            return "A"
        elif quality_score >= 85:
            return "A-"
        elif quality_score >= 80:
            return "B+"
        elif quality_score >= 75:
            return "B"
        elif quality_score >= 70:
            return "B-"
        elif quality_score >= 65:
            return "C+"
        elif quality_score >= 60:
            return "C"
        elif quality_score >= 55:
            return "C-"
        elif quality_score >= 50:
            return "D+"
        elif quality_score >= 45:
            return "D"
        else:
            return "F"

    def analyze_features_from_files(
        self,
        features_file: str,
        bugs_file: Optional[str] = None,
        bugs_relation_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        从文件分析特性质量

        Args:
            features_file: 特性数据JSON文件路径
            bugs_file: Bug数据JSON文件路径 (可选)
            bugs_relation_file: Bug-特性关系表Excel文件路径 (可选)

        Returns:
            分析结果列表
        """
        # 加载特性数据
        print(f"从文件加载特性数据: {features_file}")
        with open(features_file, 'r', encoding='utf-8') as f:
            features = json.load(f)
        print(f"加载了 {len(features)} 个特性")

        # 加载Bug数据
        bugs_by_feature = {}
        if bugs_file:
            print(f"从文件加载Bug数据: {bugs_file}")
            with open(bugs_file, 'r', encoding='utf-8') as f:
                all_bugs = json.load(f)
            print(f"加载了 {len(all_bugs)} 个Bug")

            # 如果提供了Bug-特性关系表，加载它
            if bugs_relation_file and os.path.exists(bugs_relation_file):
                print(f"加载Bug-特性关系表: {bugs_relation_file}")
                bugs_by_feature = self._load_bug_relations(all_bugs, bugs_relation_file)
            else:
                # 尝试从Bug数据中直接读取关联特性
                for bug in all_bugs:
                    if 'linked_feature' in bug and bug['linked_feature']:
                        feature_id = bug['linked_feature']
                        if feature_id not in bugs_by_feature:
                            bugs_by_feature[feature_id] = []
                        bugs_by_feature[feature_id].append(bug)

        # 分析每个特性
        results = []
        for feature in features:
            feature_key = feature['key']
            linked_bugs = bugs_by_feature.get(feature_key, [])

            # 分析质量
            result = self.analyze_feature_quality(feature, linked_bugs)
            results.append(result)

        return results

    def _load_bug_relations(self, bugs: List[Dict[str, Any]], relation_file: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        从关系表加载Bug-特性关系

        Args:
            bugs: Bug列表
            relation_file: 关系表文件路径

        Returns:
            按特性ID组织的Bug字典
        """
        bugs_by_feature = {}
        relations_df = pd.read_excel(relation_file)

        # 查找列名
        bug_col = None
        feature_col = None

        # 尝试常见的列名
        for col in relations_df.columns:
            if col.lower() in ['bug id', 'bug_id', 'bugid', 'bug']:
                bug_col = col
            elif col.lower() in ['feature', 'feature_id', 'featureid', '相关特性', '特性']:
                feature_col = col

        if bug_col and feature_col:
            # 创建Bug ID到特性ID的映射
            bug_to_feature = {}
            for _, row in relations_df.iterrows():
                bug_id = row[bug_col]
                feature_id = row[feature_col]
                if pd.notna(feature_id) and feature_id != "未确定":
                    bug_to_feature[bug_id] = feature_id

            # 根据关系表组织Bug
            for bug in bugs:
                bug_id = bug['key']
                if bug_id in bug_to_feature:
                    feature_id = bug_to_feature[bug_id]
                    if feature_id not in bugs_by_feature:
                        bugs_by_feature[feature_id] = []
                    bugs_by_feature[feature_id].append(bug)
        else:
            print("警告: 无法在关系表中找到Bug ID或特性ID列")

        return bugs_by_feature

    def generate_quality_report(self, results: List[Dict[str, Any]], output_file: str) -> Optional[pd.DataFrame]:
        """
        生成质量报告

        Args:
            results: 分析结果列表
            output_file: 输出文件路径

        Returns:
            结果数据框，如果生成失败则返回None
        """
        if not results:
            print("没有分析结果，无法生成报告")
            return None

        # 处理特殊字段以便转换为DataFrame
        processed_results = []
        for result in results:
            processed_result = result.copy()
            processed_result["severity_distribution"] = json.dumps(result["severity_distribution"])
            processed_result["priority_distribution"] = json.dumps(result["priority_distribution"])
            processed_results.append(processed_result)

        # 创建数据框
        df = pd.DataFrame(processed_results)

        # 优化列顺序
        columns_order = [
            "feature_key", "feature_summary", "quality_grade", "quality_score",
            "total_bugs", "open_bugs", "resolved_bugs", "resolution_rate",
            "avg_resolution_time", "recent_bugs", "avg_severity"
        ]

        # 确保所有列都存在
        columns_order = [col for col in columns_order if col in df.columns]

        # 添加其他未明确指定的列
        for col in df.columns:
            if col not in columns_order:
                columns_order.append(col)

        # 重新排序列
        df = df[columns_order]

        # 将结果保存到Excel
        if output_file:
            try:
                # 尝试创建Excel报告
                self._create_excel_report(df, output_file)
                print(f"质量报告已保存到 {output_file}")
            except Exception as e:
                print(f"保存Excel报告失败: {str(e)}")
                # 尝试使用基本的Excel保存
                df.to_excel(output_file, index=False)
                print(f"已使用基本格式保存报告到 {output_file}")

        return df

    def _create_excel_report(self, df: pd.DataFrame, output_file: str) -> None:
        """
        创建格式化的Excel报告

        Args:
            df: 数据框
            output_file: 输出文件路径
        """
        try:
            import xlsxwriter
        except ImportError:
            print("警告: 未安装xlsxwriter库，将使用基本Excel格式")
            df.to_excel(output_file, index=False)
            return

        # 创建Excel writer
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            # 写入主表
            df.to_excel(writer, sheet_name='质量报告', index=False)

            # 获取工作簿和工作表对象
            workbook = writer.book
            worksheet = writer.sheets['质量报告']

            # 定义格式
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'bg_color': '#D7E4BC',
                'border': 1
            })

            # 调整列宽
            worksheet.set_column('A:A', 12)  # feature_key
            worksheet.set_column('B:B', 40)  # feature_summary
            worksheet.set_column('C:L', 15)  # 其他列

            # 应用条件格式
            self._apply_conditional_formats(workbook, worksheet, df)

            # 创建汇总统计表
            self._add_summary_sheet(workbook, df)

            # 创建严重性分布表
            self._add_severity_distribution_sheet(workbook, df)

    def _apply_conditional_formats(self, workbook, worksheet, df: pd.DataFrame) -> None:
        """
        应用条件格式

        Args:
            workbook: Excel工作簿对象
            worksheet: 工作表对象
            df: 数据框
        """
        # 质量分数颜色标识
        if 'quality_score' in df.columns:
            col_idx = df.columns.get_loc('quality_score')
            worksheet.conditional_format(1, col_idx, len(df) + 1, col_idx, {
                'type': '3_color_scale',
                'min_color': "#FF9999",
                'mid_color': "#FFFF99",
                'max_color': "#99CC99"
            })

        # 解决率颜色标识
        if 'resolution_rate' in df.columns:
            col_idx = df.columns.get_loc('resolution_rate')
            worksheet.conditional_format(1, col_idx, len(df) + 1, col_idx, {
                'type': '3_color_scale',
                'min_color': "#FF9999",
                'mid_color': "#FFFF99",
                'max_color': "#99CC99"
            })

    def _add_summary_sheet(self, workbook, df: pd.DataFrame) -> None:
        """
        添加汇总统计表

        Args:
            workbook: Excel工作簿对象
            df: 数据框
        """
        # 创建汇总表
        summary_sheet = workbook.add_worksheet('质量汇总')

        # 计算汇总数据
        summary_data = {
            '质量等级': df['quality_grade'].value_counts().sort_index().to_dict(),
            '平均质量分数': df['quality_score'].mean(),
            '平均解决率': df['resolution_rate'].mean() if 'resolution_rate' in df.columns else 0,
            '总Bug数': df['total_bugs'].sum(),
            '未解决Bug数': df['open_bugs'].sum(),
            '已解决Bug数': df['resolved_bugs'].sum() if 'resolved_bugs' in df.columns else 0,
            '平均解决时间(天)': df['avg_resolution_time'].mean() if 'avg_resolution_time' in df.columns else 0,
        }

        # 写入汇总标题
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC'})
        summary_sheet.write(0, 0, '质量汇总统计', header_format)

        # 写入基本统计
        row = 2
        for key, value in summary_data.items():
            if key != '质量等级':
                summary_sheet.write(row, 0, key)
                summary_sheet.write(row, 1, value)
                row += 1

        # 写入质量等级分布
        row += 2
        summary_sheet.write(row, 0, '质量等级分布', header_format)
        row += 1
        summary_sheet.write(row, 0, '等级')
        summary_sheet.write(row, 1, '特性数量')
        row += 1

        for grade, count in sorted(summary_data['质量等级'].items()):
            summary_sheet.write(row, 0, grade)
            summary_sheet.write(row, 1, count)
            row += 1

        # 创建质量等级分布饼图
        self._add_quality_grade_chart(workbook, summary_sheet, summary_data['质量等级'], row)

    def _add_quality_grade_chart(self, workbook, worksheet, grade_data: Dict[str, int], start_row: int) -> None:
        """
        添加质量等级饼图

        Args:
            workbook: Excel工作簿对象
            worksheet: 工作表对象
            grade_data: 等级分布数据
            start_row: 数据起始行
        """
        try:
            # 创建饼图
            chart = workbook.add_chart({'type': 'pie'})

            # 设置饼图数据范围
            num_grades = len(grade_data)
            chart.add_series({
                'name': '质量等级分布',
                'categories': ['质量汇总', start_row - num_grades, 0, start_row - 1, 0],
                'values': ['质量汇总', start_row - num_grades, 1, start_row - 1, 1],
                'data_labels': {'percentage': True}
            })

            # 设置图表标题
            chart.set_title({'name': '特性质量等级分布'})

            # 插入图表
            worksheet.insert_chart('D3', chart, {'x_scale': 1.5, 'y_scale': 1.5})
        except Exception as e:
            print(f"创建图表失败: {str(e)}")

    def _add_severity_distribution_sheet(self, workbook, df: pd.DataFrame) -> None:
        """
        添加严重性分布表

        Args:
            workbook: Excel工作簿对象
            df: 数据框
        """
        try:
            # 创建严重性分布表
            severity_sheet = workbook.add_worksheet('严重性分布')

            # 解析严重性分布数据
            severity_data = []
            for idx, row in df.iterrows():
                feature_key = row['feature_key']
                try:
                    severity_dist = json.loads(row['severity_distribution'])
                    for severity, count in severity_dist.items():
                        severity_data.append({
                            'feature_key': feature_key,
                            'severity': severity,
                            'count': count
                        })
                except Exception:
                    pass

            # 创建透视表
            if severity_data:
                severity_df = pd.DataFrame(severity_data)
                pivot = severity_df.pivot_table(
                    index='feature_key',
                    columns='severity',
                    values='count',
                    aggfunc='sum',
                    fill_value=0
                )

                # 写入工作表
                pivot.to_excel(severity_sheet)

                # 创建堆叠柱状图
                self._add_severity_chart(workbook, severity_sheet, pivot)
        except Exception as e:
            print(f"创建严重性分布表失败: {str(e)}")

    def _add_severity_chart(self, workbook, worksheet, pivot_df: pd.DataFrame) -> None:
        """
        添加严重性分布堆叠柱状图

        Args:
            workbook: Excel工作簿对象
            worksheet: 工作表对象
            pivot_df: 透视表数据框
        """
        try:
            # 创建堆叠柱状图
            chart = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})

            # 获取透视表的维度
            num_rows = len(pivot_df)
            num_cols = len(pivot_df.columns)

            # 为每个严重度添加数据系列
            for col_idx, severity in enumerate(pivot_df.columns):
                chart.add_series({
                    'name': ['严重性分布', 0, col_idx + 1],
                    'categories': ['严重性分布', 1, 0, num_rows, 0],
                    'values': ['严重性分布', 1, col_idx + 1, num_rows, col_idx + 1],
                })

            # 设置图表标题和轴
            chart.set_title({'name': '特性Bug严重程度分布'})
            chart.set_x_axis({'name': '特性'})
            chart.set_y_axis({'name': 'Bug数量'})

            # 插入图表
            worksheet.insert_chart('K2', chart, {'x_scale': 1.5, 'y_scale': 1.5})
        except Exception as e:
            print(f"创建图表失败: {str(e)}")


# 如果作为独立脚本运行，则执行测试
if __name__ == "__main__":
    print("特性质量分析模块 - 测试模式")

    # 创建测试数据
    test_feature = {
        "key": "TEST-1",
        "summary": "测试特性"
    }

    test_bugs = [
        {
            "key": "BUG-1",
            "summary": "测试Bug 1",
            "status": "Open",
            "severity": "Major",
            "priority": "High",
            "created": "2023-01-01T00:00:00Z"
        },
        {
            "key": "BUG-2",
            "summary": "测试Bug 2",
            "status": "Resolved",
            "severity": "Minor",
            "priority": "Medium",
            "created": "2023-01-02T00:00:00Z",
            "resolutiondate": "2023-01-03T00:00:00Z"
        }
    ]

    # 测试分析
    analyzer = FeatureQualityAnalyzer()
    result = analyzer.analyze_feature_quality(test_feature, test_bugs)

    # 打印结果
    print("\n分析结果:")
    for key, value in result.items():
        print(f"{key}: {value}")