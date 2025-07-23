# 🚀 自学习记忆评分引擎 - 快速开始

## 📦 模块概览

`src/scoring_self_evolution` 模块提供了一个智能的、自学习的记忆项目评分系统，具备以下核心能力：

- 🧠 **自动学习**: 根据使用情况自动调整和优化
- 🔍 **关键词发现**: 自动识别和添加新的技术关键词
- 📊 **智能评分**: 基于多维度语义匹配的精准评分
- 📈 **持续改进**: 用得越多，越准确

## ⚡ 5分钟快速上手

### 1. 基本使用

```python
# 导入核心模块
from src.scoring_self_evolution import create_scoring_engine, MemoryItem

# 创建评分引擎
engine = create_scoring_engine()

# 准备记忆项目数据
memory_items = [
    MemoryItem(
        id="mem_001",
        title="API设计文档",
        content="RESTful API设计，包含CRUD操作，使用DTO模式...",
        tags=["api", "rest", "dto"],
        project="web-service",
        importance=5
    )
]

# 用户需求
user_requirement = "需要设计一个RESTful API，支持用户管理"

# 执行评分
results = engine.score_memory_items(user_requirement, memory_items)

# 查看结果
for result in results:
    print(f"匹配: {result.title}")
    print(f"评分: {result.total_score:.2f}")
    print(f"置信度: {result.confidence:.1f}%")
```

### 2. 添加用户反馈（学习）

```python
# 基于评分结果添加用户反馈
if results:
    best_match = results[0]
    engine.add_user_feedback(
        memory_id=best_match.memory_id,
        query=user_requirement,
        rating=5,  # 1-5星评分
        matched_keywords=best_match.matched_keywords[:3],
        comment="完美匹配我的需求"
    )
```

### 3. 保存和加载学习结果

```python
# 保存学习后的矩阵
engine.save_matrix("my_learned_matrix.json")

# 下次使用时加载学习结果
learned_engine = create_scoring_engine("my_learned_matrix.json")
```

## 🎛️ 高级配置

### 自定义学习参数

```python
engine = create_scoring_engine(
    learning_rate=0.03,                    # 学习速度
    stabilization_threshold=50,            # 稳定化阈值
    keyword_discovery_threshold=0.7,       # 关键词发现阈值
    auto_learning_enabled=True,            # 启用自动学习
    keyword_discovery_enabled=True,        # 启用关键词发现
    stabilization_enabled=True             # 启用系统稳定化
)
```

### 动态调整配置

```python
# 运行时调整学习参数
engine.keyword_matrix.learning_rate = 0.02
engine.keyword_matrix.weight_decay = 0.99

# 控制学习功能开关
engine.auto_learning_enabled = False  # 暂停自动学习
```

## 📊 学习监控

### 获取学习统计

```python
stats = engine.get_learning_statistics()
print(f"总关键词数: {stats['total_keywords']}")
print(f"使用次数: {stats['total_keyword_usage']}")
print(f"发现新词: {stats['discovered_keywords']}")
print(f"稳定关键词: {stats['stable_keywords']}")
```

### 查看演化报告

```python
evolution = engine.get_keyword_evolution_report()

# 表现最好的关键词
for kw in evolution['top_performing_keywords'][:5]:
    print(f"{kw['keyword']}: 贡献度={kw['avg_contribution']:.3f}")

# 新发现的关键词
for kw in evolution['newly_discovered_keywords'][:5]:
    print(f"{kw['keyword']}: 置信度={kw['confidence']:.3f}")
```

## 📈 可视化分析

```python
from src.scoring_self_evolution import create_visualizer

# 创建可视化工具
viz = create_visualizer("my_learned_matrix.json")

# 生成详细报告
viz.save_report("learning_analysis.md")

# 检查学习数据
if viz.data:
    print("学习数据加载成功")
    metadata = viz.data.get('metadata', {})
    print(f"总使用次数: {metadata.get('total_usage_count', 0)}")
```

## 🏗️ 实际应用场景

### 1. 技术文档检索

```python
# 针对技术文档优化的配置
tech_engine = create_scoring_engine(
    keyword_discovery_threshold=0.8,  # 高精度关键词发现
    learning_rate=0.02                # 稳定学习
)

# 技术查询示例
tech_query = "实现微服务架构的API网关设计"
tech_results = tech_engine.score_memory_items(tech_query, tech_docs)
```

### 2. 代码片段匹配

```python
# 代码相关的评分引擎
code_engine = create_scoring_engine(
    stabilization_threshold=30,       # 快速稳定
    auto_learning_enabled=True
)

# 代码查询示例
code_query = "实现JWT认证的中间件"
code_results = code_engine.score_memory_items(code_query, code_snippets)
```

### 3. 需求分析匹配

```python
# 需求分析特化配置
req_engine = create_scoring_engine(
    keyword_discovery_enabled=True,   # 主动发现新需求关键词
    learning_rate=0.05                # 快速适应
)

# 需求查询示例
req_query = "用户权限管理系统设计"
req_results = req_engine.score_memory_items(req_query, requirements_docs)
```

## 🔧 故障排除

### 常见问题

1. **导入错误**
   ```python
   # 确保在项目根目录运行
   from src.scoring_self_evolution import create_scoring_engine
   ```

2. **学习数据丢失**
   ```python
   # 定期保存学习结果
   engine.save_matrix("backup_matrix.json")
   ```

3. **性能问题**
   ```python
   # 调整学习参数
   engine.keyword_matrix.learning_rate = 0.01  # 降低学习率
   ```

### 调试技巧

```python
# 查看内部状态
print(f"矩阵版本: {engine.keyword_matrix.version}")
print(f"关键词统计: {len(engine.keyword_matrix.keyword_stats)}")

# 检查配置
stats = engine.get_learning_statistics()
print(f"学习状态: {stats['learning_enabled']}")
```

## 📚 进阶使用

### 批量评分优化

```python
# 处理大量记忆项目时的优化
results = []
for batch in memory_batches:
    batch_results = engine.score_memory_items(query, batch)
    results.extend(batch_results)
    
    # 每批次保存学习进度
    engine.save_matrix("progress_backup.json")
```

### 多引擎协作

```python
# 创建专门的引擎用于不同场景
api_engine = create_scoring_engine("api_learned_matrix.json")
doc_engine = create_scoring_engine("doc_learned_matrix.json")

# 根据查询类型选择引擎
def smart_score(query, memories):
    if "api" in query.lower():
        return api_engine.score_memory_items(query, memories)
    else:
        return doc_engine.score_memory_items(query, memories)
```

## 🎯 最佳实践

1. **定期保存**: 每100次评分后保存矩阵
2. **质量反馈**: 及时提供准确的用户评分
3. **参数调优**: 根据实际效果调整学习参数
4. **数据备份**: 定期备份重要的学习数据
5. **监控指标**: 关注学习统计和演化报告

---

🎉 **恭喜！** 你已经掌握了自学习记忆评分引擎的基本使用方法。随着持续使用，系统会变得越来越智能和准确！

📖 更多详细信息请查看 [README.md](README.md) 和 [自学习功能说明](self_learning_summary.md)。 