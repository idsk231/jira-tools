# Jira Bug 分析工具

这是一个用于分析 Jira Bug 与特性关联关系的工具集，提供以下主要功能：

1. Bug 分析器：分析 Bug 与特性的关联关系
2. 质量分析器：分析特性下的 Bug 质量指标
3. 链接创建器：根据分析结果创建 Jira issues 之间的链接

## 功能特点

- 支持从 Jira 直接获取数据或从本地文件加载数据
- 使用 FastGPT API 进行智能分析
- 支持交互式反馈模式，提高分析准确性
- 提供详细的质量分析报告
- 支持批量创建 Jira issues 之间的链接
- 支持缓存机制，提高处理效率

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/jirabug.git
cd jirabug
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置：
复制 `config.ini.example` 为 `config.ini`，并填写必要的配置信息：
- Jira 服务器地址、用户名和 API Token
- FastGPT API Key 和 API Base URL
- 其他可选配置项

## 使用方法

### 1. Bug 分析器

分析 Bug 与特性的关联关系：

```bash
jira-bug-analyzer --config config.ini [--debug] [--feedback] [--no-feedback] [--clear-cache] [--no-cache]
```

参数说明：
- `--config`: 配置文件路径（默认：config.ini）
- `--debug`: 启用调试模式
- `--feedback`: 启用交互式反馈模式
- `--no-feedback`: 禁用反馈模式
- `--clear-cache`: 清除本地缓存数据
- `--no-cache`: 不使用缓存数据

### 2. 质量分析器

分析特性下的 Bug 质量指标：

```bash
jira-quality-analyzer --config config.ini [--output OUTPUT_FILE] [--mode {jira,file}] [--features-file FEATURES_FILE] [--bugs-file BUGS_FILE] [--relation-file RELATION_FILE] [--jql JQL] [--use-cache] [--clear-cache] [--debug]
```

参数说明：
- `--config`: 配置文件路径（默认：config.ini）
- `--output`: 输出报告文件路径
- `--mode`: 数据来源模式（jira 或 file）
- `--features-file`: 特性数据 JSON 文件路径（file 模式）
- `--bugs-file`: Bug 数据 JSON 文件路径（file 模式）
- `--relation-file`: Bug-特性关系 Excel 文件路径（file 模式）
- `--jql`: 特性筛选 JQL 语句（jira 模式）
- `--use-cache`: 使用缓存（jira 模式）
- `--clear-cache`: 清除缓存（jira 模式）
- `--debug`: 启用调试模式

### 3. 链接创建器

根据分析结果创建 Jira issues 之间的链接：

```bash
jira-link-creator --config config.ini [--input INPUT_FILE] [--bug-col BUG_COL] [--feature-col FEATURE_COL] [--link-type LINK_TYPE] [--dry-run] [--skip-existing] [--debug]
```

参数说明：
- `--config`: 配置文件路径（默认：config.ini）
- `--input`: 关联关系输入文件（Excel）
- `--bug-col`: Bug ID 列名（默认：Bug ID）
- `--feature-col`: 特性 ID 列名（默认：相关特性）
- `--link-type`: 链接类型（默认：Relates）
- `--dry-run`: 干运行模式，不实际创建链接
- `--skip-existing`: 跳过已存在的链接
- `--debug`: 启用调试模式

## 配置说明

配置文件 `config.ini` 包含以下主要部分：

### [Jira]
- `url`: Jira 服务器地址
- `username`: Jira 用户名
- `token`: Jira API Token

### [FastGPT]
- `api_key`: FastGPT API Key
- `api_base`: FastGPT API Base URL

### [Filters]
- `bug_filter`: Bug 筛选 JQL
- `feature_filter`: 特性筛选 JQL

### [Output]
- `output_file`: 输出文件路径
- `features_file`: 特性数据文件路径
- `bugs_file`: Bug 数据文件路径
- `quality_report_file`: 质量报告文件路径

### [Feedback]
- `enable`: 是否启用反馈机制
- `feedback_file`: 反馈历史文件路径
- `similarity_threshold`: 相似度阈值
- `max_feedback_examples`: 最大使用的历史反馈数量
- `vector_db_path`: 向量数据库路径
- `conflict_strategy`: 反馈冲突解决策略
- `use_advanced_similarity`: 是否使用高级相似度计算

### [Advanced]
- `model_name`: 使用的模型名称
- `max_bugs`: 最大处理的 bug 数量
- `min_confidence`: 相似度阈值

## 依赖项

主要依赖：
- pandas>=1.3.0
- openai>=1.0.0
- requests>=2.25.0
- jira>=3.0.0
- tqdm>=4.62.0
- xlsxwriter>=3.0.0

可选依赖（用于高级功能）：
- scikit-learn>=1.0.0
- sentence-transformers>=2.2.0
- faiss-cpu>=1.7.0

## 许可证

MIT License