#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastGPT客户端模块 - 负责与FastGPT/OpenAI API交互，分析Bug与特性的关联
"""

import json
from typing import Tuple, List, Dict, Any, Optional

from openai import OpenAI


class FastGPTClient:
    def __init__(self, api_key: str, api_base: str = "https://api.fastgpt.io/v1",
                 feedback_manager: Optional[Any] = None,
                 model_name: str = "gpt-3.5-turbo"):
        """
        初始化FastGPT客户端

        Args:
            api_key: API密钥
            api_base: API基础URL
            feedback_manager: 可选的反馈管理器对象
            model_name: 使用的模型名称
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        self.feedback_manager = feedback_manager
        self.model_name = model_name

    def analyze_bug(self, bug_title: str, bug_description: str, feature_list: List[Dict[str, Any]]) -> Tuple[str, str]:
        """
        使用FastGPT分析bug与哪个特性需求相关

        Args:
            bug_title: Bug标题
            bug_description: Bug描述
            feature_list: 特性列表

        Returns:
            Tuple[str, str]: (特性ID, 完整分析结果)
        """
        # 提取bug的关键词和特征
        query_prompt = f"""
        分析以下Jira Bug单的标题和描述，提取5-10个关键词或短语，这些关键词应该能够帮助确定该bug属于哪个特性需求：

        标题: {bug_title}
        描述: {bug_description}

        仅返回关键词或短语列表，每行一个，不要有其他解释。
        """

        try:
            # 第一步：提取关键词
            keywords_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": query_prompt}],
                temperature=0.3,
                max_tokens=150
            )

            keywords = keywords_response.choices[0].message.content.strip()

            # 构建分析提示
            analysis_prompt = f"""
            你是一个专业的软件缺陷分类专家。你的任务是将一个bug精确地匹配到最相关的特性需求。

            Bug信息:
            - 标题: {bug_title}
            - 描述: {bug_description}
            - 提取的关键词/特征:
            {keywords}

            可能相关的特性需求:
            {json.dumps(feature_list, ensure_ascii=False, indent=2)}

            分析步骤:
            1. 仔细阅读bug的标题、描述和关键词
            2. 分析每个特性需求的范围和关注点
            3. 找出bug与特性之间的技术重叠或功能关联
            4. 考虑代码模块、用户体验流程或功能区域的重合
            5. 判断最可能相关的特性需求

            你的回答必须遵循以下格式:
            特性ID: [最相关特性的Jira ID]
            相关度: [高/中/低]
            理由: [简短分析理由，最多3句话]

            如果无法确定相关特性，请返回:
            特性ID: 未确定
            相关度: 无
            理由: [为什么无法确定]
            """

            final_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1,
                max_tokens=250
            )

            result = final_response.choices[0].message.content.strip()
            feature_id, _, _ = self.parse_analysis_result(result)

            return feature_id, result

        except Exception as e:
            error_msg = f"FastGPT API调用异常: {str(e)}"
            print(error_msg)
            return "未确定", error_msg

    @staticmethod
    def parse_analysis_result(analysis_result: str) -> Tuple[str, str, str]:
        """
        解析分析结果，提取特性ID、相关度和理由

        Args:
            analysis_result: 分析结果文本

        Returns:
            Tuple[str, str, str]: (特性ID, 相关度, 理由)
        """
        feature_id = "未确定"
        confidence = "未知"
        reason = ""

        if isinstance(analysis_result, str) and "\n" in analysis_result:
            lines = analysis_result.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("特性ID:"):
                    feature_id = line.replace("特性ID:", "").strip()
                elif line.startswith("相关度:"):
                    confidence = line.replace("相关度:", "").strip()
                elif line.startswith("理由:"):
                    reason = line.replace("理由:", "").strip()

        return feature_id, confidence, reason