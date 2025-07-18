# 通用任务（Common Tasks）

## 目标
定义统一的编码规范和通用实现模式

## 输出格式
```
## Common Tasks
1. 注解规范：[Specific annotation requirements for different component types]
2. 依赖注入：[Dependency injection patterns and best practices]  
3. 异常处理：[Unified exception handling approach via GlobalExceptionHandler]
   - 自定义异常类型定义和继承关系
   - 业务异常类创建标准：
     * 继承RuntimeException或自定义BusinessException基类
     * 必须包含errorCode（业务错误码）和errorMessage（错误描述）
     * 提供多种构造方法支持不同场景
     * 按业务领域分类（数据异常、权限异常、业务规则异常、外部依赖异常）
   - 统一错误响应格式（ErrorResponse DTO）
   - 异常处理器方法的标准实现模式
   - 日志记录和异常跟踪机制
4. 数据验证：[Common validation patterns and rules]
5. 日志记录：[Logging standards and patterns]
6. 文档规范：[Documentation and comment standards]
```

## 构建要点
- **标准化**：定义统一的编码规范和配置模式
- **复用性**：提取可复用的通用实现模式
- **一致性**：确保所有组件遵循相同的标准
- **质量保障**：内置验证和校验机制
- **最佳实践**：体现行业最佳实践和经验总结

## 质量标准
- 规范明确具体
- 易于执行检查
- 体现最佳实践 