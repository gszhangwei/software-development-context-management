# 记忆项目匹配度评分算法

一个基于关键词匹配和语义分析的智能评分系统，用于快速找到最符合用户需求的记忆项目。

## 🚀 功能特性

### 核心功能
- **智能评分**: 基于多维度关键词匹配计算精准的匹配度分数
- **动态权重**: 根据用户需求自动调整各维度的重要性权重
- **语义分析**: 不仅匹配关键词，还考虑上下文和结构信息
- **置信度评估**: 为每个评分结果提供可信度指标

### 高级特性
- **用户反馈学习**: 基于用户反馈自动优化评分算法
- **专家标注支持**: 支持专家快速标注和权重调整
- **矩阵版本管理**: 完整的变更历史和回滚机制
- **A/B测试框架**: 安全的算法更新和效果验证

## 📦 安装依赖

```bash
pip install numpy
```

## 🎯 快速开始

### 基本使用

```python
from memory_scoring_engine import MemoryScoringEngine, MemoryItem

# 创建评分引擎
engine = MemoryScoringEngine()

# 准备记忆项目数据
memory_items = [
    MemoryItem(
        id="mem_001",
        title="API设计指南",
        content="详细的RESTful API设计规范和最佳实践...",
        tags=["api", "design", "rest"],
        project="backend",
        importance=4
    )
]

# 用户需求
user_requirement = "需要设计新的API接口，支持用户认证和数据查询"

# 执行评分
results = engine.score_memory_items(user_requirement, memory_items)

# 查看结果
for result in results:
    print(f"标题: {result.title}")
    print(f"评分: {result.total_score:.2f}")
    print(f"置信度: {result.confidence:.1f}%")
    print(f"匹配关键词: {', '.join(result.matched_keywords)}")
```

### 运行演示

```bash
python tools/scoring_example.py
```

## 🔧 配置说明

### 评分维度

算法默认使用5个评分维度：

| 维度 | 权重 | 说明 |
|------|------|------|
| `api_enhancement` | 25% | API增强和改进相关 |
| `entity_support` | 25% | 实体和模型支持 |
| `data_model` | 20% | 数据模型设计 |
| `validation` | 15% | 验证和检查机制 |
| `mixed_type` | 15% | 混合类型处理 |

### 关键词矩阵

每个维度包含相关的关键词和权重：

```python
{
    'api_enhancement': {
        'controller': 5,
        'api': 4,
        'endpoint': 4,
        'unified': 6,
        'microservice': 6
    },
    'entity_support': {
        'Solution': 10,
        'Rule': 6,
        'Workflow': 6,
        'SolutionService': 8
    }
    # ... 其他维度
}
```

## 📊 评分算法详解

### 评分流程

1. **需求分析**: 从用户需求中提取关键要素
2. **权重计算**: 根据需求特点动态调整维度权重
3. **内容匹配**: 对每个记忆项目进行多维度语义匹配
4. **分数合成**: 加权计算最终评分和置信度

### 评分公式

```
总分 = Σ(维度得分 × 维度权重)
置信度 = f(覆盖度, 内容长度, 关键词数量)
维度得分 = min(基础分数 + 上下文奖励 + 结构奖励 + 密度奖励, 最大分数)
```

### 奖励机制

- **上下文奖励**: 关键词在一定距离内共现
- **结构奖励**: 包含图表、代码块等结构化内容
- **密度奖励**: 关键词密度合理的内容

## 🔄 更新机制

### 触发条件

算法支持以下更新触发方式：

1. **用户反馈触发**: 负面反馈比例超过阈值
2. **性能监控触发**: 准确率下降超过阈值
3. **定时触发**: 定期检查和更新
4. **手动触发**: 专家主动发起更新

### 更新策略

- **渐进式更新**: 使用梯度下降方式调整权重
- **专家知识融合**: 整合多个专家的标注意见
- **自动学习**: 从使用日志中学习关键词表现

### 示例：添加用户反馈

```python
# 添加用户反馈
engine.add_user_feedback(
    memory_id="mem_001",
    query="需要API设计指南",
    rating=5,  # 1-5分
    matched_keywords=["api", "design"],
    comment="非常有用的资源"
)

# 基于反馈更新矩阵
update_manager = MatrixUpdateManager(engine)
changes = update_manager.apply_feedback_updates(engine.feedback_history)
```

### 示例：专家标注

```python
# 专家标注
annotation = ExpertAnnotation(
    expert_id="expert_001",
    keyword="microservice",
    dimension="api_enhancement",
    suggested_weight=8.0,
    confidence=0.9,
    reasoning="微服务在现代架构中很重要"
)

update_manager.add_expert_annotation(annotation)
```

## 💾 数据管理

### 保存和加载矩阵

```python
# 保存矩阵配置
engine.save_matrix("my_matrix.json")

# 加载矩阵配置
engine.load_matrix("my_matrix.json")
```

### 统计信息

```python
# 获取评分统计
stats = engine.get_scoring_statistics()
print(f"评分会话数: {stats['total_scoring_sessions']}")
print(f"平均评分: {stats['average_user_rating']}")

# 获取变更统计
summary = update_manager.get_change_summary(days=7)
print(f"7天内变更数: {summary['total_changes']}")
```

## 🎨 自定义配置

### 添加新关键词

```python
# 添加安全相关关键词到验证维度
security_keywords = {
    'authentication': 8,
    'authorization': 8,
    'encryption': 7,
    'oauth': 6
}

for keyword, weight in security_keywords.items():
    engine.keyword_matrix.add_keyword('validation', keyword, weight)
```

### 调整权重策略

```python
# 创建自定义权重计算器
class CustomWeightCalculator(WeightCalculator):
    def calculate_weights(self, requirements):
        weights = super().calculate_weights(requirements)
        
        # 如果涉及安全需求，增加验证维度权重
        if any('auth' in req.lower() for req in requirements.functionalities):
            weights['validation'] += 10
            weights['api_enhancement'] -= 5
            weights['data_model'] -= 5
        
        return self._normalize_weights(weights)

# 使用自定义计算器
engine.weight_calculator = CustomWeightCalculator()
```

## 📈 性能优化

### 批量处理

```python
# 批量评分多个需求
requirements = [
    "API设计规范",
    "数据库优化",
    "用户认证系统"
]

all_results = []
for req in requirements:
    results = engine.score_memory_items(req, memory_items)
    all_results.extend(results)
```

### 缓存策略

```python
# 实现结果缓存
import hashlib
from functools import lru_cache

class CachedScoringEngine(MemoryScoringEngine):
    @lru_cache(maxsize=100)
    def _cached_score(self, req_hash, memory_hash):
        # 实现缓存逻辑
        pass
```

## 🔍 调试和诊断

### 详细分数分解

```python
# 查看详细评分过程
result = results[0]
for dimension, scores in result.score_breakdown.items():
    print(f"{dimension}:")
    print(f"  原始分数: {scores['raw_score']}/{scores['max_score']}")
    print(f"  权重: {scores['weight']}")
    print(f"  加权分数: {scores['weighted_score']}")
    print(f"  匹配关键词: {scores['matched_keywords']}")
```

### 性能监控

```python
# 监控评分性能
import time

start_time = time.time()
results = engine.score_memory_items(requirement, memory_items)
duration = time.time() - start_time

print(f"评分耗时: {duration:.3f}秒")
print(f"平均每项: {duration/len(memory_items):.3f}秒")
```

## 🚨 常见问题

### Q: 评分结果不符合预期怎么办？

A: 可以通过以下方式优化：
1. 检查关键词矩阵是否包含相关术语
2. 调整维度权重配置
3. 添加用户反馈来改进算法
4. 使用专家标注快速调整

### Q: 如何处理新的业务领域？

A: 
1. 添加领域相关的关键词和维度
2. 收集该领域的标注数据
3. 使用A/B测试验证效果
4. 逐步优化算法参数

### Q: 如何确保算法的稳定性？

A:
1. 使用版本管理跟踪所有变更
2. 实施回滚机制应对问题
3. 通过A/B测试验证更新效果
4. 设置性能监控和告警

## 📄 许可证

[在此添加许可证信息]

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## �� 联系方式

[在此添加联系方式] 