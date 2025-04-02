#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jirabug",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Jira Bug Analysis & Feature Management Tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/jirabug",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pandas>=1.3.0",
        "openai>=1.0.0", 
        "requests>=2.25.0",
        "jira>=3.0.0",
        "tqdm>=4.62.0",
        "xlsxwriter>=3.0.0",
    ],
    extras_require={
        "advanced": [
            "scikit-learn>=1.0.0",
            "sentence-transformers>=2.2.0",
            "faiss-cpu>=1.7.0",
        ],
    },
    entry_points={
        'console_scripts': [
            'jira-bug-analyzer=jirabug.cli.bug_analyzer_cli:main',
            'jira-link-creator=jirabug.cli.link_creator_cli:main',
            'jira-quality-analyzer=jirabug.cli.quality_analyzer_cli:main',
        ],
    },
    python_requires='>=3.7',
)
