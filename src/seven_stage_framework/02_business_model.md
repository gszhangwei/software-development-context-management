# 业务模型（Business Model）

## 目标
构建清晰的业务实体关系模型，为后续设计提供概念基础

## 输出格式
```
## Business Model
```mermaid
classDiagram
direction TB

class [CoreEntity] {
    +[AttributeType] [attributeName]
    +[AttributeType] [attributeName]
    +[Method]()
}

class [RelatedEntity] {
    +[AttributeType] [attributeName]
    +[Method]()
}

class [RequestDTO] {
    +[AttributeType] [attributeName]
    +[ValidationRule]
}

class [ResponseDTO] {
    +[AttributeType] [attributeName]
    +[StaticMethod]()
}

[CoreEntity] "[cardinality]" -- "[cardinality]" [RelatedEntity] : [relationshipDesc]
[RequestDTO] --> [CoreEntity] : creates
[CoreEntity] --> [ResponseDTO] : maps to
```

## 构建要点
- **实体识别**：识别核心业务实体、支撑实体、DTO对象
- **属性建模**：为每个实体定义关键属性，使用"类型+名称"格式
- **关系建模**：明确实体间的关系类型（1:1, 1:N, N:M）和业务语义
- **接口设计**：包含关键的方法和静态工厂方法
- **数据流向**：体现请求->处理->响应的完整数据流
- **一致性保障**：确保模型能被AI准确理解和实现
- **简洁 > 功能丰富**：避免过度工程化，保持系统可理解性

## 质量标准
- 关注当前任务流程
- 实体关系清晰准确
- 支持后续技术实现 