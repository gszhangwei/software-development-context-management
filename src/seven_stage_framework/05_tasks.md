# 任务编排（Tasks）

## 目标
将抽象方案转化为具体可执行的实现任务

## 输出格式
```
## Tasks

### 创建/更新/删除[ComponentType] - [ComponentName]类
1. 职责：[Clear responsibility description]
2. 属性：
   - [attributeName]: [Type] - [Description]
   - [attributeName]: [Type] - [Description with validation rules]
3. 方法：
   - [methodName]([parameters]): [ReturnType]
     - 逻辑：
       - [Step-by-step implementation logic]
       - [Conditional logic and edge cases]
       - [Error handling approach]
4. 注解：
   - [RequiredAnnotations for framework integration]
5. 约束：
   - [Validation rules and business constraints]

### 实现[ServiceType] - [ServiceName]服务
1. 接口定义：[Interface methods and contracts]
2. 核心方法：[methodName]([parameters]): [ReturnType]
   - 输入验证：[Input validation rules]
   - 业务逻辑：[Core business logic steps]
   - 异常处理：[Exception handling strategy]
   - 返回值：[Return value construction]
3. 依赖注入：[Required dependencies]
4. 事务管理：[Transaction boundary definition]

### 配置[ConfigurationType] - [ConfigurationName]
1. 配置项：[Configuration parameters]
2. 默认值：[Default value settings]
3. 环境变量：[Environment-specific settings]
4. 验证规则：[Configuration validation]

### 创建异常处理器 - GlobalExceptionHandler
1. 职责：统一处理全局异常，提供标准化错误响应
2. 异常类型：
   - BusinessException: [Business logic exceptions]
   - ValidationException: [Input validation exceptions]
   - SystemException: [System-level exceptions]
   - RuntimeException: [Unexpected runtime exceptions]
3. 方法：
   - handleBusinessException(BusinessException): ResponseEntity<ErrorResponse>
   - handleValidationException(ValidationException): ResponseEntity<ErrorResponse>
   - handleSystemException(SystemException): ResponseEntity<ErrorResponse>
   - handleGenericException(Exception): ResponseEntity<ErrorResponse>
4. 注解：
   - @RestControllerAdvice
   - @ExceptionHandler for each exception type
5. 响应格式：
   - 统一的错误响应结构（错误码、错误消息、时间戳等）

### 创建业务异常类 - [BusinessExceptionName]
1. 职责：定义特定业务场景的异常类型，提供清晰的错误信息和错误码
2. 继承关系：
   - extends RuntimeException 或 extends BusinessException（如果有基础业务异常类）
3. 属性：
   - errorCode: String - 业务错误码（如：USER_NOT_FOUND, INVALID_OPERATION等）
   - errorMessage: String - 详细错误描述
   - timestamp: LocalDateTime - 异常发生时间
   - context: Map<String, Object> - 异常上下文信息（可选）
4. 构造方法：
   - [ExceptionName](String errorCode, String errorMessage)
   - [ExceptionName](String errorCode, String errorMessage, Throwable cause)
   - [ExceptionName](String errorCode, String errorMessage, Map<String, Object> context)
5. 方法：
   - getErrorCode(): String - 获取错误码
   - getErrorMessage(): String - 获取错误消息
   - getContext(): Map<String, Object> - 获取上下文信息
   - toString(): String - 格式化异常信息
6. 使用场景：
   - [Specific business scenarios where this exception should be thrown]
   - [Validation rules that trigger this exception]
   - [Business logic conditions that warrant this exception]
7. 异常分类：
   - 数据异常：如 DataNotFoundException, DataConflictException
   - 权限异常：如 UnauthorizedException, ForbiddenException
   - 业务规则异常：如 BusinessRuleViolationException, InvalidStateException
   - 外部依赖异常：如 ExternalServiceException, IntegrationException
```

## 构建要点
- **基于前四阶段**：严格基于需求、模型、方案、结构的完整上下文
- **任务分类**：按功能模块或组件类型分组（实体类、服务类、控制器等）
- **实现细节**：包含具体的代码规范、配置要求、业务逻辑
- **执行顺序**：按依赖关系组织任务执行顺序
- **职责单一**：每个任务职责明确且边界清晰
- **可验证性**：每个任务都有明确的完成标准
- **逻辑严谨性**：确保任务编排基于业务模型、解决方案、结构化设计，避免出现逻辑漏洞，保证上下文数据流的连贯性

## 质量标准
- 任务可直接执行
- 覆盖完整实现
- 细节准确具体 