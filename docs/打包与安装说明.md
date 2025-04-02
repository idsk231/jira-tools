# Jira Bug 分析与特性管理工具包 - 打包与安装说明

本文档提供了如何打包和安装这套工具包的详细说明。

## 文件清单

请确保你有以下文件：

### 核心模块
1. `config_utils.py` - 配置工具模块
2. `jira_client.py` - Jira API 客户端模块
3. `fastgpt_client.py` - FastGPT 客户端模块 
4. `feedback_manager.py` - 用户反馈管理模块
5. `feature_quality_analyzer.py` - 特性质量分析模块

### 主程序
6. `jira_bug_analyzer_main.py` - Bug分析工具主程序
7. `jira_link_creator_main.py` - 链接创建工具主程序
8. `feature_quality_analyzer_main.py` - 质量分析工具主程序

### 配置与文档
9. `config.ini.example` - 配置文件示例
10. `README.md` - 使用说明文档

## 目录结构设置

建议按照以下结构组织文件：

```
jira-tools/
├── modules/
│   ├── __init__.py              # 空文件，使模块可导入
│   ├── config_utils.py
│   ├── jira_client.py
│   ├── fastgpt_client.py
│   ├── feedback_manager.py
│   └── feature_quality_analyzer.py
├── jira_bug_analyzer_main.py
├── jira_link_creator_main.py
├── feature_quality_analyzer_main.py
├── config.ini.example
├── README.md
└── requirements.txt             # 依赖列表
```

## 创建requirements.txt

创建一个`requirements.txt`文件，包含以下内容：

```
pandas>=1.3.0
openai>=1.0.0
requests>=2.25.0
jira>=3.0.0
tqdm>=4.62.0
xlsxwriter>=3.0.0
# 可选的高级功能依赖
scikit-learn>=1.0.0
sentence-transformers>=2.2.0
faiss-cpu>=1.7.0
```

## 安装步骤

### 1. 下载或克隆代码库

确保所有文件都已下载并按照上述目录结构组织。

### 2. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 安装基本依赖
pip install -r requirements.txt
```

### 4. 配置

```bash
# 复制配置文件示例
cp config.ini.example config.ini

# 编辑配置文件，填入你的Jira和FastGPT信息
nano config.ini  # 或使用任何文本编辑器
```

## 使用方法

参考`README.md`中的详细使用说明。基本用法如下：

1. **分析Bug与特性关联**:
   ```bash
   python jira_bug_analyzer_main.py --config config.ini
   ```

2. **创建Jira链接**:
   ```bash
   python jira_link_creator_main.py --config config.ini --input bug_analysis_results.xlsx
   ```

3. **分析特性质量**:
   ```bash
   python feature_quality_analyzer_main.py --config config.ini --mode file
   ```

## 模块导入修改

如果你使用了上述推荐的目录结构，需要修改主程序中的导入语句：

```python
# 原导入
from config_utils import load_config
from jira_client import JiraClient
from fastgpt_client import FastGPTClient
from feedback_manager import FeedbackManager
from feature_quality_analyzer import FeatureQualityAnalyzer

# 修改为
from modules.config_utils import load_config
from modules.jira_client import JiraClient
from modules.fastgpt_client import FastGPTClient
from modules.feedback_manager import FeedbackManager
from modules.feature_quality_analyzer import FeatureQualityAnalyzer
```

## 数据存储

工具会在当前目录创建以下文件和目录：

- `jira_cache/` - Jira数据缓存目录
- `feedback_history.csv` - 反馈历史记录
- `jira_features.json` - 特性数据
- `jira_bugs.json` - Bug数据
- `bug_analysis_results.xlsx` - 分析结果
- `feature_quality_report.xlsx` - 质量报告

## 将工具安装为可执行命令（可选）

如果你希望将这些工具安装为系统命令，可以创建一个`setup.py`文件：

```python
from setuptools import setup, find_packages

setup(
    name="jira-tools",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.3.0",
        "openai>=1.0.0",
        "requests>=2.25.0",
        "jira>=3.0.0",
        "tqdm>=4.62.0",
        "xlsxwriter>=3.0.0",
    ],
    entry_points={
        'console_scripts': [
            'jira-bug-analyzer=jira_bug_analyzer_main:main',
            'jira-link-creator=jira_link_creator_main:main',
            'feature-quality-analyzer=feature_quality_analyzer_main:main',
        ],
    },
)
```

然后执行安装：

```bash
pip install -e .
```

这样就可以直接在命令行中使用这些工具了：

```bash
jira-bug-analyzer --config config.ini
jira-link-creator --config config.ini --input bug_analysis_results.xlsx
feature-quality-analyzer --config config.ini --mode file
```

## 故障排除

如果遇到导入错误，请检查：

1. 目录结构是否正确
2. 模块导入路径是否正确
3. 是否已安装所有依赖

如果遇到API错误，请检查：

1. Jira和FastGPT的API密钥是否正确
2. 网络连接是否正常
3. API请求是否过于频繁，导致被限制

## 注意事项

- 请妥善保管配置文件，避免泄露API密钥
- 首次使用时，建议使用小数据集进行测试
- 对于大型Jira项目，建议设置合理的JQL过滤器，避免获取太多数据
