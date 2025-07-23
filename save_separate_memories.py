#!/usr/bin/env python3
"""
将工作流设计的各个部分分别保存为独立的记忆条目
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.commands.team_memory_command import TeamMemoryCommand

def main():
    """将工作流设计的各个部分分别保存为独立记忆条目"""
    
    # 初始化组件
    memory_command = TeamMemoryCommand(root_path="test_data")
    
    # 定义各个记忆条目
    memory_entries = [
        {
            "title": "工作流业务模型关系设计",
            "content": """# 工作流业务模型关系设计

## 核心实体定义

- **Workflow**: 工作流核心实体，包含 id、name、description、orderedSteps、owner、时间戳等字段
- **WorkflowRequest**: 创建工作流的请求对象，包含 name、description、orderedSteps、owner
- **WorkflowResponse**: 工作流响应对象，提供完整的工作流信息给前端
- **WorkflowPO**: 持久化对象，用于数据库存储

## 查询和分页对象

- **WorkflowQueryParams**: 查询参数对象，支持 name、description、owner、分页参数、排序参数
- **PagedWorkflowResponse**: 分页响应包装，包含 content、分页元数据(totalPages、totalElements等)

## 更新检查相关

- **WorkflowUpdateCheckRequest**: 更新检查请求，包含 workflowId 和 rulesHashes 列表
- **RuleHashInfo**: 规则哈希信息，包含 ruleId 和 contentHash
- **WorkflowUpdateCheckResponse**: 更新检查响应，标识步骤和规则的更新状态

## 关系映射

- WorkflowRequest -> Workflow (创建转换)
- Workflow -> WorkflowResponse (响应映射)  
- Workflow -> WorkflowPO (持久化转换)
- WorkflowPO -> Workflow (加载转换)
- Workflow -> Rule (通过 orderedSteps 关联)""",
            "tags": "data-model,entity-design,workflow,architecture",
            "importance": 5
        },
        {
            "title": "创建工作流完整流程设计",
            "content": """# 创建工作流完整流程设计

## 核心流程步骤

1. **请求接收**: POST /api/v1/workflows 接收 WorkflowRequest
2. **用户验证**: 通过 UserContext.getCurrentUserEmail() 获取当前用户
3. **请求丰富**: enrichWithUserEmail(request) 补充用户信息
4. **规则验证**: 
   - 调用 RuleRepository.findAllByIdIn(orderedSteps)
   - validateIfPromptExists() 验证规则存在性
5. **重复检查**: 
   - findByNameAndOwner(name, owner) 检查是否存在同名工作流
6. **数据处理**:
   - 如果不存在: Workflow.fromRequest(request) 创建新实体
   - 调用 WorkflowRepository.save(workflow) 持久化
   - 如果存在: 返回现有工作流
7. **响应生成**: WorkflowResponse.of(workflow) 转换响应格式

## 技术要点

- 分层调用: Controller -> Service -> Repository -> DAO -> Database
- 事务处理: 确保数据一致性
- 异常处理: 统一错误响应格式
- 性能考虑: 批量规则查询优化""",
            "tags": "create-workflow,api-flow,business-logic,backend",
            "importance": 5
        },
        {
            "title": "分页查询工作流流程设计", 
            "content": """# 分页查询工作流流程设计

## 查询流程步骤

1. **参数解析**: GET /api/v1/workflows 解析查询参数
2. **参数构建**: 构建 WorkflowQueryParams 对象
3. **分页信息**: WorkflowCriteriaBuilder.buildPageableInfo() 构建 Pageable
4. **动态查询**: 
   - buildSpecification(queryParams) 构建动态查询条件
   - 支持 name、description、owner 等多字段模糊查询
5. **数据库查询**: 
   - findAll(specification, pageable) 执行分页查询
   - 生成优化的 SQL: SELECT ... WHERE ... LIMIT ... OFFSET ...
6. **结果转换**: 
   - Page<WorkflowPO> -> Page<Workflow> 实体转换
   - PagedWorkflowResponse.of(workflowPage) 响应格式化

## 技术特性

- 动态查询条件构建 (Specification Pattern)
- 数据库分页优化
- 实体转换层次清晰
- 支持多种排序方式
- 查询性能监控""",
            "tags": "pagination,search,query-optimization,database",
            "importance": 4
        },
        {
            "title": "工作流更新检查机制设计",
            "content": """# 工作流更新检查机制设计

## 更新检查流程

1. **请求处理**: POST /api/v1/workflows/check-updates 接收 WorkflowUpdateCheckRequest
2. **工作流获取**: findWorkflowById(workflowId) 获取当前工作流状态
3. **步骤序列检查**: 
   - checkOrderedStepsUpdated(workflow, request)
   - 比较 request.rulesHashes.ruleIds 与 workflow.orderedSteps 的序列
4. **规则内容检查**:
   - 如果 rulesHashes 非空: findAllByIdIn(ruleIds) 获取当前规则
   - checkRulesUpdated(request) 比较 contentHash
   - 识别不存在的规则和内容变更的规则
5. **响应构建**: WorkflowUpdateCheckResponse.of() 生成检查结果

## 核心检查逻辑

- **步骤序列更新**: 检查 orderedSteps 数组的顺序和内容变化
- **规则内容更新**: 通过 contentHash 比较检测规则内容变更
- **增量检测**: 只返回实际发生变更的部分
- **性能优化**: 批量查询规则，避免 N+1 查询问题

## 应用场景

- 工作流版本控制
- 缓存失效判断
- 客户端同步检查
- 审计日志记录""",
            "tags": "update-check,version-control,cache-invalidation,incremental",
            "importance": 4
        },
        {
            "title": "批量查询工作流优化设计",
            "content": """# 批量查询工作流优化设计

## 批量查询流程

1. **参数验证**: 
   - GET /api/v1/workflows/ids?ids=id1,id2,id3
   - 验证 ids 参数非空
   - 限制 ids.size() <= 100 (防止查询过大)
2. **批量查询**: 
   - getWorkflowsByIds(ids) 服务层处理
   - findAllByIdIn(ids) 数据层批量查询
   - 生成优化 SQL: SELECT ... WHERE id IN (...)
3. **结果处理**:
   - List<WorkflowPO> -> List<Workflow> 实体转换
   - WorkflowResponse.of(workflows) 批量响应转换

## 性能优化策略

- **参数限制**: 最多支持 100 个 ID，防止查询过载
- **批量查询**: 使用 IN 子句避免多次单独查询
- **内存优化**: 流式处理大结果集
- **缓存策略**: 常用工作流 ID 缓存
- **索引优化**: 主键索引保证 O(log n) 查询复杂度

## 错误处理

- 参数验证失败: 400 Bad Request
- ID 不存在: 静默忽略，返回存在的记录
- 查询异常: 500 Internal Server Error

## 使用场景

- 批量操作工作流
- 关联数据预加载
- 报表数据获取
- 移动端数据同步""",
            "tags": "batch-query,performance-optimization,api-design,scalability", 
            "importance": 4
        }
    ]
    
    print("🚀 开始分别保存工作流设计的各个部分...")
    
    success_count = 0
    
    for i, entry in enumerate(memory_entries, 1):
        print(f"\n📝 保存第 {i}/{len(memory_entries)} 个记忆条目: {entry['title']}")
        
        result = memory_command.execute(
            team_name="engineering_team",
            action="save", 
            content=entry["content"],
            tags=entry["tags"],
            project="workflow-management-system",
            memory_type="procedural",
            importance=entry["importance"]
        )
        
        if result.success:
            print(f"✅ 成功保存: {entry['title']}")
            if result.data:
                print(f"   🆔 记忆ID: {result.data.get('entry_id', 'N/A')}")
            success_count += 1
        else:
            print(f"❌ 保存失败: {entry['title']}")
            print(f"   错误信息: {result.message}")
    
    print(f"\n🎉 批量保存完成!")
    print(f"✅ 成功保存: {success_count}/{len(memory_entries)} 个记忆条目")
    
    # 验证保存结果
    print(f"\n🔍 验证保存结果...")
    list_result = memory_command.execute(
        team_name="engineering_team",
        action="list",
        memory_type="procedural", 
        project="workflow-management-system",
        limit=10
    )
    
    if list_result.success:
        print(f"✅ 验证成功! 总共找到 {list_result.data.get('count', 0)} 条相关记忆")
    else:
        print("⚠️ 验证失败，但内容可能已保存")
    
    return success_count == len(memory_entries)

if __name__ == "__main__":
    main() 