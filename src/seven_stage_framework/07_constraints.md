# 约束控制（Constraints）

## 目标
定义明确的边界条件和质量标准

## 输出格式
```
## Constraints
1. 功能约束：[Functional requirements and limitations with specific criteria]
2. 性能约束：[Performance requirements with measurable metrics]
3. 安全约束：[Security requirements and compliance standards]
4. 集成约束：[Integration limitations and compatibility requirements]
5. 业务规则约束：[Business rule validation with specific conditions]
6. 异常处理约束：[Exception handling standards and requirements]
   - 业务异常必须包含明确的错误码和错误消息
   - 异常类型必须按业务领域分类和命名
   - 异常信息不得暴露敏感的系统内部信息
   - 所有业务异常必须被GlobalExceptionHandler统一处理
7. 技术约束：[Technical implementation restrictions and standards]
8. 数据约束：[Data validation rules and format requirements]
9. API约束：[API design standards and interface contracts]
```

## 构建要点
- **边界明确**：清晰定义可以做什么和不能做什么
- **可验证性**：约束条件应该可以验证
- **完整性**：覆盖功能、性能、安全、集成等各个方面
- **实用性**：约束应该有助于提高代码质量和系统稳定性
- **量化标准**：尽可能提供可量化的标准和指标

## 质量标准
- 约束条件明确
- 可验证
- 覆盖面完整 