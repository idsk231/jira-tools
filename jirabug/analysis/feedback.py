#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
反馈管理模块 - 负责管理用户对分析结果的反馈，用于改进后续分析
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional


class FeedbackManager:
    """
    管理用户对分析结果的反馈，用于改进后续分析
    """
    def __init__(self, feedback_file="feedback_history.csv"):
        self.feedback_file = feedback_file
        self.feedback_data = []
        self.similarity_threshold = 0.7  # 相似度阈值
        self.max_feedback_examples = 5   # 最大返回的相关反馈数量
        self.load_feedback()

    def load_feedback(self):
        """加载历史反馈数据"""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    self.feedback_data = list(reader)
                print(f"已加载 {len(self.feedback_data)} 条历史反馈记录")
            except Exception as e:
                print(f"加载反馈历史失败: {str(e)}")
                self.feedback_data = []

    def save_feedback(self, bug_id, bug_title, predicted_feature, correct_feature, reason=None):
        """
        保存用户反馈

        参数:
            bug_id (str): Bug ID
            bug_title (str): Bug标题
            predicted_feature (str): 预测的特性ID
            correct_feature (str): 正确的特性ID
            reason (str): 纠正理由

        返回:
            bool: 成功返回True，失败返回False
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 添加到内存中的反馈数据
        feedback_entry = {
            "bug_id": bug_id,
            "bug_title": bug_title,
            "predicted_feature": predicted_feature,
            "correct_feature": correct_feature,
            "reason": reason if reason else "",
            "timestamp": timestamp
        }
        self.feedback_data.append(feedback_entry)

        # 确定是否需要创建表头
        file_exists = os.path.exists(self.feedback_file)

        # 写入CSV文件
        try:
            with open(self.feedback_file, 'a', encoding='utf-8', newline='') as f:
                fieldnames = ["bug_id", "bug_title", "predicted_feature", "correct_feature", "reason", "timestamp"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow(feedback_entry)
            print(f"反馈已保存: Bug {bug_id} 应归属于特性 {correct_feature}")
            return True
        except Exception as e:
            print(f"保存反馈失败: {str(e)}")
            return False

    def get_relevant_feedback(self, bug_title, bug_description=""):
        """
        获取与当前bug相关的历史反馈

        参数:
            bug_title (str): Bug标题
            bug_description (str): Bug描述

        返回:
            list: 相关反馈列表
        """
        if not self.feedback_data:
            return []

        # 简单实现：基于标题的文本相似度
        # 可以扩展为更复杂的NLP相似度计算
        relevant_feedback = []

        for entry in self.feedback_data:
            # 计算相似度（简化版）
            similarity = self._calculate_similarity(bug_title, entry["bug_title"])

            if similarity >= self.similarity_threshold:
                entry_copy = entry.copy()
                entry_copy["similarity"] = similarity
                relevant_feedback.append(entry_copy)

        # 按相似度排序并限制返回数量
        relevant_feedback.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return relevant_feedback[:self.max_feedback_examples]

    def _calculate_similarity(self, text1, text2):
        """
        计算两个文本的相似度，可以扩展为更复杂的算法
        目前使用简单的词袋模型和杰卡德相似度

        参数:
            text1 (str): 第一个文本
            text2 (str): 第二个文本

        返回:
            float: 相似度，0-1之间
        """
        # 简单的分词（可以根据语言特点优化）
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # 计算杰卡德相似度
        if not words1 or not words2:
            return 0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0

    def get_feedback_prompt(self, bug_title, bug_description):
        """
        生成考虑历史反馈的提示

        参数:
            bug_title (str): Bug标题
            bug_description (str): Bug描述

        返回:
            str: 反馈提示
        """
        relevant_feedback = self.get_relevant_feedback(bug_title, bug_description)

        if not relevant_feedback:
            return ""  # 无历史反馈

        # 构建反馈提示
        feedback_examples = []
        for entry in relevant_feedback:
            similarity = entry.get('similarity', 0)
            similarity_text = f"(相似度: {similarity:.2f})" if similarity > 0 else ""

            feedback_examples.append(
                f"- Bug '{entry['bug_id']}': '{entry['bug_title']}' 最初被分类为 '{entry['predicted_feature']}'，"
                f"正确分类应为 '{entry['correct_feature']}'。{entry['reason']} {similarity_text}"
            )

        feedback_text = "\n".join(feedback_examples)

        prompt = f"""
        历史反馈案例：
        {feedback_text}

        请注意以上反馈案例中的模式，应用到当前分析中。上述案例按与当前Bug的相关性排序。
        """

        return prompt

def interactive_feedback_mode(bug_results: List[Dict[str, Any]],
                             feature_map: List[Any],
                             feedback_manager: FeedbackManager) -> List[Dict[str, Any]]:
    """
    交互式反馈模式，用户可以纠正错误分类

    Args:
        bug_results: Bug分析结果列表
        feature_map: 特性映射列表
        feedback_manager: 反馈管理器对象

    Returns:
        更新后的Bug分析结果列表
    """

    print("\n=== 进入交互式反馈模式 ===")
    print("在此模式下，您可以纠正错误的分类并提供反馈。")
    print("这些反馈将被保存，并用于改进后续分析。")
    print("输入 'q' 或 'quit' 退出反馈模式。\n")

    # 特性映射字典，用于显示选项
    if hasattr(feature_map[0], 'key'):
        # 处理JIRA Issue对象
        features_by_id = {f.key: f.fields.summary for f in feature_map}
    else:
        # 处理字典对象
        features_by_id = {f["key"]: f["summary"] for f in feature_map}

    features_list = sorted(features_by_id.keys())

    while True:
        # 显示Bug列表
        print("\n当前分析结果:")
        for i, result in enumerate(bug_results, 1):
            bug_id = result["Bug ID"]
            bug_title = result["Bug标题"]
            feature_id = result["相关特性"]
            feature_title = features_by_id.get(feature_id, "未找到特性名称")
            confidence = result.get("相关度", "未知")

            # 格式化显示，突出显示低置信度的结果
            highlight = "" if confidence in ["高", "High"] else " (!)"
            print(f"{i}. {bug_id}: {bug_title[:50]}... => {feature_id} ({confidence}{highlight})")

        # 获取用户输入
        selection = input("\n选择要纠正的Bug编号(1-{})，或输入'q'退出: ".format(len(bug_results)))

        if selection.lower() in ['q', 'quit', 'exit']:
            break

        try:
            idx = int(selection) - 1
            if 0 <= idx < len(bug_results):
                selected_bug = bug_results[idx]

                # 显示当前Bug的详细信息
                print("\n=== Bug 详情 ===")
                print(f"ID: {selected_bug['Bug ID']}")
                print(f"标题: {selected_bug['Bug标题']}")
                print(f"当前分类到特性: {selected_bug['相关特性']}")
                print(f"相关度: {selected_bug.get('相关度', '未知')}")
                if "分析理由" in selected_bug:
                    print(f"分析理由: {selected_bug['分析理由']}")

                # 显示特性列表并请求纠正
                print("\n可用的特性:")
                for i, f_id in enumerate(features_list, 1):
                    print(f"{i}. {f_id}: {features_by_id[f_id][:50]}")

                feature_selection = input("\n选择正确的特性编号，或输入特性ID，或输入'c'取消: ")

                if feature_selection.lower() == 'c':
                    continue

                # 确定正确的特性ID
                correct_feature = None
                if feature_selection.isdigit():
                    f_idx = int(feature_selection) - 1
                    if 0 <= f_idx < len(features_list):
                        correct_feature = features_list[f_idx]
                else:
                    # 用户直接输入了特性ID
                    if feature_selection in features_by_id:
                        correct_feature = feature_selection

                if correct_feature:
                    # 获取反馈原因
                    reason = input("请简要说明为何此Bug应归属于该特性(可选): ")

                    # 保存反馈
                    feedback_manager.save_feedback(
                        selected_bug['Bug ID'],
                        selected_bug['Bug标题'],
                        selected_bug['相关特性'],
                        correct_feature,
                        reason
                    )

                    # 更新结果
                    bug_results[idx]['相关特性'] = correct_feature
                    bug_results[idx]['相关度'] = "高 (用户确认)"
                    if reason:
                        bug_results[idx]['分析理由'] = reason
                else:
                    print("无效的特性选择!")
            else:
                print("选择超出范围!")
        except ValueError:
            print("请输入有效的数字!")

    return bug_results  # 返回可能被修改的结果