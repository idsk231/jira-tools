#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""配置管理模块。"""

import os
import configparser
from typing import Optional, Dict, Any

def load_config(config_file: str) -> Optional[configparser.ConfigParser]:
    """
    从配置文件加载设置

    参数:
        config_file (str): 配置文件路径

    返回:
        configparser.ConfigParser: 配置对象，如果加载失败则返回None
    """
    config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        print(f"配置文件 {config_file} 不存在，将创建示例配置文件")
        create_sample_config(config_file)
        return None

    config.read(config_file, encoding='utf-8')

    # 验证必要的配置项
    required_sections = ['Jira', 'FastGPT', 'Filters']
    required_options = {
        'Jira': ['url', 'username', 'token'],
        'FastGPT': ['api_key'],
        'Filters': ['bug_filter', 'feature_filter']
    }

    # 检查必要的配置
    for section in required_sections:
        if section not in config:
            print(f"配置文件缺少必要的部分: [{section}]")
            return None
        for option in required_options[section]:
            if option not in config[section]:
                print(f"配置文件 [{section}] 部分缺少必要的选项: {option}")
                return None

    return config

def create_sample_config(config_file: str) -> None:
    """
    创建示例配置文件

    参数:
        config_file (str): 配置文件路径
    """
    config = configparser.ConfigParser()

    config['Jira'] = {
        'url': 'https://your-jira-instance.atlassian.net',
        'username': 'your-email@example.com',
        'token': 'your-jira-api-token'
    }

    config['FastGPT'] = {
        'api_key': 'your-fastgpt-api-key',
        'api_base': 'https://api.fastgpt.io/v1'
    }

    config['Filters'] = {
        'bug_filter': 'project = PROJ AND issuetype = Bug',
        'feature_filter': 'project = PROJ AND issuetype = Feature'
    }

    config['Output'] = {
        'output_file': 'bug_analysis_results.xlsx',
        'features_file': 'jira_features.json',
        'bugs_file': 'jira_bugs.json'
    }

    config['Feedback'] = {
        'enable': 'true',
        'feedback_file': 'feedback_history.csv',
        'similarity_threshold': '0.7',
        'max_feedback_examples': '5'
    }

    config['Advanced'] = {
        'model_name': 'gpt-3.5-turbo',
        'max_bugs': '0',
        'min_confidence': '0.6',
        'use_cache': 'true',
        'clear_cache': 'false'
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        config.write(f)

    print(f"已创建示例配置文件 {config_file}，请编辑后再运行程序")

def get_jira_config(config: configparser.ConfigParser) -> Dict[str, str]:
    """
    获取Jira配置部分

    Args:
        config: 配置对象

    Returns:
        Jira配置字典
    """
    return {
        'url': config['Jira']['url'],
        'username': config['Jira']['username'],
        'token': config['Jira']['token']
    }


def get_fastgpt_config(config: configparser.ConfigParser) -> Dict[str, str]:
    """
    获取FastGPT配置部分

    Args:
        config: 配置对象

    Returns:
        FastGPT配置字典
    """
    return {
        'api_key': config['FastGPT']['api_key'],
        'api_base': config['FastGPT'].get('api_base', 'https://api.fastgpt.io/v1')
    }