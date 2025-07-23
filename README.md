# Software Development Context Management

> 基于团队记忆和结构化框架的智能上下文管理系统

## 🎯 项目概述

Software Development Context Management 是一个面向软件开发团队的智能上下文管理系统。它通过组织团队记忆、管理项目知识和提供结构化的开发框架，帮助团队构建精准的AI上下文，提高开发效率和代码质量。

### 核心功能

- **📋 项目级记忆管理**: 按项目组织团队记忆，支持声明性、程序性和情景性记忆
- **🧠 智能上下文生成**: 基于用户消息智能匹配相关记忆，生成精准上下文
- **📐 七步框架**: 结构化的软件开发框架，指导AI生成高质量的技术方案
- **🔧 多模式支持**: 支持记忆模式、框架模式和混合模式
- **🎨 灵活配置**: 可配置的记忆过滤、重要性阈值和上下文生成策略

## 🏗️ 架构设计

```
src/
├── agent/                  # AI Agent实现
│   ├── claude/            # Claude API集成
│   └── env_config.py      # 环境配置
├── api/                   # API服务
│   └── api_server.py      # REST API服务器
├── commands/              # 命令行工具
│   ├── base_command.py    # 命令基类
│   ├── team_context_command.py    # 团队上下文命令
│   └── team_memory_command.py     # 团队记忆命令
├── core/                  # 核心模块
│   ├── context_processor.py      # 上下文处理器
│   ├── directory_manager.py      # 目录管理器
│   ├── markdown_engine.py        # Markdown存储引擎
│   ├── seven_stage_engine.py     # 七步框架引擎
│   └── ...                       # 其他核心模块
└── seven_stage_framework/ # 七步开发框架
    ├── 00_overview.md     # 框架概述
    ├── 01_requirements.md # 需求锚定
    ├── 02_business_model.md # 业务模型
    ├── 03_solution.md     # 解决方案
    ├── 04_structure.md    # 结构定义
    ├── 05_tasks.md        # 任务编排
    ├── 06_common_tasks.md # 通用任务
    └── 07_constraints.md  # 约束控制
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Git

### 安装

1. **克隆项目**
```bash
git clone <repository-url>
cd software-development-context-management
```

2. **创建虚拟环境**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置API密钥
```

### 基本使用

#### 1. 创建团队和项目

```python
from src.core.directory_manager import DirectoryManager
from pathlib import Path

dm = DirectoryManager(Path("data"))

# 创建团队
team_path = dm.create_team("my_team", "我的开发团队")

# 创建项目
project_path = dm.create_project("my_team", "my_project", "我的项目")
```

#### 2. 生成上下文

```python
from src.core.context_processor import ContextProcessor, create_hybrid_config

processor = ContextProcessor(Path("data"))

# 项目级别上下文
config = create_hybrid_config(
    team_name="my_team",
    project_name="my_project",
    stages=["requirements", "business-model", "solution"],
    include_team_memories=True
)

context = processor.generate_context(config, "如何实现用户认证功能？")
print(context.to_markdown())
```

#### 3. 使用命令行工具

```bash
# 生成团队上下文
python -m src.commands.team_context_command my_team generate \
    --project-name my_project \
    --mode hybrid \
    --stages requirements,business-model,solution

# 管理团队记忆
python -m src.commands.team_memory_command my_team add \
    --project-name my_project \
    --content "项目的核心架构设计" \
    --tags architecture,design \
    --importance 5
```

## 💡 核心概念

### 记忆类型

1. **声明性记忆 (Declarative)**: 存储事实性知识和概念
2. **程序性记忆 (Procedural)**: 存储操作流程和最佳实践
3. **情景性记忆 (Episodic)**: 存储具体的项目经验和案例

### 上下文模式

1. **记忆模式 (Memory Only)**: 仅使用团队/项目记忆
2. **框架模式 (Framework Only)**: 仅使用七步开发框架
3. **混合模式 (Hybrid)**: 结合记忆和框架生成综合上下文

### 项目级组织

```
teams/
  my_team/
    memory/                 # 团队级记忆（通用知识）
      procedural.md
      declarative.md
      episodic/
    projects/               # 项目级组织
      project_a/
        memory/             # 项目特定记忆
          procedural.md
          declarative.md
          episodic/
        context/            # 项目特定上下文
      project_b/
        memory/
        context/
```

## 🛠️ 七步开发框架

我们的核心创新是**七步结构化开发框架**，它将软件开发过程标准化为7个阶段：

1. **🎯 需求锚定** - 提取需求本质和核心目标
2. **🏗️ 业务模型** - 构建实体关系和数据流模型
3. **💡 解决方案** - 设计高层架构和技术方案
4. **🔧 结构定义** - 定义技术架构和组件关系
5. **📋 任务编排** - 转化为具体可执行任务
6. **🔄 通用任务** - 定义编码规范和通用模式
7. **⚖️ 约束控制** - 明确边界条件和质量标准

每个阶段都有明确的输出格式和质量标准，确保生成的技术方案具有高度的一致性和可执行性。

## 📚 API 文档

### ContextProcessor

主要的上下文处理类：

```python
class ContextProcessor:
    def generate_context(
        self, 
        config: ContextGenerationConfig, 
        user_message: str = None
    ) -> GeneratedContext:
        """生成结构化上下文"""
        
    def _find_relevant_memories_by_message(
        self, 
        memories: List[MemoryEntry], 
        user_message: str
    ) -> List[MemoryEntry]:
        """智能匹配相关记忆"""
```

### DirectoryManager

团队和项目管理：

```python
class DirectoryManager:
    def create_team(self, team_name: str, description: str) -> Path:
        """创建团队"""
        
    def create_project(self, team_name: str, project_name: str, description: str) -> Path:
        """创建项目"""
        
    def list_projects(self, team_name: str) -> List[str]:
        """列出团队项目"""
```

### 配置选项

```python
@dataclass
class ContextGenerationConfig:
    team_name: str                          # 团队名称
    project_name: Optional[str] = None      # 项目名称
    mode: ContextMode = ContextMode.HYBRID  # 生成模式
    include_team_memories: bool = True      # 是否包含团队记忆
    max_memory_items: int = 50              # 最大记忆数量
    memory_importance_threshold: int = 2    # 重要性阈值
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_context_processor.py

# 运行带覆盖率的测试
pytest --cov=src tests/
```

## 🔧 配置

### 环境变量

```bash
# API 配置
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# 系统配置
DEFAULT_MODEL=claude-3-sonnet-20241022
MAX_TOKENS=4096
TEMPERATURE=0.1

# 数据路径
DATA_PATH=./data
LOGS_PATH=./logs
```

### 配置文件示例

```json
{
  "team_config": {
    "default_memory_threshold": 3,
    "max_memory_items": 50,
    "auto_cleanup_days": 90
  },
  "project_config": {
    "memory_isolation": true,
    "inherit_team_memories": true
  },
  "generation_config": {
    "default_mode": "hybrid",
    "default_stages": [
      "requirements",
      "business-model", 
      "solution",
      "structure",
      "tasks",
      "common-tasks",
      "constraints"
    ]
  }
}
```

## 🎨 最佳实践

### 记忆管理

1. **按项目组织**: 将记忆按项目分类，避免无关信息干扰
2. **合理分级**: 使用1-5的重要性评分，重要记忆优先匹配
3. **标签规范**: 使用一致的标签体系，提高检索精度
4. **定期清理**: 删除过时的记忆，保持知识库新鲜

### 上下文生成

1. **精准查询**: 提供具体的用户消息，获得更相关的记忆
2. **模式选择**: 根据场景选择合适的生成模式
3. **阶段定制**: 只包含需要的框架阶段，避免信息过载
4. **迭代优化**: 根据生成效果调整配置参数

### 团队协作

1. **统一规范**: 团队成员遵循相同的记忆和标签规范
2. **知识共享**: 将项目经验及时转化为团队记忆
3. **版本管理**: 使用Git管理记忆文件的版本变更
4. **权限控制**: 合理设置项目访问权限

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 提交代码

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

### 代码规范

- 使用 Black 进行代码格式化
- 使用 isort 整理导入
- 添加类型注解
- 编写单元测试
- 更新文档

### 提交消息规范

```
类型(范围): 描述

详细说明

Fixes #issue_number
```

类型：feat, fix, docs, style, refactor, test, chore

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

- 📖 [文档](./docs/)
- 🐛 [问题报告](../../issues)
- 💬 [讨论区](../../discussions)
- 📧 Email: support@example.com

## 🗺️ 路线图

### v1.0.0 (当前版本)
- ✅ 基础记忆管理
- ✅ 项目级组织
- ✅ 七步框架
- ✅ 智能上下文生成

### v1.1.0 (规划中)
- 🔄 Web UI界面
- 🔄 记忆搜索优化
- 🔄 多语言支持
- 🔄 插件系统

### v2.0.0 (未来版本)
- 🔮 AI驱动的记忆推荐
- 🔮 团队协作实时同步
- 🔮 企业级权限管理
- 🔮 云端部署支持

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

特别感谢：
- Claude AI 提供的智能对话能力
- Anthropic 团队的技术支持
- 开源社区的宝贵反馈

---

**⭐ 如果这个项目对你有帮助，请给我们一个星标！** 