#!/usr/bin/env python3
"""
增强评分算法测试脚本

基于procedural.md中的真实记忆条目测试增强评分算法的效果，
验证对工作流、Solution管理等新技术概念的评分准确性。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from tools.enhanced_memory_scoring_engine import create_enhanced_scoring_engine, MemoryItem
from tools.memory_scoring_engine import MemoryScoringEngine  # 原始评分引擎
from src.core.procedural_memory_parser import load_procedural_memories


def load_procedural_memories_wrapper() -> list[MemoryItem]:
    """从procedural.md加载真实的记忆条目（使用专门的解析器）"""
    return load_procedural_memories()


def test_workflow_related_queries():
    """测试工作流相关的查询"""
    print("🧪 测试工作流相关查询")
    print("=" * 60)
    
    # 加载记忆条目
    memory_items = load_procedural_memories_wrapper()
    print(f"📚 加载了 {len(memory_items)} 个记忆条目")
    
    # 测试查询
    test_queries = [
        {
            "name": "工作流Solution集成",
            "query": """
            增强工作流创建API，支持将Solution作为步骤。
            需要更新数据模型支持Solution引用，验证Solution ID的存在性和有效性，
            支持混合步骤类型（Rule/Prompt和Solution），确保数据持久化正确。
            """
        },
        {
            "name": "API统一管理",
            "query": """
            设计统一的API管理系统，支持多种资源类型的CRUD操作。
            需要Service Selector模式进行类型路由，支持批量处理和ID前缀策略。
            """
        },
        {
            "name": "跨类型验证",
            "query": """
            实现跨类型验证机制，支持依赖关系检查和引用完整性验证。
            需要处理Rule和Solution的混合验证，防止孤立引用。
            """
        },
        {
            "name": "工作流步骤管理",
            "query": """
            优化工作流步骤管理，支持有序步骤和步骤依赖验证。
            需要支持Solution作为步骤类型，确保步骤引用的有效性。
            """
        }
    ]
    
    # 创建评分引擎
    enhanced_engine = create_enhanced_scoring_engine()
    original_engine = MemoryScoringEngine()
    
    for test_case in test_queries:
        print(f"\n🔍 测试查询: {test_case['name']}")
        print("-" * 40)
        print(f"查询内容: {test_case['query'].strip()}")
        
        # 增强评分结果
        enhanced_results = enhanced_engine.score_memory_items(test_case['query'], memory_items)
        
        # 原始评分结果
        original_results = original_engine.score_memory_items(test_case['query'], memory_items)
        
        # 比较结果
        print(f"\n📊 评分比较（前5名）:")
        print(f"{'排名':<4} {'增强算法':<50} {'原始算法':<50}")
        print("-" * 104)
        
        for i in range(min(5, len(enhanced_results), len(original_results))):
            enhanced = enhanced_results[i]
            original = original_results[i]
            
            enhanced_info = f"{enhanced.memory_id} ({enhanced.total_score:.1f})"
            original_info = f"{original.memory_id} ({original.total_score:.1f})"
            
            print(f"{i+1:<4} {enhanced_info:<50} {original_info:<50}")
        
        # 显示增强算法的详细分析
        if enhanced_results:
            top_result = enhanced_results[0]
            print(f"\n🏆 增强算法最佳匹配: {top_result.memory_id}")
            print(f"   总分: {top_result.total_score:.2f}/100")
            print(f"   置信度: {top_result.confidence:.1f}%")
            print(f"   关键优势: {', '.join(top_result.key_strengths[:3])}")
            print(f"   匹配关键词: {', '.join(top_result.matched_keywords[:8])}")
            
            # 显示详细分数分解
            print(f"   分数分解:")
            for dimension, scores in top_result.score_breakdown.items():
                if scores['weighted_score'] > 0:
                    print(f"     {dimension}: {scores['weighted_score']:.2f}/{scores['weight']:.1f} "
                          f"(语义奖励: {scores.get('semantic_bonus', 0):.1f})")
        
        print()


def test_specific_memory_scoring():
    """测试特定记忆条目的评分详情"""
    print("\n🔬 特定记忆条目评分详情分析")
    print("=" * 60)
    
    # 加载记忆条目
    memory_items = load_procedural_memories_wrapper()
    
    # 测试特定的查询
    test_query = """
    增强工作流创建API，支持将Solution作为步骤。
    需要更新数据模型支持Solution引用，验证Solution ID的存在性和有效性，
    支持混合步骤类型（Rule/Prompt和Solution），确保数据持久化正确。
    API应该支持批量操作和统一的DTO设计。
    """
    
    # 创建增强评分引擎
    enhanced_engine = create_enhanced_scoring_engine()
    results = enhanced_engine.score_memory_items(test_query, memory_items)
    
    print(f"查询: {test_query.strip()}")
    print(f"\n📈 评分结果详情（前3名）:")
    
    for i, result in enumerate(results[:3], 1):
        print(f"\n{i}. {result.memory_id}")
        print(f"   总分: {result.total_score:.2f}/100")
        print(f"   置信度: {result.confidence:.1f}%")
        print(f"   匹配关键词数: {len(result.matched_keywords)}")
        
        # 详细分数分解
        print(f"   维度评分:")
        for dimension, scores in result.score_breakdown.items():
            raw_score = scores['raw_score']
            max_score = scores['max_score']
            weight = scores['weight']
            weighted_score = scores['weighted_score']
            
            if raw_score > 0:
                print(f"     {dimension}:")
                print(f"       原始分数: {raw_score:.1f}/{max_score}")
                print(f"       权重: {weight:.1f}%")
                print(f"       加权分数: {weighted_score:.2f}")
                print(f"       匹配关键词: {', '.join(scores['matched_keywords'][:5])}")
                if 'semantic_bonus' in scores and scores['semantic_bonus'] > 0:
                    print(f"       语义奖励: {scores['semantic_bonus']:.1f}")


def compare_algorithm_performance():
    """比较算法性能"""
    print("\n⚡ 算法性能比较")
    print("=" * 60)
    
    # 加载记忆条目
    memory_items = load_procedural_memories_wrapper()
    
    # 测试查询
    test_query = """
    设计统一的多类型资源管理API，支持Solution和Rule的混合处理。
    需要Service Selector模式、ID前缀策略、批量操作和跨类型验证。
    """
    
    import time
    
    # 测试增强算法性能
    start_time = time.time()
    enhanced_engine = create_enhanced_scoring_engine()
    enhanced_results = enhanced_engine.score_memory_items(test_query, memory_items)
    enhanced_time = time.time() - start_time
    
    # 测试原始算法性能
    start_time = time.time()
    original_engine = MemoryScoringEngine()
    original_results = original_engine.score_memory_items(test_query, memory_items)
    original_time = time.time() - start_time
    
    print(f"📊 性能对比:")
    print(f"   增强算法: {enhanced_time:.3f}秒")
    print(f"   原始算法: {original_time:.3f}秒")
    print(f"   性能比: {enhanced_time/original_time:.2f}x")
    
    print(f"\n🎯 结果质量对比:")
    if enhanced_results and original_results:
        print(f"   增强算法最高分: {enhanced_results[0].total_score:.2f}")
        print(f"   原始算法最高分: {original_results[0].total_score:.2f}")
        print(f"   分数提升: {enhanced_results[0].total_score - original_results[0].total_score:.2f}")
        
        # 比较前3名的排序差异
        enhanced_top3 = [r.memory_id for r in enhanced_results[:3]]
        original_top3 = [r.memory_id for r in original_results[:3]]
        
        print(f"\n📈 排序对比:")
        print(f"   增强算法前3名: {', '.join(enhanced_top3)}")
        print(f"   原始算法前3名: {', '.join(original_top3)}")
        
        # 计算排序相似度
        common_in_top3 = len(set(enhanced_top3) & set(original_top3))
        print(f"   前3名重合度: {common_in_top3}/3")


def main():
    """主函数"""
    print("🚀 增强评分算法测试")
    print("基于procedural.md中真实记忆条目的评分测试")
    print("=" * 60)
    
    try:
        # 检查文件是否存在
        procedural_path = Path("test_data/teams/engineering_team/memory/procedural.md")
        if not procedural_path.exists():
            print(f"❌ 找不到测试文件: {procedural_path}")
            print("请确保项目根目录下存在该文件")
            return
        
        # 运行测试
        test_workflow_related_queries()
        test_specific_memory_scoring()
        compare_algorithm_performance()
        
        print(f"\n✅ 测试完成！")
        print(f"💡 建议：可以调整enhanced_memory_scoring_engine.py中的关键词权重以进一步优化评分效果")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 