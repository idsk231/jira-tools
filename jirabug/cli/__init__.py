#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令行接口模块

提供各种命令行工具，包括Bug分析、链接创建、质量分析等。
"""

from .bug_analyzer_cli import main as bug_analyzer_main
from .link_creator_cli import main as link_creator_main
from .quality_analyzer_cli import main as quality_analyzer_main

__all__ = [
    'bug_analyzer_main',
    'link_creator_main',
    'quality_analyzer_main'
]