#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bug分析模块，负责分析Bug与特性的关联。
提供Bug分析的核心功能，包括处理Bug数据和使用FastGPT进行特性关联分析。
"""

import time
from typing import Dict, List, Any, Tuple, Optional, Union

from tqdm import tqdm

from ..core.fastgpt_client import FastGPTClient


def analyze_bugs(
    bugs: List[Any],
    features: List[Any],
    fastgpt_client: FastGPTClient,
    debug_mode: bool = False,
    delay: float = 0.5
) -> List[Dict[str, Any]]:
    """
    分析Bug与特性的关联

    Args:
        bugs: Bug列表（可以是Jira Issue对象或字典）
        features: 特性列表（可以是Jira Issue对象或字典）
        fastgpt_client: FastGPT客户端
        debug_mode: 是否启用调试模式
        delay: API调用间隔时间(秒)

    Returns:
        分析结果列表
    """
    # 准备特性数据
    feature_list_for_gpt = prepare_feature_data_for_gpt(features)

    # 分析结果列表
    results = []

    print("开始分析Bug与特性需求的关系...")
    for bug in tqdm(bugs):
        # 提取Bug信息
        bug_data = extract_bug_data(bug)

        if debug_mode:
            print(f"\n正在分析Bug: {bug_data['key']} - {bug_data['summary']}")

        # 使用FastGPT分析
        feature_id, analysis_result = fastgpt_client.analyze_bug(
            bug_data['summary'],
            bug_data['description'],
            feature_list_for_gpt
        )

        # 解析分析结果
        feature_id, confidence, reason = fastgpt_client.parse_analysis_result(analysis_result)

        if debug_mode:
            print(f"分析结果: 特性ID={feature_id}, 相关度={confidence}")
            if reason:
                print(f"分析理由: {reason}")

        # 创建结果条目
        result_entry = {
            "Bug ID": bug_data['key'],
            "Bug标题": bug_data['summary'],
            "Bug状态": bug_data['status'],
            "创建时间": bug_data['created'],
            "相关特性": feature_id,
            "相关度": confidence,
            "分析理由": reason
        }

        results.append(result_entry)

        # 避免API调用过快
        time.sleep(delay)

    return results


def prepare_feature_data_for_gpt(features: List[Any]) -> List[Dict[str, str]]:
    """
    准备用于GPT分析的特性数据

    Args:
        features: 特性列表（可以是Jira Issue对象或字典）

    Returns:
        简化的特性数据列表
    """
    feature_list = []

    for feature in features:
        if hasattr(feature, 'key'):
            # 处理Jira Issue对象
            feature_list.append({
                "key": feature.key,
                "summary": feature.fields.summary
            })
        else:
            # 处理字典对象
            feature_list.append({
                "key": feature["key"],
                "summary": feature["summary"]
            })

    return feature_list


def extract_bug_data(bug: Any) -> Dict[str, str]:
    """
    从Bug对象中提取必要的数据

    Args:
        bug: Bug对象（可以是Jira Issue对象或字典）

    Returns:
        包含Bug数据的字典
    """
    if hasattr(bug, 'key'):
        # 处理Jira Issue对象
        bug_key = bug.key
        bug_summary = bug.fields.summary

        # 处理bug描述，可能是富文本或纯文本
        bug_description = ""
        if hasattr(bug.fields, "description") and bug.fields.description:
            if isinstance(bug.fields.description, str):
                bug_description = bug.fields.description
            else:
                # 尝试处理富文本描述，简化处理
                bug_description = "复杂描述，请在Jira中查看"

        bug_status = bug.fields.status.name if hasattr(bug.fields, "status") else ""
        bug_created = str(bug.fields.created) if hasattr(bug.fields, "created") else ""
    else:
        # 处理字典对象
        bug_key = bug.get("key", "")
        bug_summary = bug.get("summary", "")
        bug_description = bug.get("description", "")
        bug_status = bug.get("status", "")
        bug_created = bug.get("created", "")

    return {
        "key": bug_key,
        "summary": bug_summary,
        "description": bug_description,
        "status": bug_status,
        "created": bug_created
    }


def filter_bugs(bugs: List[Any], max_bugs: int = 0, jql_filter: str = None) -> List[Any]:
    """
    过滤Bug列表

    Args:
        bugs: Bug列表
        max_bugs: 最大Bug数量，0表示不限制
        jql_filter: JQL过滤条件（尚未实现）

    Returns:
        过滤后的Bug列表
    """
    # 如果设置了最大处理数量限制
    if max_bugs > 0 and len(bugs) > max_bugs:
        print(f"根据配置限制，将只处理前 {max_bugs} 个Bug单")
        return bugs[:max_bugs]

    # TODO: 实现基于JQL的过滤

    return bugs


def enrich_bug_data(
    bugs: List[Dict[str, Any]],
    feature_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    使用分析结果丰富Bug数据

    Args:
        bugs: 原始Bug数据列表
        feature_results: 特性分析结果列表

    Returns:
        丰富后的Bug数据列表
    """
    # 创建Bug ID到特性的映射
    bug_feature_map = {}
    for result in feature_results:
        bug_id = result["Bug ID"]
        bug_feature_map[bug_id] = {
            "feature_id": result["相关特性"],
            "confidence": result["相关度"],
            "reason": result.get("分析理由", "")
        }

    # 丰富Bug数据
    enriched_bugs = []
    for bug in bugs:
        bug_id = bug["key"]
        enriched_bug = bug.copy()

        if bug_id in bug_feature_map:
            enriched_bug["linked_feature"] = bug_feature_map[bug_id]["feature_id"]
            enriched_bug["feature_confidence"] = bug_feature_map[bug_id]["confidence"]
            enriched_bug["feature_reason"] = bug_feature_map[bug_id]["reason"]

        enriched_bugs.append(enriched_bug)

    return enriched_bugs


def get_bug_statistics(bugs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    获取Bug统计信息

    Args:
        bugs: Bug列表

    Returns:
        统计信息字典
    """
    # 基本统计
    total_bugs = len(bugs)

    # 特性关联统计
    bugs_with_feature = sum(1 for bug in bugs if bug.get("linked_feature"))
    linking_rate = (bugs_with_feature / total_bugs * 100) if total_bugs > 0 else 0

    # 置信度统计
    confidence_high = sum(1 for bug in bugs
                         if bug.get("feature_confidence") in ["高", "High"])
    confidence_medium = sum(1 for bug in bugs
                           if bug.get("feature_confidence") in ["中", "Medium"])
    confidence_low = sum(1 for bug in bugs
                        if bug.get("feature_confidence") in ["低", "Low"])

    # 返回统计结果
    return {
        "total_bugs": total_bugs,
        "bugs_with_feature": bugs_with_feature,
        "linking_rate": linking_rate,
        "confidence_distribution": {
            "high": confidence_high,
            "medium": confidence_medium,
            "low": confidence_low,
            "unknown": total_bugs - confidence_high - confidence_medium - confidence_low
        }
    }


# 如果作为独立脚本运行，则执行测试
if __name__ == "__main__":
    print("Bug分析模块 - 测试模式")

    # 创建测试数据
    test_features = [
        {"key": "FEAT-1", "summary": "用户登录功能"},
        {"key": "FEAT-2", "summary": "数据导出功能"}
    ]

    test_bugs = [
        {
            "key": "BUG-1",
            "summary": "登录页面崩溃",
            "description": "用户在登录页面输入用户名和密码后点击登录按钮，页面崩溃。",
            "status": "Open",
            "created": "2023-01-01T00:00:00Z"
        }
    ]

    # 测试功能
    print("测试 prepare_feature_data_for_gpt 函数...")
    feature_data = prepare_feature_data_for_gpt(test_features)
    print(f"特性数据: {feature_data}")

    print("\n测试 extract_bug_data 函数...")
    bug_data = extract_bug_data(test_bugs[0])
    print(f"Bug数据: {bug_data}")