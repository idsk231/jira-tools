# Jira Bug 分析与特性管理工具包

这是一个强大的工具包，用于分析 Jira bug 单与特性需求的关联、创建链接关系和评估特性质量。该工具包包含三个主要功能模块，均使用模块化设计便于维护和扩展。

## 主要功能

1. **Bug 与特性关联分析**：使用 FastGPT（或兼容 OpenAI API 的大语言模型）自动判断每个 bug 与哪个特性需求相关
2. **Jira 链接创建**：根据分析结果自动在 Jira 中创建 bug 与特性之间的链接关系
3. **特性质量评估**：分析每个特性下的 bug 数量、状态、严重程度和优先级等，生成质量评估报告

## 文件结构

```
jira-tools/
├── jirabug/                    # 主包目录
│   ├── core/                   # 核心功能模块
│   │   ├── jira_client.py      # Jira API 客户端
│   │   ├── fastgpt_client.py   # FastGPT 客户端
│   │   ├── config.py           # 配置管理
│   │   └── utils.py            # 工具函数
│   ├── analysis/               # 分析模块
│   │   ├── feature_analyzer.py # 特性质量分析
│   │   └── feedback.py         # 反馈管理
│   ├── cli/                    # 命令行接口
│   │   ├── bug_analyzer_cli.py # Bug分析工具
│   │   ├── link_creator_cli.py # 链接创建工具
│   │   └── quality_analyzer_cli.py # 质量分析工具
│   └── service/                # 服务层
├── config/                     # 配置目录
├── docs/                       # 文档目录
├── setup.py                    # 安装配置
└── requirements.txt            # 依赖列表
```

## 安装与配置

### 1. 环境要求

- Python 3.7+
- 所需第三方库

### 2. 安装依赖

```bash
# 基本依赖
pip install -r requirements.txt

# 可选的高级功能依赖
pip install scikit-learn sentence-transformers faiss-cpu
```

### 3. 配置

复制并编辑 `config/config.ini` 文件，填写必要信息：

```ini
[Jira]
url = https://your-jira-instance.atlassian.net
username = your-email@example.com
token = your-jira-api-token

[FastGPT]
api_key = your-fastgpt-api-key
api_base = https://api.fastgpt.io/v1

[Filters]
bug_filter = project = PROJ AND issuetype = Bug
feature_filter = project = PROJ AND issuetype = Feature

[Output]
output_file = bug_analysis_results.xlsx
features_file = jira_features.json
bugs_file = jira_bugs.json

[Feedback]
enable = true
feedback_file = feedback_history.csv
similarity_threshold = 0.7
max_feedback_examples = 5

[Advanced]
model_name = gpt-3.5-turbo
max_bugs = 0
min_confidence = 0.6
use_cache = true
clear_cache = false
```

## 使用方法

### 1. Bug 与特性关联分析

```bash
jira-bug-analyzer --config config/config.ini
```

选项:
- `--debug`: 启用调试模式，输出详细分析信息
- `--feedback`: 启用交互式反馈模式
- `--no-cache`: 不使用缓存数据
- `--clear-cache`: 清除本地缓存数据

此工具会:
1. 从Jira拉取bug和特性需求
2. 使用FastGPT分析每个bug与哪个特性相关
3. 将结果保存到Excel文件和JSON文件
4. 如果启用反馈模式，允许用户纠正错误的关联并保存反馈

### 2. 创建Jira链接关系

```bash
jira-link-creator --config config/config.ini --input bug_analysis_results.xlsx
```

选项:
- `--bug-col`: Bug ID列名 (默认: "Bug ID")
- `--feature-col`: 特性ID列名 (默认: "相关特性")
- `--link-type`: 链接类型 (默认: "Relates")
- `--dry-run`: 干运行模式，不实际创建链接
- `--skip-existing`: 跳过已存在的链接

此工具会根据关联分析结果，自动在Jira中创建bug与特性之间的链接关系。

### 3. 特性质量分析

```bash
jira-quality-analyzer --config config/config.ini --output feature_quality_report.xlsx
```

选项:
- `--mode`: 数据来源模式，jira=直接从Jira获取，file=从本地文件获取 (默认: file)
- `--features-file`: 特性数据JSON文件路径 (file模式)
- `--bugs-file`: Bug数据JSON文件路径 (file模式)
- `--relation-file`: Bug-特性关系Excel文件路径 (file模式)
- `--jql`: 特性筛选JQL语句 (jira模式)
- `--use-cache`: 使用缓存 (jira模式)

此工具会分析每个特性下的bug情况，评估特性质量，生成详细的质量报告。

## 反馈机制

该工具包实现了完整的反馈循环系统:

1. 系统进行初始分析，判断bug与特性的关联
2. 用户可以纠正不准确的结果，并提供理由
3. 反馈被保存到历史记录中
4. 分析新bug时，系统会查找相似的历史反馈，应用学到的模式

随着使用时间的增长和反馈的积累，系统会变得越来越准确。

## 数据缓存

为了减少对Jira API的请求次数，工具会将拉取的数据缓存在本地：

- 特性数据: `jira_features.json`
- Bug数据: `jira_bugs.json`
- 关联关系数据: `bug_analysis_results.xlsx`

如果您的Jira数据有更新，可以使用 `--clear-cache` 参数清除缓存，或 `--no-cache` 参数忽略缓存。

## 质量评估方法

特性质量分析基于多个指标：

1. **Bug总数**: 与特性关联的bug总数
2. **未解决Bug**: 状态为未解决的bug数量
3. **严重程度分布**: 不同严重程度bug的数量分布
4. **解决率**: 已解决bug占总bug的百分比
5. **平均解决时间**: bug的平均解决时间
6. **最近bug趋势**: 最近一个月新增的bug数量

基于以上指标计算质量分数和等级(A+到F)，为项目管理提供直观的质量度量。

## 注意事项

1. **API令牌安全**: 请妥善保管Jira和FastGPT的API令牌
2. **API限制**: 请注意Jira和FastGPT API的使用限制和配额
3. **数据备份**: 建议在修改Jira数据(如创建链接)前进行备份

## 扩展与自定义

该工具包采用模块化设计，可以方便地进行扩展和定制：

1. 修改 `fastgpt_client.py` 以支持不同的LLM提供商
2. 在 `feature_analyzer.py` 中调整质量评估算法
3. 通过继承 `FeedbackManager` 类实现更高级的反馈处理机制

## 疑难解答

**问题**: 连接Jira失败
- 检查Jira URL格式是否正确
- 验证用户名和API令牌是否有效

**问题**: FastGPT分析不准确
- 尝试使用更高级的模型(如GPT-4)
- 启用反馈机制，提供更多的纠正样本

**问题**: 特性质量分析结果不准确
- 确保bug与特性之间已正确建立链接关系
- 检查Jira中的字段配置，特别是自定义字段

## 许可证

本项目使用MIT许可证。

## 联系方式

如有问题或建议，请提交Issue或联系作者。