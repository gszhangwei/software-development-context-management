#!/usr/bin/env python3
"""
记忆项目匹配度评分算法

基于用户需求和记忆项目内容，计算精准的匹配度评分，支持动态更新和多种评分策略。
"""

import re
import json
import uuid
import numpy as np
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from abc import ABC, abstractmethod
from enum import Enum


class ChangeType(Enum):
    """变更类型枚举"""
    ADD_KEYWORD = "add_keyword"
    UPDATE_WEIGHT = "update_weight"
    REMOVE_KEYWORD = "remove_keyword"
    ADD_DIMENSION = "add_dimension"
    REMOVE_DIMENSION = "remove_dimension"


class UpdateSource(Enum):
    """更新来源枚举"""
    USER_FEEDBACK = "user_feedback"
    EXPERT_ANNOTATION = "expert_annotation"
    AUTO_LEARNING = "auto_learning"
    PERFORMANCE_MONITORING = "performance_monitoring"


@dataclass
class UserRequirement:
    """用户需求数据结构"""
    text: str
    api_operations: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    functionalities: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class MemoryItem:
    """记忆项目数据结构"""
    id: str
    title: str
    content: str
    tags: List[str]
    project: str
    importance: int
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ScoringResult:
    """评分结果数据结构"""
    memory_id: str
    title: str
    total_score: float
    confidence: float
    score_breakdown: Dict[str, Dict[str, Union[int, float, List[str]]]]
    key_strengths: List[str]
    matched_keywords: List[str]


@dataclass
class MatrixChange:
    """矩阵变更记录"""
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    change_type: ChangeType = ChangeType.UPDATE_WEIGHT
    dimension: str = ""
    keyword: str = ""
    old_value: Optional[Union[int, float]] = None
    new_value: Optional[Union[int, float]] = None
    reason: str = ""
    source: UpdateSource = UpdateSource.USER_FEEDBACK
    confidence: float = 0.0


@dataclass
class UserFeedback:
    """用户反馈数据结构"""
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_id: str = ""
    query: str = ""
    rating: int = 3  # 1-5 scale
    matched_keywords: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    comment: str = ""


@dataclass
class ExpertAnnotation:
    """专家标注数据结构"""
    annotation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    expert_id: str = ""
    keyword: str = ""
    dimension: str = ""
    suggested_weight: float = 0.0
    confidence: float = 0.0
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class KeywordMatrix:
    """关键词匹配矩阵"""
    
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.created_at = datetime.now()
        self.created_by = "system"
        self.description = "Keyword matching matrix"
        
        # 初始化关键词矩阵
        self.matrix = {
            'api_enhancement': {
                'controller': 5, 'api': 4, 'endpoint': 4, 'POST': 3, 'GET': 3,
                'unified': 6, 'enhance': 5, 'create': 3, 'update': 3,
                'rest': 4, 'service': 4, 'microservice': 6, 'architecture': 5
            },
            'entity_support': {
                'Solution': 10, 'Rule': 6, 'Prompt': 4, 'Workflow': 6,
                'SolutionService': 8, 'RuleService': 6, 'GenericService': 7,
                'entity': 5, 'model': 4, 'class': 3
            },
            'data_model': {
                'DTO': 6, 'Entity': 5, 'Model': 4, 'classDiagram': 8,
                'UnifiedDTO': 8, 'Response': 4, 'Request': 4,
                'schema': 5, 'structure': 4, 'design': 3
            },
            'validation': {
                'validate': 8, 'check': 5, 'verify': 5, 'exist': 6,
                'IdGenerator': 7, 'validateFormat': 8, 'validation': 6,
                'constraint': 5, 'rule': 4
            },
            'mixed_type': {
                'mixed': 10, 'batch': 6, 'multiple': 5, 'prefix': 8,
                'selector': 7, 'routing': 6, 'polymorphic': 7,
                'hybrid': 6, 'heterogeneous': 5
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
        
        # 最大分数配置
        self.max_scores = {
            'api_enhancement': 25,
            'entity_support': 25,
            'data_model': 20,
            'validation': 15,
            'mixed_type': 15
        }
    
    def get_keyword_weight(self, dimension: str, keyword: str) -> float:
        """获取关键词权重"""
        return self.matrix.get(dimension, {}).get(keyword, 0.0)
    
    def update_keyword_weight(self, dimension: str, keyword: str, weight: float):
        """更新关键词权重"""
        if dimension not in self.matrix:
            self.matrix[dimension] = {}
        self.matrix[dimension][keyword] = max(0, min(weight, 10))
    
    def add_keyword(self, dimension: str, keyword: str, weight: float):
        """添加新关键词"""
        if dimension not in self.matrix:
            self.matrix[dimension] = {}
        self.matrix[dimension][keyword] = max(0, min(weight, 10))
        self.metadata['total_keywords'] += 1
    
    def remove_keyword(self, dimension: str, keyword: str):
        """删除关键词"""
        if dimension in self.matrix and keyword in self.matrix[dimension]:
            del self.matrix[dimension][keyword]
            self.metadata['total_keywords'] -= 1
    
    def get_all_keywords(self, dimension: Optional[str] = None) -> Dict[str, List[str]]:
        """获取所有关键词"""
        if dimension:
            return {dimension: list(self.matrix.get(dimension, {}).keys())}
        return {dim: list(keywords.keys()) for dim, keywords in self.matrix.items()}


class RequirementAnalyzer:
    """需求分析器"""
    
    def __init__(self):
        self.api_operations_pattern = re.compile(
            r'\b(POST|GET|PUT|DELETE|PATCH|create|update|delete|query|search)\b', 
            re.IGNORECASE
        )
        self.entity_pattern = re.compile(
            r'\b(Workflow|Solution|Rule|Prompt|Entity|Model|DTO|Service)\b'
        )
        self.functionality_pattern = re.compile(
            r'\b(validate|enhance|optimize|implement|design|configure|deploy|test)\b',
            re.IGNORECASE
        )
    
    def extract_requirements(self, text: str) -> UserRequirement:
        """从文本中提取需求要素"""
        api_operations = self.api_operations_pattern.findall(text)
        entities = self.entity_pattern.findall(text)
        functionalities = self.functionality_pattern.findall(text)
        
        # 提取约束条件
        constraints = []
        if 'valid' in text.lower():
            constraints.append('validation')
        if 'error' in text.lower():
            constraints.append('error_handling')
        if 'persist' in text.lower():
            constraints.append('persistence')
        
        return UserRequirement(
            text=text,
            api_operations=list(set(api_operations)),
            entities=list(set(entities)),
            functionalities=list(set(functionalities)),
            constraints=constraints
        )


class WeightCalculator:
    """权重计算器"""
    
    def __init__(self):
        self.base_weights = {
            'api_enhancement': 25,
            'entity_support': 25,
            'data_model': 20,
            'validation': 15,
            'mixed_type': 15
        }
    
    def calculate_weights(self, requirements: UserRequirement) -> Dict[str, float]:
        """根据需求动态计算权重"""
        weights = self.base_weights.copy()
        
        # 根据实体类型调整权重
        if 'Solution' in requirements.entities:
            weights['entity_support'] += 5
            weights['mixed_type'] += 5
            weights['data_model'] -= 5
            weights['validation'] -= 5
        
        # 根据API操作调整权重
        if any(op in requirements.api_operations for op in ['POST', 'create']):
            weights['api_enhancement'] += 3
            weights['validation'] += 2
            weights['data_model'] -= 5
        
        # 根据功能性需求调整权重
        if 'validate' in requirements.functionalities:
            weights['validation'] += 5
            weights['api_enhancement'] -= 2
            weights['data_model'] -= 3
        
        # 确保权重总和为100
        return self._normalize_weights(weights)
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """标准化权重，确保总和为100"""
        total = sum(weights.values())
        if total == 0:
            return weights
        
        return {k: (v / total) * 100 for k, v in weights.items()}


class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self, keyword_matrix: KeywordMatrix):
        self.keyword_matrix = keyword_matrix
        self.context_window = 50  # 上下文窗口大小（字符数）
    
    def calculate_semantic_score(self, content: str, dimension: str) -> Dict[str, Any]:
        """计算语义匹配分数"""
        content_lower = content.lower()
        keywords = self.keyword_matrix.matrix.get(dimension, {})
        
        score = 0
        matched_keywords = []
        keyword_positions = {}
        
        # 精确匹配
        for keyword, weight in keywords.items():
            if keyword.lower() in content_lower:
                score += weight
                matched_keywords.append(keyword)
                # 记录关键词位置
                positions = [m.start() for m in re.finditer(
                    re.escape(keyword.lower()), content_lower
                )]
                keyword_positions[keyword] = positions
        
        # 上下文匹配奖励
        context_bonus = self._calculate_context_bonus(keyword_positions)
        
        # 结构匹配奖励
        structure_bonus = self._calculate_structure_bonus(content, dimension)
        
        # 密度奖励
        density_bonus = self._calculate_density_bonus(matched_keywords, len(content))
        
        total_score = score + context_bonus + structure_bonus + density_bonus
        max_score = self.keyword_matrix.max_scores.get(dimension, 25)
        
        return {
            'raw_score': min(total_score, max_score),
            'max_score': max_score,
            'matched_keywords': matched_keywords,
            'context_bonus': context_bonus,
            'structure_bonus': structure_bonus,
            'density_bonus': density_bonus
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
                            bonus += 2
                        elif distance < self.context_window * 2:
                            bonus += 1
        
        return min(bonus, 5)  # 最多5分上下文奖励
    
    def _calculate_structure_bonus(self, content: str, dimension: str) -> float:
        """计算结构匹配奖励"""
        bonus = 0
        
        # 类图结构
        if dimension == 'data_model' and 'classDiagram' in content:
            bonus += 3
        
        # 时序图结构
        if dimension == 'api_enhancement' and 'sequenceDiagram' in content:
            bonus += 3
        
        # 代码块
        if '```' in content:
            bonus += 2
        
        # 列表结构
        if re.search(r'^[\s]*[-*+]', content, re.MULTILINE):
            bonus += 1
        
        return min(bonus, 4)  # 最多4分结构奖励
    
    def _calculate_density_bonus(self, matched_keywords: List[str], content_length: int) -> float:
        """计算关键词密度奖励"""
        if content_length == 0:
            return 0
        
        density = len(matched_keywords) / (content_length / 100)  # 每100字符的关键词数
        
        if density > 5:
            return 3
        elif density > 3:
            return 2
        elif density > 1:
            return 1
        else:
            return 0


class ConfidenceCalculator:
    """置信度计算器"""
    
    def calculate_confidence(self, score_breakdown: Dict[str, Dict], 
                           content_length: int, matched_keywords: List[str]) -> float:
        """计算置信度"""
        # 基于覆盖度的置信度
        coverage = sum(1 for scores in score_breakdown.values() 
                      if scores['raw_score'] > 0) / len(score_breakdown)
        
        # 基于内容长度的置信度
        length_factor = min(content_length / 1000, 1.0)
        
        # 基于关键词匹配数量的置信度
        keyword_factor = min(len(matched_keywords) / 10, 1.0)
        
        # 综合置信度
        confidence = (coverage * 0.5 + length_factor * 0.3 + keyword_factor * 0.2) * 100
        
        return min(confidence, 95)  # 最高95%置信度


class MemoryScoringEngine:
    """记忆项目评分引擎"""
    
    def __init__(self, matrix_file: Optional[str] = None):
        self.keyword_matrix = self._load_or_create_matrix(matrix_file)
        self.requirement_analyzer = RequirementAnalyzer()
        self.weight_calculator = WeightCalculator()
        self.content_analyzer = ContentAnalyzer(self.keyword_matrix)
        self.confidence_calculator = ConfidenceCalculator()
        
        # 历史记录
        self.scoring_history: List[Dict] = []
        self.feedback_history: List[UserFeedback] = []
    
    def _load_or_create_matrix(self, matrix_file: Optional[str]) -> KeywordMatrix:
        """加载或创建关键词矩阵"""
        if matrix_file and Path(matrix_file).exists():
            with open(matrix_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                matrix = KeywordMatrix(data.get('version', '1.0.0'))
                matrix.matrix = data.get('matrix', {})
                matrix.metadata = data.get('metadata', {})
                return matrix
        else:
            return KeywordMatrix()
    
    def score_memory_items(self, user_requirement: str, 
                          memory_items: List[MemoryItem]) -> List[ScoringResult]:
        """评分记忆项目列表"""
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
        """评分单个记忆项目"""
        score_breakdown = {}
        total_weighted_score = 0
        all_matched_keywords = []
        
        # 对每个维度进行评分
        for dimension in self.keyword_matrix.matrix.keys():
            dimension_result = self.content_analyzer.calculate_semantic_score(
                memory_item.content, dimension
            )
            
            # 计算加权分数
            weighted_score = (dimension_result['raw_score'] / dimension_result['max_score']) * weights[dimension]
            total_weighted_score += weighted_score
            
            # 记录详细分数
            score_breakdown[dimension] = {
                'raw_score': dimension_result['raw_score'],
                'max_score': dimension_result['max_score'],
                'weight': weights[dimension],
                'weighted_score': weighted_score,
                'matched_keywords': dimension_result['matched_keywords']
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
        """识别记忆项目的关键优势"""
        strengths = []
        
        for dimension, scores in score_breakdown.items():
            if scores['weighted_score'] > scores['weight'] * 0.8:  # 超过80%权重
                matched_keywords = scores['matched_keywords']
                if matched_keywords:
                    strength_desc = f"{dimension.replace('_', ' ').title()}: {', '.join(matched_keywords[:3])}"
                    strengths.append(strength_desc)
        
        # 添加基于标签的优势
        important_tags = ['architecture', 'workflow', 'api-design', 'performance']
        for tag in memory_item.tags:
            if tag in important_tags:
                strengths.append(f"Tagged as: {tag}")
        
        return strengths[:5]  # 最多返回5个优势
    
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
            'session_id': str(uuid.uuid4())
        }
        self.scoring_history.append(session)
    
    def add_user_feedback(self, memory_id: str, query: str, rating: int, 
                         matched_keywords: List[str], comment: str = ""):
        """添加用户反馈"""
        feedback = UserFeedback(
            memory_id=memory_id,
            query=query,
            rating=rating,
            matched_keywords=matched_keywords,
            comment=comment
        )
        self.feedback_history.append(feedback)
    
    def save_matrix(self, file_path: str):
        """保存关键词矩阵"""
        data = {
            'version': self.keyword_matrix.version,
            'created_at': self.keyword_matrix.created_at.isoformat(),
            'matrix': self.keyword_matrix.matrix,
            'metadata': self.keyword_matrix.metadata,
            'max_scores': self.keyword_matrix.max_scores
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_matrix(self, file_path: str):
        """加载关键词矩阵"""
        self.keyword_matrix = self._load_or_create_matrix(file_path)
        self.content_analyzer = ContentAnalyzer(self.keyword_matrix)
    
    def get_scoring_statistics(self) -> Dict[str, Any]:
        """获取评分统计信息"""
        if not self.scoring_history:
            return {}
        
        total_sessions = len(self.scoring_history)
        avg_top_score = np.mean([session['top_score'] for session in self.scoring_history])
        
        # 最常见的需求实体
        all_entities = []
        for session in self.scoring_history:
            all_entities.extend(session['analyzed_requirements']['entities'])
        
        entity_counter = Counter(all_entities)
        
        # 反馈统计
        if self.feedback_history:
            avg_rating = np.mean([fb.rating for fb in self.feedback_history])
            feedback_count = len(self.feedback_history)
        else:
            avg_rating = 0
            feedback_count = 0
        
        return {
            'total_scoring_sessions': total_sessions,
            'average_top_score': avg_top_score,
            'most_common_entities': entity_counter.most_common(5),
            'feedback_count': feedback_count,
            'average_user_rating': avg_rating,
            'matrix_version': self.keyword_matrix.version,
            'total_keywords': self.keyword_matrix.metadata.get('total_keywords', 0)
        }


# 更新机制相关类

class UpdateTrigger(ABC):
    """更新触发器抽象基类"""
    
    @abstractmethod
    def should_trigger(self) -> bool:
        pass
    
    @abstractmethod
    def urgency_level(self) -> str:
        pass
    
    @abstractmethod
    def get_reason(self) -> str:
        pass


class FeedbackTrigger(UpdateTrigger):
    """基于用户反馈的触发器"""
    
    def __init__(self, threshold: int = 10, negative_ratio_threshold: float = 0.3):
        self.threshold = threshold
        self.negative_ratio_threshold = negative_ratio_threshold
        self.feedback_count = 0
        self.negative_feedback_ratio = 0.0
    
    def update_stats(self, feedback_list: List[UserFeedback]):
        """更新反馈统计"""
        self.feedback_count = len(feedback_list)
        if self.feedback_count > 0:
            negative_count = sum(1 for fb in feedback_list if fb.rating < 3)
            self.negative_feedback_ratio = negative_count / self.feedback_count
    
    def should_trigger(self) -> bool:
        return (self.feedback_count >= self.threshold and 
                self.negative_feedback_ratio > self.negative_ratio_threshold)
    
    def urgency_level(self) -> str:
        if self.negative_feedback_ratio > 0.5:
            return "HIGH"
        elif self.negative_feedback_ratio > 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_reason(self) -> str:
        return (f"Negative feedback ratio: {self.negative_feedback_ratio:.2f}, "
                f"Total feedback: {self.feedback_count}")


class PerformanceTrigger(UpdateTrigger):
    """基于性能监控的触发器"""
    
    def __init__(self, drop_threshold: float = 0.05):
        self.drop_threshold = drop_threshold
        self.baseline_accuracy = 0.85
        self.current_accuracy = 0.85
    
    def update_accuracy(self, current_accuracy: float):
        """更新当前准确率"""
        self.current_accuracy = current_accuracy
    
    def should_trigger(self) -> bool:
        accuracy_drop = self.baseline_accuracy - self.current_accuracy
        return accuracy_drop > self.drop_threshold
    
    def urgency_level(self) -> str:
        accuracy_drop = self.baseline_accuracy - self.current_accuracy
        if accuracy_drop > 0.15:
            return "HIGH"
        elif accuracy_drop > 0.10:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_reason(self) -> str:
        accuracy_drop = self.baseline_accuracy - self.current_accuracy
        return f"Accuracy dropped by {accuracy_drop:.3f} from baseline {self.baseline_accuracy:.3f}"


class MatrixUpdateManager:
    """矩阵更新管理器"""
    
    def __init__(self, scoring_engine: MemoryScoringEngine):
        self.scoring_engine = scoring_engine
        self.change_history: List[MatrixChange] = []
        self.triggers = {
            'feedback': FeedbackTrigger(),
            'performance': PerformanceTrigger()
        }
        self.learning_rate = 0.1
        self.momentum = 0.9
        self.momentum_cache: Dict[str, float] = {}
    
    def check_update_triggers(self) -> List[Dict[str, Any]]:
        """检查是否需要更新"""
        # 更新触发器状态
        self.triggers['feedback'].update_stats(self.scoring_engine.feedback_history)
        
        active_triggers = []
        for name, trigger in self.triggers.items():
            if trigger.should_trigger():
                active_triggers.append({
                    'name': name,
                    'urgency': trigger.urgency_level(),
                    'reason': trigger.get_reason()
                })
        
        return active_triggers
    
    def apply_feedback_updates(self, feedback_data: List[UserFeedback]) -> List[MatrixChange]:
        """基于用户反馈应用更新"""
        changes = []
        
        # 分析每个关键词的表现
        keyword_performance = self._analyze_keyword_performance(feedback_data)
        
        for keyword, stats in keyword_performance.items():
            if stats['sample_count'] >= 5:  # 最少需要5个样本
                dimension = self._find_keyword_dimension(keyword)
                if dimension:
                    new_weight = self._calculate_new_weight(keyword, stats)
                    old_weight = self.scoring_engine.keyword_matrix.get_keyword_weight(dimension, keyword)
                    
                    if abs(new_weight - old_weight) > 0.5:  # 变化幅度足够大
                        change = MatrixChange(
                            change_type=ChangeType.UPDATE_WEIGHT,
                            dimension=dimension,
                            keyword=keyword,
                            old_value=old_weight,
                            new_value=new_weight,
                            reason=f"Feedback analysis: {stats}",
                            source=UpdateSource.USER_FEEDBACK,
                            confidence=min(stats['sample_count'] / 20, 1.0)
                        )
                        
                        self.scoring_engine.keyword_matrix.update_keyword_weight(
                            dimension, keyword, new_weight
                        )
                        changes.append(change)
                        self.change_history.append(change)
        
        return changes
    
    def _analyze_keyword_performance(self, feedback_data: List[UserFeedback]) -> Dict[str, Dict]:
        """分析关键词表现"""
        keyword_stats = defaultdict(lambda: {
            'total_matches': 0,
            'positive_matches': 0,
            'negative_matches': 0,
            'avg_rating': 0.0,
            'sample_count': 0
        })
        
        for feedback in feedback_data:
            for keyword in feedback.matched_keywords:
                stats = keyword_stats[keyword]
                stats['total_matches'] += 1
                stats['sample_count'] += 1
                
                if feedback.rating >= 4:
                    stats['positive_matches'] += 1
                elif feedback.rating <= 2:
                    stats['negative_matches'] += 1
                
                # 更新平均评分
                stats['avg_rating'] = (
                    (stats['avg_rating'] * (stats['sample_count'] - 1) + feedback.rating)
                    / stats['sample_count']
                )
        
        return dict(keyword_stats)
    
    def _find_keyword_dimension(self, keyword: str) -> Optional[str]:
        """查找关键词所属维度"""
        for dimension, keywords in self.scoring_engine.keyword_matrix.matrix.items():
            if keyword in keywords:
                return dimension
        return None
    
    def _calculate_new_weight(self, keyword: str, stats: Dict) -> float:
        """计算新的权重值"""
        current_weight = 0
        dimension = self._find_keyword_dimension(keyword)
        if dimension:
            current_weight = self.scoring_engine.keyword_matrix.get_keyword_weight(dimension, keyword)
        
        # 基于平均评分和正面匹配率计算调整
        avg_rating = stats['avg_rating']
        positive_ratio = stats['positive_matches'] / stats['total_matches'] if stats['total_matches'] > 0 else 0
        
        performance_score = (avg_rating / 5) * 0.6 + positive_ratio * 0.4
        
        # 使用梯度下降式更新
        gradient = (performance_score - 0.6) * 2  # 目标性能分数为0.6
        
        # 应用动量
        cache_key = f"{dimension}_{keyword}"
        if cache_key in self.momentum_cache:
            gradient = self.momentum * self.momentum_cache[cache_key] + (1 - self.momentum) * gradient
        
        new_weight = current_weight + self.learning_rate * gradient
        new_weight = max(1, min(new_weight, 10))  # 限制在1-10范围内
        
        self.momentum_cache[cache_key] = gradient
        
        return new_weight
    
    def add_expert_annotation(self, annotation: ExpertAnnotation) -> bool:
        """添加专家标注"""
        # 验证专家标注的有效性
        if annotation.confidence < 0.7:
            return False
        
        change = MatrixChange(
            change_type=ChangeType.UPDATE_WEIGHT,
            dimension=annotation.dimension,
            keyword=annotation.keyword,
            old_value=self.scoring_engine.keyword_matrix.get_keyword_weight(
                annotation.dimension, annotation.keyword
            ),
            new_value=annotation.suggested_weight,
            reason=annotation.reasoning,
            source=UpdateSource.EXPERT_ANNOTATION,
            confidence=annotation.confidence
        )
        
        self.scoring_engine.keyword_matrix.update_keyword_weight(
            annotation.dimension, annotation.keyword, annotation.suggested_weight
        )
        
        self.change_history.append(change)
        return True
    
    def rollback_changes(self, change_ids: List[str]) -> bool:
        """回滚指定的变更"""
        rollback_changes = []
        
        for change in self.change_history:
            if change.change_id in change_ids:
                # 创建回滚变更
                rollback_change = MatrixChange(
                    change_type=change.change_type,
                    dimension=change.dimension,
                    keyword=change.keyword,
                    old_value=change.new_value,
                    new_value=change.old_value,
                    reason=f"Rollback of change {change.change_id}",
                    source=UpdateSource.PERFORMANCE_MONITORING
                )
                
                # 应用回滚
                if change.change_type == ChangeType.UPDATE_WEIGHT:
                    self.scoring_engine.keyword_matrix.update_keyword_weight(
                        change.dimension, change.keyword, change.old_value
                    )
                elif change.change_type == ChangeType.ADD_KEYWORD:
                    self.scoring_engine.keyword_matrix.remove_keyword(
                        change.dimension, change.keyword
                    )
                elif change.change_type == ChangeType.REMOVE_KEYWORD:
                    self.scoring_engine.keyword_matrix.add_keyword(
                        change.dimension, change.keyword, change.old_value
                    )
                
                rollback_changes.append(rollback_change)
        
        self.change_history.extend(rollback_changes)
        return len(rollback_changes) > 0
    
    def get_change_summary(self, days: int = 7) -> Dict[str, Any]:
        """获取变更摘要"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_changes = [
            change for change in self.change_history 
            if change.timestamp >= cutoff_date
        ]
        
        change_types = Counter(change.change_type.value for change in recent_changes)
        change_sources = Counter(change.source.value for change in recent_changes)
        
        return {
            'total_changes': len(recent_changes),
            'change_types': dict(change_types),
            'change_sources': dict(change_sources),
            'avg_confidence': np.mean([change.confidence for change in recent_changes]) if recent_changes else 0,
            'period_days': days
        }


def main():
    """主函数 - 演示用法"""
    # 创建评分引擎
    engine = MemoryScoringEngine()
    
    # 示例记忆项目
    memory_items = [
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
            """,
            tags=["architecture", "unified-controller", "service-selector"],
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
            """,
            tags=["create-workflow", "api-flow", "sequence-diagram"],
            project="workflow-management-system", 
            importance=4
        )
    ]
    
    # 用户需求
    user_requirement = """
    增强工作流创建API，支持将Solution作为步骤。
    需要更新数据模型支持Solution引用，验证Solution ID的存在性和有效性，
    支持混合步骤类型（Rule/Prompt和Solution），确保数据持久化正确。
    """
    
    # 执行评分
    results = engine.score_memory_items(user_requirement, memory_items)
    
    # 输出结果
    print("=== 记忆项目匹配度评分结果 ===\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title}")
        print(f"   总分: {result.total_score:.2f}")
        print(f"   置信度: {result.confidence:.1f}%")
        print(f"   关键优势: {', '.join(result.key_strengths)}")
        print(f"   匹配关键词: {', '.join(result.matched_keywords)}")
        print()
    
    # 添加反馈示例
    engine.add_user_feedback(
        memory_id="memory_001",
        query=user_requirement,
        rating=5,
        matched_keywords=["Solution", "unified", "service"],
        comment="完全符合需求"
    )
    
    # 获取统计信息
    stats = engine.get_scoring_statistics()
    print("=== 评分统计信息 ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # 保存矩阵
    engine.save_matrix("keyword_matrix.json")
    print("\n关键词矩阵已保存到 keyword_matrix.json")


if __name__ == "__main__":
    main() 