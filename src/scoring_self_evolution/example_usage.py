#!/usr/bin/env python3
"""
自学习记忆评分引擎使用示例

这个脚本演示了如何使用自学习记忆评分引擎的各种功能，
包括基本使用、高级配置、学习监控和可视化等。
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入自学习评分引擎模块
from src.scoring_self_evolution import (
    SelfLearningMemoryScoringEngine,
    LearningVisualization,
    create_scoring_engine,
    create_visualizer,
    MemoryItem,
    UserRequirement
)


def create_sample_memory_items():
    """创建示例记忆项目"""
    return [
        MemoryItem(
            id="memory_001",
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
            - **新增工作流集成**: WorkflowIntegrationService支持多类型步骤管理
            - **Solution步骤处理**: SolutionStepProcessor专门处理Solution类型步骤
            """,
            tags=["architecture", "unified-controller", "service-selector", "workflow"],
            project="workflow-management-system",
            importance=5
        ),
        MemoryItem(
            id="memory_002", 
            title="创建工作流时序图流程设计",
            content="""
            # 创建工作流时序图流程设计
            
            ## 完整创建工作流时序图
            
            1. **用户验证**: 通过UserContext获取当前用户邮箱
            2. **请求丰富**: enrichWithUserEmail补充用户信息到请求中
            3. **规则验证**: 批量查询orderedSteps中的规则，确保存在性
            4. **新增Solution验证**: SolutionValidationService验证Solution步骤
            5. **跨类型依赖检查**: CrossTypeValidator确保混合步骤的兼容性
            6. **工作流持久化**: WorkflowPersistenceManager处理数据保存
            7. **异步通知**: EventPublisher发布工作流创建事件
            """,
            tags=["create-workflow", "api-flow", "sequence-diagram", "validation"],
            project="workflow-management-system", 
            importance=4
        ),
        MemoryItem(
            id="memory_003",
            title="Solution实体管理API设计",
            content="""
            # Solution实体管理API设计
            
            ## RESTful API端点设计
            
            ### 基础CRUD操作
            - GET /api/solutions - 列出所有Solution
            - GET /api/solutions/{id} - 获取特定Solution详情
            - POST /api/solutions - 创建新Solution
            - PUT /api/solutions/{id} - 更新Solution
            - DELETE /api/solutions/{id} - 删除Solution
            
            ### 高级操作
            - POST /api/solutions/batch - 批量创建Solution
            - PUT /api/solutions/batch - 批量更新Solution
            - POST /api/solutions/{id}/validate - 验证Solution配置
            - GET /api/solutions/{id}/dependencies - 获取Solution依赖关系
            
            ### DTO设计
            - SolutionCreateDTO: 创建Solution的数据传输对象
            - SolutionUpdateDTO: 更新Solution的数据传输对象
            - SolutionResponseDTO: 返回Solution信息的数据传输对象
            - SolutionBatchDTO: 批量操作的数据传输对象
            """,
            tags=["solution-api", "rest-api", "dto-design", "crud"],
            project="workflow-management-system",
            importance=5
        )
    ]


def demonstrate_basic_usage():
    """演示基本使用方法"""
    print("=" * 60)
    print("🚀 基本使用演示")
    print("=" * 60)
    
    # 创建评分引擎
    engine = create_scoring_engine()
    
    # 创建示例数据
    memory_items = create_sample_memory_items()
    
    user_requirement = """
    增强工作流创建API，支持将Solution作为步骤。
    需要更新数据模型支持Solution引用，验证Solution ID的存在性和有效性，
    支持混合步骤类型（Rule/Prompt和Solution），确保数据持久化正确。
    实现SolutionStepProcessor处理Solution类型的步骤，
    添加CrossTypeValidator进行跨类型验证，
    设计SolutionManagementAPI支持Solution的完整生命周期管理。
    """
    
    # 执行评分
    print("📊 正在执行记忆项目评分...")
    results = engine.score_memory_items(user_requirement, memory_items)
    
    # 显示结果
    print(f"\n📈 评分结果 (共 {len(results)} 个项目):")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   📊 总分: {result.total_score:.2f}")
        print(f"   🎯 置信度: {result.confidence:.1f}%")
        print(f"   ⭐ 关键优势: {', '.join(result.key_strengths[:3])}")
        print(f"   🔑 匹配关键词: {', '.join(result.matched_keywords[:8])}")
        
        # 显示发现的新关键词
        discovered_any = False
        for dimension, scores in result.score_breakdown.items():
            discovered = scores.get('discovered_keywords', {})
            if discovered:
                if not discovered_any:
                    print(f"   🔍 发现的新关键词:")
                    discovered_any = True
                print(f"     {dimension}: {list(discovered.keys())}")
    
    return engine


def demonstrate_learning_with_feedback(engine):
    """演示学习和反馈功能"""
    print("\n" + "=" * 60)
    print("🧠 学习和反馈演示")
    print("=" * 60)
    
    memory_items = create_sample_memory_items()
    
    # 模拟多次查询和反馈
    queries = [
        "实现Solution步骤验证和工作流集成",
        "设计统一的API Controller和Service选择器",
        "开发工作流创建的完整时序图流程",
        "构建Solution管理的RESTful API",
        "实现跨类型验证和依赖检查机制"
    ]
    
    print("🔄 模拟多次查询和学习过程...")
    
    for i, query in enumerate(queries, 1):
        print(f"\n第 {i} 次查询: {query[:30]}...")
        
        # 执行评分
        results = engine.score_memory_items(query, memory_items)
        
        if results:
            best_result = results[0]
            print(f"   最佳匹配: {best_result.title[:40]}... (评分: {best_result.total_score:.2f})")
            
            # 模拟用户反馈
            rating = 5 if i % 2 == 1 else 4  # 交替给出好评和较好评价
            engine.add_user_feedback(
                memory_id=best_result.memory_id,
                query=query,
                rating=rating,
                matched_keywords=best_result.matched_keywords[:3],
                comment=f"第{i}次反馈 - 评分{rating}星"
            )
            print(f"   用户反馈: {rating}星 ({'👍 好评' if rating >= 4 else '👎 差评'})")
    
    return engine


def demonstrate_learning_statistics(engine):
    """演示学习统计功能"""
    print("\n" + "=" * 60)
    print("📊 学习统计分析")
    print("=" * 60)
    
    # 获取学习统计
    stats = engine.get_learning_statistics()
    
    print("📈 基本学习指标:")
    print(f"   🔢 总评分会话数: {stats['total_scoring_sessions']}")
    print(f"   🎯 总关键词使用次数: {stats['total_keyword_usage']}")
    print(f"   🔍 发现新关键词数: {stats['discovered_keywords']}")
    print(f"   ⚖️ 稳定关键词数: {stats['stable_keywords']}")
    print(f"   📚 总关键词数: {stats['total_keywords']}")
    print(f"   📊 平均权重变化: {stats['average_weight_change']:.3f}")
    print(f"   💬 用户反馈数: {stats['feedback_count']}")
    
    print(f"\n🎛️ 学习配置状态:")
    print(f"   🤖 自动学习: {'✅ 启用' if stats['learning_enabled'] else '❌ 禁用'}")
    print(f"   🔍 关键词发现: {'✅ 启用' if stats['discovery_enabled'] else '❌ 禁用'}")
    print(f"   ⚖️ 系统稳定化: {'✅ 启用' if stats['stabilization_enabled'] else '❌ 禁用'}")
    
    # 获取关键词演化报告
    evolution = engine.get_keyword_evolution_report()
    
    print(f"\n🏆 表现最佳关键词 (Top 5):")
    for kw in evolution['top_performing_keywords'][:5]:
        print(f"   {kw['keyword']} ({kw['dimension']}): "
              f"贡献度={kw['avg_contribution']:.3f}, 使用{kw['usage_count']}次")
    
    print(f"\n🆕 最新发现关键词 (Top 5):")
    for kw in evolution['newly_discovered_keywords'][:5]:
        discovered_time = datetime.fromisoformat(kw['discovered_at']).strftime('%H:%M:%S')
        print(f"   {kw['keyword']} ({kw['dimension']}): "
              f"置信度={kw['confidence']:.3f}, 时间={discovered_time}")
    
    print(f"\n⚖️ 最稳定关键词 (Top 5):")
    for kw in evolution['most_stable_keywords'][:5]:
        print(f"   {kw['keyword']} ({kw['dimension']}): "
              f"稳定性={kw['stability_score']:.3f}, 使用{kw['usage_count']}次")


def demonstrate_advanced_configuration():
    """演示高级配置功能"""
    print("\n" + "=" * 60)
    print("⚙️ 高级配置演示")
    print("=" * 60)
    
    # 使用自定义配置创建引擎
    custom_engine = create_scoring_engine(
        learning_rate=0.03,  # 较慢的学习速度
        stabilization_threshold=30,  # 较低的稳定化阈值
        keyword_discovery_threshold=0.8,  # 较高的发现阈值
        auto_learning_enabled=True,
        keyword_discovery_enabled=True,
        stabilization_enabled=True
    )
    
    print("🎛️ 自定义配置已应用:")
    print(f"   📉 学习率: {custom_engine.keyword_matrix.learning_rate}")
    print(f"   📊 稳定化阈值: {custom_engine.keyword_matrix.stabilization_threshold}")
    print(f"   🎯 发现阈值: {custom_engine.keyword_matrix.keyword_discovery_threshold}")
    
    # 演示动态配置修改
    print("\n🔧 动态修改配置...")
    custom_engine.keyword_matrix.learning_rate = 0.02
    custom_engine.keyword_matrix.weight_decay = 0.98
    
    print("✅ 配置修改完成:")
    print(f"   📉 新学习率: {custom_engine.keyword_matrix.learning_rate}")
    print(f"   📉 权重衰减: {custom_engine.keyword_matrix.weight_decay}")
    
    return custom_engine


def demonstrate_visualization():
    """演示可视化功能"""
    print("\n" + "=" * 60)
    print("📊 可视化功能演示")
    print("=" * 60)
    
    # 检查是否有学习数据文件
    matrix_file = "self_learning_keyword_matrix.json"
    
    if not os.path.exists(matrix_file):
        print("⚠️ 未找到学习数据文件，将使用默认数据生成报告...")
        matrix_file = None
    
    try:
        # 创建可视化工具
        visualizer = create_visualizer(matrix_file)
        
        if visualizer.data:
            print("📈 生成学习报告...")
            
            # 生成文本报告
            report_file = "example_learning_report.md"
            visualizer.save_report(report_file)
            print(f"✅ 学习报告已保存到: {report_file}")
            
            # 显示简要统计
            metadata = visualizer.data.get('metadata', {})
            print(f"\n📊 数据概览:")
            print(f"   📚 总关键词数: {metadata.get('total_keywords', 0)}")
            print(f"   🎯 总使用次数: {metadata.get('total_usage_count', 0)}")
            print(f"   🔍 新发现关键词: {metadata.get('discovered_keywords_count', 0)}")
            
        else:
            print("⚠️ 暂无可视化数据")
            
    except Exception as e:
        print(f"❌ 可视化功能出错: {e}")


def demonstrate_persistence():
    """演示数据持久化功能"""
    print("\n" + "=" * 60)
    print("💾 数据持久化演示")
    print("=" * 60)
    
    # 创建引擎并进行一些学习
    engine = create_scoring_engine()
    memory_items = create_sample_memory_items()
    
    # 执行评分生成一些学习数据
    user_requirement = "实现高性能的Solution管理系统，支持批量操作和实时验证"
    results = engine.score_memory_items(user_requirement, memory_items)
    
    if results:
        # 添加反馈
        engine.add_user_feedback(
            memory_id=results[0].memory_id,
            query=user_requirement,
            rating=5,
            matched_keywords=results[0].matched_keywords[:3],
            comment="演示数据 - 优秀匹配"
        )
    
    # 保存学习结果
    save_file = "demo_learned_matrix.json"
    engine.save_matrix(save_file)
    print(f"💾 学习矩阵已保存到: {save_file}")
    
    # 验证加载
    try:
        loaded_engine = SelfLearningMemoryScoringEngine(save_file)
        loaded_stats = loaded_engine.get_learning_statistics()
        print(f"✅ 数据加载成功，包含 {loaded_stats['total_keywords']} 个关键词")
        
        # 清理演示文件
        if os.path.exists(save_file):
            os.remove(save_file)
            print("🧹 演示文件已清理")
            
    except Exception as e:
        print(f"❌ 数据加载出错: {e}")


def main():
    """主演示函数"""
    print("🎯 自学习记忆评分引擎 - 完整功能演示")
    print("版本: 3.0.0")
    print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        # 1. 基本使用演示
        engine = demonstrate_basic_usage()
        
        # 2. 学习和反馈演示
        engine = demonstrate_learning_with_feedback(engine)
        
        # 3. 学习统计分析
        demonstrate_learning_statistics(engine)
        
        # 4. 高级配置演示
        demonstrate_advanced_configuration()
        
        # 5. 可视化功能演示
        demonstrate_visualization()
        
        # 6. 数据持久化演示
        demonstrate_persistence()
        
        print("\n" + "=" * 60)
        print("🎉 演示完成！")
        print("=" * 60)
        print("✨ 自学习记忆评分引擎的所有核心功能都已展示完毕。")
        print("📚 更多信息请查看 README.md 和相关文档。")
        print("🚀 现在你可以开始在自己的项目中使用这个强大的工具了！")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 