# AI模型集成模块

此模块将多种AI模型（Claude、OpenAI等）与团队上下文管理进行了模块化重构，实现了功能分离和结果分开存放。

## 模块结构

```
src/agent/claude/
├── __init__.py                    # 模块导出
├── ai_model_factory.py           # AI模型工厂（多模型支持）
├── ai_model_base.py              # AI模型基类
├── claude_model_impl.py          # Claude模型实现
├── openai_model_impl.py          # OpenAI模型实现
├── model_usage_manager.py        # 多模型使用和上下文集成
├── model_storage_manager.py      # 通用结果存储管理
├── model_runner.py              # 多模型运行器
├── claude_api_client.py          # 原始Claude API客户端（向后兼容）
└── README.md                     # 本文档
```

## 核心功能

### 1. AI模型工厂（ai_model_factory.py）
- 支持多个AI提供商：Claude (Anthropic)、OpenAI
- 统一的模型创建接口和配置管理
- 工厂模式设计，易于扩展新的AI提供商

### 2. 模型实现层
- **ai_model_base.py**: 定义统一的AI模型接口
- **claude_model_impl.py**: Claude模型具体实现
- **openai_model_impl.py**: OpenAI模型具体实现

### 3. 使用管理（model_usage_manager.py）  
- **ModelUsageManager**: 多AI模型的团队上下文生成和集成
- 自动生成团队系统提示词
- 支持多种上下文模式（framework_only, memory_only, hybrid）
- 处理多种AI模型API调用和结果整合

### 4. 存储管理（model_storage_manager.py）
- **ModelStorageManager**: 通用的AI模型结果存储
- 分开存放系统提示词和AI响应内容
- 自动创建分类目录结构
- 支持元数据记录和文件管理

### 5. 运行器（model_runner.py）
- **ModelRunner**: 整合所有功能的主调用接口
- 支持多种AI模型的综合测试和完整工作流
- 自动处理结果保存和分类

## 存储结构

运行后会自动创建以下目录结构：

```
output/
├── system_prompts/           # 系统提示词文件
│   └── YYYYMMDD_HHMMSS_team_mode_system_prompt.txt
├── ai_responses/            # AI模型响应内容
│   └── YYYYMMDD_HHMMSS_team_ai_response.md  
└── metadata/                # 元数据JSON文件
    └── YYYYMMDD_HHMMSS_metadata.json
```

## 使用方法

### 快速开始

```python
# 方法1: 使用运行器（推荐）
from src.agent.claude import create_claude_runner

runner = create_claude_runner()  # 向后兼容，实际返回ModelRunner
result = runner.run_with_context(  # 新方法名，更通用
    user_message="请帮我设计一个API",
    team_name="engineering_team",
    mode="framework_only"
)
```

### 分模块使用

```python
# 单独使用模型
from src.agent.claude import create_claude_model
model = create_claude_model()
result = model.create_message("你好", "你是一个助手")

# 单独使用上下文  
from src.agent.claude import create_claude_usage
usage = create_claude_usage()
context = usage.generate_team_context("frontend-team", "hybrid")

# 单独使用存储
from src.agent.claude import create_claude_storage
storage = create_claude_storage()
saved_paths = storage.save_complete_result(result)
```

### 运行测试

```bash
# 运行主测试文件
python claude_test_runner.py

# 或者直接运行运行器
python src/agent/claude/claude_runner.py
```

## 配置要求

1. **环境变量**: 需要在 `.env` 文件中配置 `ANTHROPIC_API_KEY`
2. **依赖库**: `pip install anthropic`
3. **团队数据**: 确保 `test_data/teams/` 目录下有团队数据

## 功能特点

### ✅ 已实现功能
- 模型创建与连接测试
- 团队上下文自动生成（多种模式）
- Claude API集成调用
- 结果分类存储（系统提示词、响应、元数据分开）
- comprehensive测试流程
- 向后兼容原始API客户端

### 🔄 与原始版本的区别
- **模块化**: 功能按职责分离到不同模块
- **分离存储**: 系统提示词和响应内容分开保存
- **更好的错误处理**: 每个模块独立的错误处理
- **灵活配置**: 支持独立使用各个模块
- **清晰的目录结构**: 自动创建分类存储目录

## 测试结果

最新测试结果：
- ✅ 基本连接测试：成功（4.63秒响应）
- ✅ 团队上下文生成：成功（支持9个团队）
- ✅ Claude集成测试：成功（52.19秒，8973 tokens）

结果自动分开保存到：
- `output/system_prompts/` - 系统提示词（9279字符）
- `output/claude_responses/` - Claude响应（9484字符）
- `output/metadata/` - 元数据记录（JSON格式） 