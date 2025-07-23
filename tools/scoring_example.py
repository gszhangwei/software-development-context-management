#!/usr/bin/env python3
"""
记忆项目匹配度评分算法使用示例

展示如何使用 MemoryScoringEngine 进行记忆项目评分和管理
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加工具目录到路径
sys.path.append(str(Path(__file__).parent))

from memory_scoring_engine import (
    MemoryScoringEngine, MemoryItem, UserFeedback, ExpertAnnotation,
    MatrixUpdateManager, ChangeType, UpdateSource
)


def create_sample_memory_items():
    """创建示例记忆项目"""
    return [
        MemoryItem(
            id="workflow_001",
            title="统一Controller与Service选择器架构设计",
            content="""
            # 统一控制器与服务选择器架构设计
            
            ## 核心设计模式
            
            ### 1. 统一控制器模式
            - **ID前缀约定**: "r_"表示Rule，"s_"表示Solution
            - **枚举类型设计**: PromptType包含idPrefix和displayName属性
            - **集中式ID生成**: IdGeneratorService负责ID生成和类型推断
            - **服务路由**: ServiceSelector根据类型路由请求到对应服务
            - **泛型服务接口**: GenericPromptService提供统一的CRUD操作
            - **统一DTO**: UnifiedPromptDTO包含完整的类型信息
            
            ### 2. 服务选择器模式
            - **类型映射**: 维护PromptType到服务实现的映射关系
            - **多种查找方式**: 支持单个服务查找、基于ID的服务查找和批量操作
            - **依赖注入管理**: 自动注入所有GenericPromptService实现
            - **异常处理**: 优雅处理无效ID和类型的异常情况
            - **批量操作分组**: 根据ID前缀进行高效的批量操作分组
            
            ### 3. ID前缀约定策略
            - **格式规范**: 有意义的短前缀 + UUID格式
            - **服务层集中管理**: 只在Service层生成ID，Repository层不得覆盖
            - **混合ID支持**: API端点支持处理混合类型的ID列表
            - **高效分组**: 通过ID前缀实现批量操作的高效分组处理
            
            ### 4. 统一DTO模式
            - **基础DTO类**: UnifiedPromptDTO包含所有通用字段和类型信息
            - **工厂方法**: 支持从实体转换、类型推断等多种创建方式
            - **向后兼容**: 支持现有API的平滑迁移
            - **类型元数据**: 所有响应中包含完整的类型信息，便于客户端处理
            """,
            tags=["architecture", "unified-controller", "service-selector", "id-prefix", "dto-pattern"],
            project="workflow-management-system",
            importance=5
        ),
        
        MemoryItem(
            id="workflow_002",
            title="创建工作流时序图流程设计",
            content="""
            # 创建工作流时序图流程设计
            
            ## 完整创建工作流时序图
            
            1. **用户验证**: 通过UserContext获取当前用户邮箱
            2. **请求丰富**: enrichWithUserEmail补充用户信息到请求中
            3. **规则验证**: 批量查询orderedSteps中的规则，确保存在性
            4. **重复检查**: 按name+owner查询，避免重复创建工作流
            5. **条件处理**: 不存在则创建新工作流，存在则返回现有工作流
            6. **数据转换**: 实体层面的转换确保数据一致性
            
            ## 关键流程要点
            - Controller接收POST请求
            - Service层处理业务逻辑
            - Repository层数据持久化
            - 完整的错误处理机制
            """,
            tags=["create-workflow", "api-flow", "business-logic", "sequence-diagram"],
            project="workflow-management-system",
            importance=4
        ),
        
        MemoryItem(
            id="api_003",
            title="RESTful API设计规范",
            content="""
            # RESTful API设计规范
            
            ## 基本原则
            - 使用HTTP动词表示操作
            - 资源导向的URL设计
            - 统一的响应格式
            - 适当的状态码使用
            
            ## 端点设计
            - GET /api/v1/resources - 获取资源列表
            - POST /api/v1/resources - 创建新资源
            - PUT /api/v1/resources/{id} - 更新资源
            - DELETE /api/v1/resources/{id} - 删除资源
            
            ## 数据传输
            - 请求体使用JSON格式
            - 响应体包含数据和元信息
            - 错误响应统一格式
            """,
            tags=["api-design", "rest", "http", "json"],
            project="general",
            importance=3
        ),
        
        MemoryItem(
            id="data_004", 
            title="数据库设计最佳实践",
            content="""
            # 数据库设计最佳实践
            
            ## 表结构设计
            - 主键设计原则
            - 外键约束管理
            - 索引优化策略
            - 数据类型选择
            
            ## 性能优化
            - 查询优化技巧
            - 索引使用策略
            - 分页查询实现
            - 批量操作优化
            
            ## 数据一致性
            - 事务管理
            - 并发控制
            - 数据完整性约束
            """,
            tags=["database", "performance", "design", "optimization"],
            project="general",
            importance=3
        )
    ]


def demo_basic_scoring():
    """演示基本评分功能"""
    print("=== 基本评分功能演示 ===\n")
    
    # 创建评分引擎
    engine = MemoryScoringEngine()
    
    # 准备测试数据
    memory_items = create_sample_memory_items()
    
    # 用户需求
    user_requirement = """
    增强工作流创建API，支持将Solution作为步骤。
    需要更新数据模型支持Solution引用，验证Solution ID的存在性和有效性，
    支持混合步骤类型（Rule/Prompt和Solution），确保数据持久化正确。
    API应该支持批量操作和统一的DTO设计。
    """
    
    # 执行评分
    results = engine.score_memory_items(user_requirement, memory_items)
    
    # 输出结果
    print(f"用户需求: {user_requirement}\n")
    print("评分结果:")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title}")
        print(f"   总分: {result.total_score:.2f}/100")
        print(f"   置信度: {result.confidence:.1f}%")
        print(f"   匹配关键词: {', '.join(result.matched_keywords[:8])}")
        print(f"   关键优势:")
        for strength in result.key_strengths:
            print(f"     • {strength}")
        print()
        
        # 显示详细分数分解
        if i == 1:  # 只显示第一个结果的详细分解
            print("   详细分数分解:")
            for dimension, scores in result.score_breakdown.items():
                print(f"     {dimension}: {scores['weighted_score']:.2f}/{scores['weight']:.1f} "
                      f"(原始分: {scores['raw_score']}/{scores['max_score']})")
            print()
    
    return engine


def demo_feedback_system():
    """演示反馈系统"""
    print("=== 反馈系统演示 ===\n")
    
    engine = demo_basic_scoring()
    
    # 添加用户反馈
    feedbacks = [
        ("workflow_001", 5, ["Solution", "unified", "service"], "完全符合需求，架构设计很完整"),
        ("workflow_002", 3, ["create", "workflow", "api"], "部分相关，但缺少Solution支持"),
        ("api_003", 2, ["api", "design"], "太通用，不够具体"),
        ("data_004", 1, ["database"], "与需求不相关")
    ]
    
    user_requirement = """
    增强工作流创建API，支持将Solution作为步骤。
    需要更新数据模型支持Solution引用，验证Solution ID的存在性和有效性。
    """
    
    print("添加用户反馈:")
    for memory_id, rating, keywords, comment in feedbacks:
        engine.add_user_feedback(memory_id, user_requirement, rating, keywords, comment)
        print(f"  {memory_id}: {rating}星 - {comment}")
    
    # 显示统计信息
    stats = engine.get_scoring_statistics()
    print(f"\n反馈统计:")
    print(f"  反馈数量: {stats['feedback_count']}")
    print(f"  平均评分: {stats['average_user_rating']:.2f}")
    print(f"  评分会话数: {stats['total_scoring_sessions']}")
    
    return engine


def demo_matrix_updates():
    """演示矩阵更新功能"""
    print("\n=== 矩阵更新功能演示 ===\n")
    
    engine = demo_feedback_system()
    
    # 创建更新管理器
    update_manager = MatrixUpdateManager(engine)
    
    # 检查更新触发器
    triggers = update_manager.check_update_triggers()
    print("更新触发器状态:")
    if triggers:
        for trigger in triggers:
            print(f"  {trigger['name']}: {trigger['urgency']} - {trigger['reason']}")
    else:
        print("  暂无触发条件满足")
    
    # 添加专家标注示例
    expert_annotation = ExpertAnnotation(
        expert_id="expert_001",
        keyword="microservice",
        dimension="api_enhancement", 
        suggested_weight=7.0,
        confidence=0.9,
        reasoning="微服务架构在现代API设计中越来越重要"
    )
    
    success = update_manager.add_expert_annotation(expert_annotation)
    print(f"\n专家标注添加: {'成功' if success else '失败'}")
    
    # 基于反馈应用更新
    changes = update_manager.apply_feedback_updates(engine.feedback_history)
    print(f"基于反馈的更新数量: {len(changes)}")
    
    if changes:
        print("具体变更:")
        for change in changes[:3]:  # 只显示前3个变更
            print(f"  {change.dimension}.{change.keyword}: "
                  f"{change.old_value:.2f} → {change.new_value:.2f} "
                  f"(置信度: {change.confidence:.2f})")
    
    # 获取变更摘要
    summary = update_manager.get_change_summary(days=7)
    print(f"\n7天内变更摘要:")
    print(f"  总变更数: {summary['total_changes']}")
    print(f"  平均置信度: {summary['avg_confidence']:.2f}")
    print(f"  变更类型: {summary['change_types']}")


def demo_advanced_features():
    """演示高级功能"""
    print("\n=== 高级功能演示 ===\n")
    
    engine = MemoryScoringEngine()
    
    # 测试不同类型的需求
    requirements = [
        "创建新的微服务API",
        "数据库性能优化", 
        "实现用户认证系统",
        "设计工作流管理界面"
    ]
    
    memory_items = create_sample_memory_items()
    
    print("多需求对比分析:")
    print("-" * 60)
    
    for req in requirements:
        results = engine.score_memory_items(req, memory_items)
        top_result = results[0]
        
        print(f"需求: {req}")
        print(f"  最佳匹配: {top_result.title}")
        print(f"  得分: {top_result.total_score:.2f}")
        print(f"  置信度: {top_result.confidence:.1f}%")
        print()
    
    # 保存和加载矩阵
    matrix_file = "demo_matrix.json"
    engine.save_matrix(matrix_file)
    print(f"矩阵已保存到: {matrix_file}")
    
    # 创建新引擎并加载矩阵
    new_engine = MemoryScoringEngine()
    new_engine.load_matrix(matrix_file)
    print("矩阵加载成功")
    
    # 清理示例文件
    Path(matrix_file).unlink(missing_ok=True)
    print("示例文件已清理")


def demo_custom_matrix():
    """演示自定义矩阵配置"""
    print("\n=== 自定义矩阵配置演示 ===\n")
    
    engine = MemoryScoringEngine()
    
    # 添加新的维度和关键词
    print("添加自定义关键词:")
    
    # 添加安全相关关键词
    security_keywords = {
        'authentication': 8,
        'authorization': 8, 
        'encryption': 7,
        'oauth': 6,
        'jwt': 6,
        'security': 5
    }
    
    for keyword, weight in security_keywords.items():
        engine.keyword_matrix.add_keyword('validation', keyword, weight)
        print(f"  添加 validation.{keyword}: {weight}")
    
    # 添加前端相关关键词
    frontend_keywords = {
        'react': 7,
        'component': 6,
        'ui': 5,
        'interface': 6,
        'responsive': 5
    }
    
    for keyword, weight in frontend_keywords.items():
        engine.keyword_matrix.add_keyword('api_enhancement', keyword, weight)
        print(f"  添加 api_enhancement.{keyword}: {weight}")
    
    # 测试自定义关键词的效果
    test_requirement = "实现用户认证和授权系统，使用JWT和OAuth"
    memory_items = create_sample_memory_items()
    
    results = engine.score_memory_items(test_requirement, memory_items)
    
    print(f"\n测试需求: {test_requirement}")
    print("匹配到的新关键词:")
    
    for result in results:
        security_matches = [kw for kw in result.matched_keywords 
                          if kw in security_keywords or kw in frontend_keywords]
        if security_matches:
            print(f"  {result.title}: {', '.join(security_matches)}")


def main():
    """主演示函数"""
    print("🚀 记忆项目匹配度评分算法演示")
    print("=" * 80)
    
    try:
        # 基本功能演示
        demo_basic_scoring()
        
        # 反馈系统演示
        demo_feedback_system()
        
        # 矩阵更新演示
        demo_matrix_updates()
        
        # 高级功能演示
        demo_advanced_features()
        
        # 自定义矩阵演示
        demo_custom_matrix()
        
        print("\n🎉 所有演示完成！")
        print("\n💡 使用提示:")
        print("  1. 可以通过修改 keyword_matrix 来调整评分策略")
        print("  2. 用户反馈会自动改进算法的准确性")
        print("  3. 支持专家标注来快速优化关键词权重")
        print("  4. 可以保存和加载自定义的矩阵配置")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 