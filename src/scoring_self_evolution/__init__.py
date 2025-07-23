"""
自学习记忆评分引擎模块

这个模块提供了智能的、自学习的记忆项目评分系统，能够根据使用情况自动优化和进化。

主要功能:
- 关键词自动发现和权重调整
- 用户反馈驱动的学习
- 系统稳定化机制
- 学习过程可视化

使用示例:
    from src.scoring_self_evolution import SelfLearningMemoryScoringEngine
    
    engine = SelfLearningMemoryScoringEngine()
    results = engine.score_memory_items(user_requirement, memory_items)
"""

from .enhanced_memory_scoring_engine import (
    SelfLearningMemoryScoringEngine,
    SelfLearningKeywordMatrix,
    RequirementAnalyzer,
    EnhancedContentAnalyzer,
    UserRequirement,
    MemoryItem,
    ScoringResult,
    KeywordStats,
    MatrixChange,
    UserFeedback,
    ChangeType,
    UpdateSource
)

from .learning_visualization import LearningVisualization

__version__ = "3.0.0"
__author__ = "AI Assistant"
__description__ = "Self-learning memory scoring engine with automatic keyword discovery and adaptive weighting"

# 便捷的工厂函数
def create_scoring_engine(matrix_file=None, **kwargs):
    """
    创建自学习评分引擎的便捷函数
    
    Args:
        matrix_file (str, optional): 预训练的矩阵文件路径
        **kwargs: 其他配置参数
    
    Returns:
        SelfLearningMemoryScoringEngine: 配置好的评分引擎实例
    """
    engine = SelfLearningMemoryScoringEngine(matrix_file)
    
    # 应用配置参数
    for key, value in kwargs.items():
        if hasattr(engine, key):
            setattr(engine, key, value)
        elif hasattr(engine.keyword_matrix, key):
            setattr(engine.keyword_matrix, key, value)
    
    return engine

def create_visualizer(matrix_file="self_learning_keyword_matrix.json"):
    """
    创建学习可视化工具的便捷函数
    
    Args:
        matrix_file (str): 矩阵文件路径
    
    Returns:
        LearningVisualization: 可视化工具实例
    """
    return LearningVisualization(matrix_file)

# 导出主要类和函数
__all__ = [
    # 主要引擎类
    'SelfLearningMemoryScoringEngine',
    'SelfLearningKeywordMatrix',
    'RequirementAnalyzer',
    'EnhancedContentAnalyzer',
    
    # 数据结构
    'UserRequirement',
    'MemoryItem', 
    'ScoringResult',
    'KeywordStats',
    'MatrixChange',
    'UserFeedback',
    
    # 枚举类型
    'ChangeType',
    'UpdateSource',
    
    # 可视化工具
    'LearningVisualization',
    
    # 便捷函数
    'create_scoring_engine',
    'create_visualizer',
    
    # 元信息
    '__version__',
    '__author__',
    '__description__'
] 