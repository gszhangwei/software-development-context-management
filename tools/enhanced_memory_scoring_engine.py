#!/usr/bin/env python3
"""
增强记忆项目匹配度评分算法

基于procedural.md中新增的记忆条目内容优化的评分算法，
特别针对工作流、Solution管理、跨类型操作等新技术概念进行了增强。
"""

import re
import json
import uuid
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter

# 导入基础类型
try:
    from .memory_scoring_engine import (
        MemoryItem, ScoringResult, UserRequirement, 
        RequirementAnalyzer, ConfidenceCalculator
    )
except ImportError:
    from memory_scoring_engine import (
        MemoryItem, ScoringResult, UserRequirement, 
        RequirementAnalyzer, ConfidenceCalculator
    )


class EnhancedKeywordMatrix:
    """增强的关键词匹配矩阵，针对新技术概念优化"""
    
    def __init__(self, version: str = "2.0.0"):
        self.version = version
        self.created_at = datetime.now()
        self.created_by = "enhanced_system"
        self.description = "Enhanced keyword matching matrix for workflow and solution management"
        
        # 增强的关键词矩阵 - 7个维度
        self.matrix = {
            # API增强和REST设计 (20%)
            'api_enhancement': {
                'controller': 5, 'api': 4, 'endpoint': 4, 'POST': 3, 'GET': 3,
                'unified': 6, 'enhance': 5, 'create': 3, 'update': 3,
                'rest': 4, 'service': 4, 'microservice': 6, 'architecture': 5,
                'unified-api': 8, 'multi-type-management': 8, 'service-selector': 7,
                'type-routing': 7, 'crud-operations': 6, 'http-status-codes': 5,
                'service-delegation': 6, 'error-handling': 6
            },
            
            # 实体和模型支持 (15%) 
            'entity_support': {
                'Solution': 10, 'Rule': 6, 'Prompt': 4, 'Workflow': 6,
                'SolutionService': 8, 'RuleService': 6, 'GenericService': 7,
                'entity': 5, 'model': 4, 'class': 3, 'PromptService': 7,
                'PromptController': 8, 'WorkflowController': 7,
                'entity-support': 6, 'model-support': 5
            },
            
            # 工作流集成和步骤管理 (20%) - 新增维度
            'workflow_integration': {
                'workflow': 8, 'step': 7, 'validation': 8, 'dependency': 7,
                'ordered-steps': 9, 'step-validation': 9, 'workflow-creation': 8,
                'workflow-integration': 10, 'cross-type-validation': 9,
                'referential-integrity': 8, 'pre-deletion-check': 7,
                'workflow-lifecycle': 7, 'step-dependency': 8,
                'workflow-management': 7, 'workflow-api': 6
            },
            
            # Solution特定管理 (15%) - 新增维度
            'solution_management': {
                'Solution': 10, 'SolutionService': 9, 'solution-reference': 8,
                'solution-id': 8, 'solution-type': 7, 'solution-as-step': 9,
                'mixed-step-types': 8, 'solution-validation': 8,
                'solution-support': 7, 'solution-integration': 8,
                'solution-management': 9, 'solution-api': 6
            },
            
            # 验证和检查机制 (15%)
            'validation_patterns': {
                'validate': 8, 'check': 5, 'verify': 5, 'exist': 6,
                'IdGenerator': 7, 'validateFormat': 8, 'validation': 6,
                'constraint': 5, 'rule': 4, 'cross-type-validation': 9,
                'dependency-validation': 8, 'referential-integrity': 8,
                'step-validation': 8, 'id-prefix-inference': 7,
                'validation-patterns': 7, 'input-validation': 6
            },
            
            # 多类型操作和批量处理 (10%)
            'multi_type_operations': {
                'mixed': 10, 'batch': 6, 'multiple': 5, 'prefix': 8,
                'selector': 7, 'routing': 6, 'polymorphic': 7,
                'hybrid': 6, 'heterogeneous': 5, 'multi-type-operations': 9,
                'batch-processing': 7, 'parallel-processing': 7,
                'type-abstraction': 6, 'batch-optimization': 6,
                'multi-type': 8, 'type-routing': 7
            },
            
            # 系统架构和设计模式 (5%) - 新增维度
            'system_architecture': {
                'architecture': 6, 'pattern': 5, 'design': 4, 'structure': 4,
                'dto-pattern': 7, 'factory-methods': 6, 'polymorphic-factory': 7,
                'user-context': 6, 'thread-safe': 6, 'auto-population': 5,
                'design-pattern': 6, 'system-design': 5, 'architecture-pattern': 6
            }
        }
        
        # 元数据
        self.metadata = {
            'total_keywords': sum(len(keywords) for keywords in self.matrix.values()),
            'dimensions': list(self.matrix.keys()),
            'avg_weights': {dim: np.mean(list(keywords.values())) 
                          for dim, keywords in self.matrix.items()},
            'validation_score': 0.0
        }
        
        # 更新的最大分数配置 - 7个维度
        self.max_scores = {
            'api_enhancement': 25,
            'entity_support': 20,
            'workflow_integration': 25,
            'solution_management': 20,
            'validation_patterns': 20,
            'multi_type_operations': 15,
            'system_architecture': 15
        }
    
    def get_keyword_weight(self, dimension: str, keyword: str) -> float:
        """获取关键词权重"""
        return self.matrix.get(dimension, {}).get(keyword, 0.0)
    
    def update_keyword_weight(self, dimension: str, keyword: str, weight: float):
        """更新关键词权重"""
        if dimension not in self.matrix:
            self.matrix[dimension] = {}
        self.matrix[dimension][keyword] = max(0, min(weight, 10))


class EnhancedWeightCalculator:
    """增强的权重计算器，针对新技术概念优化"""
    
    def __init__(self):
        # 更新的基础权重 - 7个维度
        self.base_weights = {
            'api_enhancement': 20,
            'entity_support': 15,
            'workflow_integration': 20,
            'solution_management': 15,
            'validation_patterns': 15,
            'multi_type_operations': 10,
            'system_architecture': 5
        }
    
    def calculate_weights(self, requirements: UserRequirement) -> Dict[str, float]:
        """根据需求动态计算权重"""
        weights = self.base_weights.copy()
        
        # 检查是否涉及工作流概念
        workflow_keywords = ['workflow', 'step', 'ordered', 'flow', 'process']
        if any(keyword in ' '.join(requirements.api_operations + requirements.functionalities).lower() 
               for keyword in workflow_keywords):
            weights['workflow_integration'] += 10
            weights['solution_management'] += 5
            weights['api_enhancement'] -= 5
            weights['system_architecture'] -= 5
            weights['multi_type_operations'] -= 5
        
        # 检查是否涉及Solution概念
        solution_keywords = ['solution', 'mixed', 'heterogeneous', 'multi-type']
        if any(keyword in ' '.join(requirements.entities + requirements.functionalities).lower() 
               for keyword in solution_keywords):
            weights['solution_management'] += 10
            weights['workflow_integration'] += 5
            weights['entity_support'] -= 5
            weights['system_architecture'] -= 5
            weights['multi_type_operations'] -= 5
        
        # 检查是否涉及验证需求
        validation_keywords = ['validate', 'check', 'verify', 'validation', 'dependency']
        if any(keyword in ' '.join(requirements.functionalities).lower() 
               for keyword in validation_keywords):
            weights['validation_patterns'] += 10
            weights['workflow_integration'] += 5
            weights['api_enhancement'] -= 5
            weights['system_architecture'] -= 5
            weights['entity_support'] -= 5
        
        # 检查是否涉及API设计
        api_keywords = ['api', 'endpoint', 'controller', 'rest', 'crud']
        if any(keyword in ' '.join(requirements.api_operations + requirements.functionalities).lower() 
               for keyword in api_keywords):
            weights['api_enhancement'] += 8
            weights['validation_patterns'] += 2
            weights['system_architecture'] -= 5
            weights['entity_support'] -= 5
        
        # 确保权重总和为100
        return self._normalize_weights(weights)
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """标准化权重，确保总和为100"""
        total = sum(weights.values())
        if total == 0:
            return weights
        
        return {k: (v / total) * 100 for k, v in weights.items()}


class EnhancedContentAnalyzer:
    """增强的内容分析器，提供更精确的语义匹配"""
    
    def __init__(self, keyword_matrix: EnhancedKeywordMatrix):
        self.keyword_matrix = keyword_matrix
        self.context_window = 100  # 增加上下文窗口大小
    
    def calculate_semantic_score(self, content: str, dimension: str) -> Dict[str, Any]:
        """计算增强的语义匹配分数"""
        content_lower = content.lower()
        keywords = self.keyword_matrix.matrix.get(dimension, {})
        
        score = 0
        matched_keywords = []
        keyword_positions = {}
        
        # 精确匹配
        for keyword, weight in keywords.items():
            keyword_lower = keyword.lower()
            if keyword_lower in content_lower:
                # 计算出现次数，多次出现给予额外分数
                count = content_lower.count(keyword_lower)
                score += weight * min(count, 3)  # 最多3倍加分
                matched_keywords.append(keyword)
                
                # 记录关键词位置
                positions = [m.start() for m in re.finditer(
                    re.escape(keyword_lower), content_lower
                )]
                keyword_positions[keyword] = positions
        
        # 上下文匹配奖励
        context_bonus = self._calculate_context_bonus(keyword_positions)
        
        # 结构匹配奖励
        structure_bonus = self._calculate_structure_bonus(content, dimension)
        
        # 密度奖励
        density_bonus = self._calculate_density_bonus(matched_keywords, len(content))
        
        # 语义相关性奖励（新增）
        semantic_bonus = self._calculate_semantic_bonus(content, dimension, matched_keywords)
        
        total_score = score + context_bonus + structure_bonus + density_bonus + semantic_bonus
        max_score = self.keyword_matrix.max_scores.get(dimension, 25)
        
        return {
            'raw_score': min(total_score, max_score),
            'max_score': max_score,
            'matched_keywords': matched_keywords,
            'context_bonus': context_bonus,
            'structure_bonus': structure_bonus,
            'density_bonus': density_bonus,
            'semantic_bonus': semantic_bonus
        }
    
    def _calculate_context_bonus(self, keyword_positions: Dict[str, List[int]]) -> float:
        """计算上下文匹配奖励"""
        bonus = 0
        keywords = list(keyword_positions.keys())
        
        for i, keyword1 in enumerate(keywords):
            for keyword2 in keywords[i+1:]:
                for pos1 in keyword_positions[keyword1]:
                    for pos2 in keyword_positions[keyword2]:
                        distance = abs(pos2 - pos1)
                        if distance < self.context_window:
                            bonus += 3  # 增加奖励分数
                        elif distance < self.context_window * 2:
                            bonus += 1.5
        
        return min(bonus, 8)  # 最多8分上下文奖励
    
    def _calculate_structure_bonus(self, content: str, dimension: str) -> float:
        """计算结构匹配奖励"""
        bonus = 0
        
        # 根据维度类型给予不同的结构奖励
        if dimension in ['workflow_integration', 'solution_management']:
            # 工作流和Solution相关内容的特殊结构
            if 'sequenceDiagram' in content or 'flowchart' in content:
                bonus += 4
            if '```' in content:  # 代码块
                bonus += 3
            if re.search(r'^\s*\d+\)', content, re.MULTILINE):  # 编号列表
                bonus += 2
        
        if dimension == 'api_enhancement':
            # API相关内容的特殊结构
            if 'POST' in content and 'GET' in content:
                bonus += 3
            if '/api/' in content or 'endpoint' in content:
                bonus += 2
        
        if dimension == 'validation_patterns':
            # 验证相关内容的特殊结构
            if 'Exception' in content:
                bonus += 2
            if 'validate' in content and 'check' in content:
                bonus += 2
        
        # 通用结构奖励
        if '```' in content:
            bonus += 2
        if re.search(r'^[\s]*[-*+]', content, re.MULTILINE):
            bonus += 1
        
        return min(bonus, 6)  # 最多6分结构奖励
    
    def _calculate_density_bonus(self, matched_keywords: List[str], content_length: int) -> float:
        """计算关键词密度奖励"""
        if content_length == 0:
            return 0
        
        density = len(matched_keywords) / (content_length / 200)  # 每200字符的关键词数
        
        if density > 8:
            return 4
        elif density > 5:
            return 3
        elif density > 2:
            return 2
        elif density > 1:
            return 1
        else:
            return 0
    
    def _calculate_semantic_bonus(self, content: str, dimension: str, 
                                 matched_keywords: List[str]) -> float:
        """计算语义相关性奖励（新增）"""
        bonus = 0
        content_lower = content.lower()
        
        # 工作流语义组合检测
        if dimension == 'workflow_integration':
            workflow_combinations = [
                (['workflow', 'step'], 3),
                (['solution', 'step'], 3),
                (['validate', 'dependency'], 2),
                (['cross-type', 'validation'], 3),
                (['ordered', 'steps'], 2)
            ]
            
            for combo, score in workflow_combinations:
                if all(word in content_lower for word in combo):
                    bonus += score
        
        # Solution管理语义组合检测
        if dimension == 'solution_management':
            solution_combinations = [
                (['solution', 'service'], 3),
                (['solution', 'reference'], 2),
                (['mixed', 'step'], 3),
                (['solution', 'validation'], 2),
                (['heterogeneous', 'type'], 2)
            ]
            
            for combo, score in solution_combinations:
                if all(word in content_lower for word in combo):
                    bonus += score
        
        # API增强语义组合检测
        if dimension == 'api_enhancement':
            api_combinations = [
                (['unified', 'api'], 3),
                (['multi-type', 'management'], 3),
                (['service', 'selector'], 2),
                (['crud', 'operations'], 2),
                (['rest', 'api'], 2)
            ]
            
            for combo, score in api_combinations:
                if all(word in content_lower for word in combo):
                    bonus += score
        
        return min(bonus, 8)  # 最多8分语义奖励


class EnhancedMemoryScoringEngine:
    """增强的记忆项目评分引擎"""
    
    def __init__(self, matrix_file: Optional[str] = None):
        self.keyword_matrix = self._load_or_create_enhanced_matrix(matrix_file)
        self.requirement_analyzer = RequirementAnalyzer()
        self.weight_calculator = EnhancedWeightCalculator()
        self.content_analyzer = EnhancedContentAnalyzer(self.keyword_matrix)
        self.confidence_calculator = ConfidenceCalculator()
        
        # 历史记录
        self.scoring_history: List[Dict] = []
    
    def _load_or_create_enhanced_matrix(self, matrix_file: Optional[str]) -> EnhancedKeywordMatrix:
        """加载或创建增强的关键词矩阵"""
        if matrix_file and Path(matrix_file).exists():
            try:
                with open(matrix_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    matrix = EnhancedKeywordMatrix(data.get('version', '2.0.0'))
                    if 'enhanced_matrix' in data:
                        matrix.matrix = data['enhanced_matrix']
                    matrix.metadata = data.get('metadata', {})
                    return matrix
            except Exception:
                pass
        
        return EnhancedKeywordMatrix()
    
    def score_memory_items(self, user_requirement: str, 
                          memory_items: List[MemoryItem]) -> List[ScoringResult]:
        """评分记忆项目列表（增强版）"""
        # 分析用户需求
        requirements = self.requirement_analyzer.extract_requirements(user_requirement)
        
        # 计算动态权重
        weights = self.weight_calculator.calculate_weights(requirements)
        
        results = []
        for memory_item in memory_items:
            result = self._score_single_memory(memory_item, requirements, weights)
            results.append(result)
        
        # 按总分排序
        results.sort(key=lambda x: x.total_score, reverse=True)
        
        # 记录评分历史
        self._record_scoring_session(user_requirement, requirements, weights, results)
        
        return results
    
    def _score_single_memory(self, memory_item: MemoryItem, 
                           requirements: UserRequirement, 
                           weights: Dict[str, float]) -> ScoringResult:
        """评分单个记忆项目（增强版）"""
        score_breakdown = {}
        total_weighted_score = 0
        all_matched_keywords = []
        
        # 对每个维度进行评分
        for dimension in self.keyword_matrix.matrix.keys():
            dimension_result = self.content_analyzer.calculate_semantic_score(
                memory_item.content, dimension
            )
            
            # 计算加权分数
            weight = weights.get(dimension, 0)
            if dimension_result['max_score'] > 0:
                weighted_score = (dimension_result['raw_score'] / dimension_result['max_score']) * weight
            else:
                weighted_score = 0
            
            total_weighted_score += weighted_score
            
            # 记录详细分数
            score_breakdown[dimension] = {
                'raw_score': dimension_result['raw_score'],
                'max_score': dimension_result['max_score'],
                'weight': weight,
                'weighted_score': weighted_score,
                'matched_keywords': dimension_result['matched_keywords'],
                'semantic_bonus': dimension_result.get('semantic_bonus', 0)
            }
            
            all_matched_keywords.extend(dimension_result['matched_keywords'])
        
        # 计算置信度
        confidence = self.confidence_calculator.calculate_confidence(
            score_breakdown, len(memory_item.content), all_matched_keywords
        )
        
        # 识别关键优势
        key_strengths = self._identify_key_strengths(score_breakdown, memory_item)
        
        return ScoringResult(
            memory_id=memory_item.id,
            title=memory_item.title,
            total_score=total_weighted_score,
            confidence=confidence,
            score_breakdown=score_breakdown,
            key_strengths=key_strengths,
            matched_keywords=list(set(all_matched_keywords))
        )
    
    def _identify_key_strengths(self, score_breakdown: Dict[str, Dict], 
                              memory_item: MemoryItem) -> List[str]:
        """识别记忆项目的关键优势（增强版）"""
        strengths = []
        
        for dimension, scores in score_breakdown.items():
            if scores['weighted_score'] > scores['weight'] * 0.7:  # 超过70%权重
                matched_keywords = scores['matched_keywords']
                if matched_keywords:
                    # 根据维度类型生成更精确的优势描述
                    if dimension == 'workflow_integration':
                        strength_desc = f"工作流集成: {', '.join(matched_keywords[:3])}"
                    elif dimension == 'solution_management':
                        strength_desc = f"Solution管理: {', '.join(matched_keywords[:3])}"
                    elif dimension == 'api_enhancement':
                        strength_desc = f"API增强: {', '.join(matched_keywords[:3])}"
                    else:
                        strength_desc = f"{dimension.replace('_', ' ').title()}: {', '.join(matched_keywords[:3])}"
                    strengths.append(strength_desc)
        
        # 添加基于标签的优势（增强版）
        important_tags = ['workflow', 'solution', 'api', 'validation', 'multi-type', 'architecture']
        for tag in memory_item.tags:
            tag_lower = tag.lower()
            for important_tag in important_tags:
                if important_tag in tag_lower:
                    strengths.append(f"专业标签: {tag}")
                    break
        
        return strengths[:6]  # 最多返回6个优势
    
    def _record_scoring_session(self, user_requirement: str, requirements: UserRequirement,
                               weights: Dict[str, float], results: List[ScoringResult]):
        """记录评分会话"""
        session = {
            'timestamp': datetime.now().isoformat(),
            'user_requirement': user_requirement,
            'analyzed_requirements': {
                'api_operations': requirements.api_operations,
                'entities': requirements.entities,
                'functionalities': requirements.functionalities,
                'constraints': requirements.constraints
            },
            'calculated_weights': weights,
            'results_count': len(results),
            'top_score': results[0].total_score if results else 0,
            'session_id': str(uuid.uuid4()),
            'algorithm_version': '2.0.0'
        }
        self.scoring_history.append(session)
    
    def save_enhanced_matrix(self, file_path: str):
        """保存增强的关键词矩阵"""
        data = {
            'version': self.keyword_matrix.version,
            'created_at': self.keyword_matrix.created_at.isoformat(),
            'created_by': self.keyword_matrix.created_by,
            'description': self.keyword_matrix.description,
            'enhanced_matrix': self.keyword_matrix.matrix,
            'metadata': self.keyword_matrix.metadata,
            'max_scores': self.keyword_matrix.max_scores
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def create_enhanced_scoring_engine(matrix_file: Optional[str] = None) -> EnhancedMemoryScoringEngine:
    """工厂函数：创建增强的评分引擎"""
    return EnhancedMemoryScoringEngine(matrix_file)


# 向后兼容的接口函数
def score_memories_enhanced(user_requirement: str, memory_items: List[MemoryItem]) -> List[ScoringResult]:
    """增强版记忆评分的便捷函数"""
    engine = create_enhanced_scoring_engine()
    return engine.score_memory_items(user_requirement, memory_items)


if __name__ == "__main__":
    # 测试增强的评分引擎
    try:
        from .memory_scoring_engine import create_sample_memory_items
    except ImportError:
        from memory_scoring_engine import create_sample_memory_items
    
    engine = create_enhanced_scoring_engine()
    
    # 使用工作流相关的测试需求
    test_requirement = """
    增强工作流创建API，支持将Solution作为步骤。
    需要更新数据模型支持Solution引用，验证Solution ID的存在性和有效性，
    支持混合步骤类型（Rule/Prompt和Solution），确保数据持久化正确。
    API应该支持批量操作和统一的DTO设计。
    """
    
    # 创建测试记忆项目
    memory_items = create_sample_memory_items()
    
    # 执行增强评分
    results = engine.score_memory_items(test_requirement, memory_items)
    
    print("=== 增强版记忆评分结果 ===\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title}")
        print(f"   总分: {result.total_score:.2f}/100")
        print(f"   置信度: {result.confidence:.1f}%")
        print(f"   关键优势: {', '.join(result.key_strengths)}")
        print(f"   匹配关键词: {', '.join(result.matched_keywords[:10])}")
        
        if i <= 2:  # 显示前2个结果的详细分解
            print(f"   详细分数分解:")
            for dimension, scores in result.score_breakdown.items():
                print(f"     {dimension}: {scores['weighted_score']:.2f}/{scores['weight']:.1f} "
                      f"(原始: {scores['raw_score']}/{scores['max_score']})")
        print()
    
    # 保存增强矩阵
    engine.save_enhanced_matrix("enhanced_keyword_matrix.json")
    print("增强关键词矩阵已保存到 enhanced_keyword_matrix.json") 