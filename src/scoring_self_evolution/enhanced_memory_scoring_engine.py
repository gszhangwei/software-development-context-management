#!/usr/bin/env python3
"""
增强记忆项目匹配度评分算法 - 自学习版本

基于用户需求和记忆项目内容，计算精准的匹配度评分，支持自学习和关键词自动发现。
"""

import re
import json
import uuid
import numpy as np
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from abc import ABC, abstractmethod
from enum import Enum
import math


class ChangeType(Enum):
    """变更类型枚举"""
    ADD_KEYWORD = "add_keyword"
    UPDATE_WEIGHT = "update_weight"
    REMOVE_KEYWORD = "remove_keyword"
    ADD_DIMENSION = "add_dimension"
    REMOVE_DIMENSION = "remove_dimension"
    AUTO_DISCOVERY = "auto_discovery"


class UpdateSource(Enum):
    """更新来源枚举"""
    USER_FEEDBACK = "user_feedback"
    EXPERT_ANNOTATION = "expert_annotation"
    AUTO_LEARNING = "auto_learning"
    PERFORMANCE_MONITORING = "performance_monitoring"
    KEYWORD_DISCOVERY = "keyword_discovery"
    STABILIZATION = "stabilization"


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
class KeywordStats:
    """关键词统计信息"""
    keyword: str
    dimension: str
    usage_count: int = 0
    match_count: int = 0
    total_score_contribution: float = 0.0
    avg_score_contribution: float = 0.0
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    weight_history: List[Tuple[datetime, float]] = field(default_factory=list)
    confidence: float = 0.0
    stability_score: float = 0.0


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


class RequirementAnalyzer:
    """需求分析器 - 增强版，支持自动关键词发现"""
    
    def __init__(self):
        self.api_operations_pattern = re.compile(
            r'\b(POST|GET|PUT|DELETE|PATCH|create|update|delete|query|search|fetch|list|retrieve)\b', 
            re.IGNORECASE
        )
        self.entity_pattern = re.compile(
            r'\b(Workflow|Solution|Rule|Prompt|Entity|Model|DTO|Service|Controller|Manager|Handler)\b'
        )
        self.functionality_pattern = re.compile(
            r'\b(validate|enhance|optimize|implement|design|configure|deploy|test|analyze|process|manage|handle)\b',
            re.IGNORECASE
        )
        
        # 技术词汇模式
        self.technical_pattern = re.compile(
            r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*|[a-z]+(?:-[a-z]+)+|\w+(?:API|Service|DTO|Entity|Model))\b'
        )
        
        # 停用词
        self.stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
    
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
    
    def discover_potential_keywords(self, text: str) -> Dict[str, List[str]]:
        """从文本中发现潜在的技术关键词"""
        discovered = {
            'technical_terms': [],
            'compound_words': [],
            'camel_case': [],
            'hyphenated': []
        }
        
        # 查找技术术语
        technical_matches = self.technical_pattern.findall(text)
        for match in technical_matches:
            if len(match) > 2 and match.lower() not in self.stop_words:
                if '-' in match:
                    discovered['hyphenated'].append(match)
                elif any(c.isupper() for c in match[1:]):
                    discovered['camel_case'].append(match)
                elif match.endswith(('API', 'Service', 'DTO', 'Entity', 'Model')):
                    discovered['technical_terms'].append(match)
                else:
                    discovered['compound_words'].append(match)
        
        # 去重并过滤
        for category in discovered:
            discovered[category] = list(set(discovered[category]))
            discovered[category] = [term for term in discovered[category] if len(term) > 2]
        
        return discovered


class SelfLearningKeywordMatrix:
    """自学习关键词匹配矩阵"""
    
    def __init__(self, version: str = "3.0.0"):
        self.version = version
        self.created_at = datetime.now()
        self.created_by = "self_learning_system"
        self.description = "Self-learning keyword matching matrix"
        
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
        
        # 关键词统计信息
        self.keyword_stats: Dict[str, KeywordStats] = {}
        self._initialize_keyword_stats()
        
        # 学习参数
        self.learning_rate = 0.05
        self.stabilization_threshold = 50  # 使用50次后开始稳定
        self.keyword_discovery_threshold = 0.7  # 发现新关键词的置信度阈值
        self.weight_decay = 0.99  # 权重衰减因子
        
        # 元数据
        self.metadata = {
            'total_keywords': sum(len(keywords) for keywords in self.matrix.values()),
            'dimensions': list(self.matrix.keys()),
            'avg_weights': {dim: np.mean(list(keywords.values())) 
                          for dim, keywords in self.matrix.items()},
            'validation_score': 0.0,
            'total_usage_count': 0,
            'discovered_keywords_count': 0
        }
        
        # 最大分数配置
        self.max_scores = {
            'api_enhancement': 25,
            'entity_support': 25,
            'data_model': 20,
            'validation': 15,
            'mixed_type': 15
        }
    
    def _initialize_keyword_stats(self):
        """初始化关键词统计信息"""
        for dimension, keywords in self.matrix.items():
            for keyword, weight in keywords.items():
                self.keyword_stats[f"{dimension}_{keyword}"] = KeywordStats(
                    keyword=keyword,
                    dimension=dimension,
                    weight_history=[(datetime.now(), weight)]
                )
    
    def get_keyword_weight(self, dimension: str, keyword: str) -> float:
        """获取关键词权重，支持自适应调整"""
        base_weight = self.matrix.get(dimension, {}).get(keyword, 0.0)
        
        # 根据使用统计调整权重
        stats_key = f"{dimension}_{keyword}"
        if stats_key in self.keyword_stats:
            stats = self.keyword_stats[stats_key]
            
            # 计算稳定性调整因子
            stability_factor = self._calculate_stability_factor(stats)
            
            # 计算性能调整因子
            performance_factor = self._calculate_performance_factor(stats)
            
            # 应用调整
            adjusted_weight = base_weight * stability_factor * performance_factor
            return max(0.1, min(adjusted_weight, 10))
        
        return base_weight
    
    def _calculate_stability_factor(self, stats: KeywordStats) -> float:
        """计算稳定性因子"""
        if stats.usage_count < self.stabilization_threshold:
            # 使用次数不足，应用学习率
            return 1.0 + (self.learning_rate * (stats.usage_count / self.stabilization_threshold))
        else:
            # 已稳定，权重变化减少
            return 1.0 + (self.learning_rate * 0.1)
    
    def _calculate_performance_factor(self, stats: KeywordStats) -> float:
        """计算性能因子"""
        if stats.match_count == 0:
            return 1.0
        
        # 基于平均贡献分数调整
        if stats.avg_score_contribution > 0.8:
            return 1.1  # 表现良好，增加权重
        elif stats.avg_score_contribution < 0.3:
            return 0.9  # 表现较差，减少权重
        else:
            return 1.0  # 表现一般，保持权重
    
    def update_keyword_weight(self, dimension: str, keyword: str, weight: float, reason: str = ""):
        """更新关键词权重并记录历史"""
        if dimension not in self.matrix:
            self.matrix[dimension] = {}
        
        old_weight = self.matrix[dimension].get(keyword, 0)
        new_weight = max(0, min(weight, 10))
        self.matrix[dimension][keyword] = new_weight
        
        # 更新统计信息
        stats_key = f"{dimension}_{keyword}"
        if stats_key not in self.keyword_stats:
            self.keyword_stats[stats_key] = KeywordStats(
                keyword=keyword,
                dimension=dimension
            )
        
        stats = self.keyword_stats[stats_key]
        stats.weight_history.append((datetime.now(), new_weight))
        stats.last_seen = datetime.now()
        
        # 限制历史记录长度
        if len(stats.weight_history) > 100:
            stats.weight_history = stats.weight_history[-50:]
    
    def add_discovered_keyword(self, dimension: str, keyword: str, initial_weight: float, confidence: float):
        """添加通过自动发现的新关键词"""
        if confidence < self.keyword_discovery_threshold:
            return False
        
        self.matrix[dimension][keyword] = initial_weight
        
        stats = KeywordStats(
            keyword=keyword,
            dimension=dimension,
            confidence=confidence,
            weight_history=[(datetime.now(), initial_weight)]
        )
        
        self.keyword_stats[f"{dimension}_{keyword}"] = stats
        self.metadata['total_keywords'] += 1
        self.metadata['discovered_keywords_count'] += 1
        
        return True
    
    def update_keyword_usage(self, dimension: str, keyword: str, score_contribution: float):
        """更新关键词使用统计"""
        stats_key = f"{dimension}_{keyword}"
        if stats_key in self.keyword_stats:
            stats = self.keyword_stats[stats_key]
            stats.usage_count += 1
            stats.match_count += 1
            stats.total_score_contribution += score_contribution
            stats.avg_score_contribution = stats.total_score_contribution / stats.match_count
            stats.last_seen = datetime.now()
            
            # 更新稳定性分数
            stats.stability_score = min(stats.usage_count / self.stabilization_threshold, 1.0)
        
        self.metadata['total_usage_count'] += 1
    
    def get_keyword_recommendations(self, discovered_keywords: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """基于发现的关键词生成推荐"""
        recommendations = []
        
        for category, keywords in discovered_keywords.items():
            for keyword in keywords:
                # 判断关键词应该属于哪个维度
                suggested_dimension = self._suggest_dimension_for_keyword(keyword)
                if suggested_dimension:
                    # 计算推荐权重
                    suggested_weight = self._calculate_suggested_weight(keyword, suggested_dimension)
                    
                    # 计算置信度
                    confidence = self._calculate_keyword_confidence(keyword, suggested_dimension)
                    
                    if confidence > 0.5:  # 只推荐置信度较高的关键词
                        recommendations.append({
                            'keyword': keyword,
                            'dimension': suggested_dimension,
                            'suggested_weight': suggested_weight,
                            'confidence': confidence,
                            'category': category,
                            'reason': f"Discovered from {category}, suggested for {suggested_dimension}"
                        })
        
        # 按置信度排序
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        return recommendations[:10]  # 返回前10个推荐
    
    def _suggest_dimension_for_keyword(self, keyword: str) -> Optional[str]:
        """为关键词建议合适的维度"""
        keyword_lower = keyword.lower()
        
        # API相关
        if any(term in keyword_lower for term in ['api', 'endpoint', 'controller', 'service', 'rest']):
            return 'api_enhancement'
        
        # 实体相关
        elif any(term in keyword_lower for term in ['entity', 'model', 'service', 'workflow', 'solution', 'rule']):
            return 'entity_support'
        
        # 数据模型相关
        elif any(term in keyword_lower for term in ['dto', 'request', 'response', 'schema', 'structure']):
            return 'data_model'
        
        # 验证相关
        elif any(term in keyword_lower for term in ['valid', 'check', 'verify', 'constraint']):
            return 'validation'
        
        # 混合类型相关
        elif any(term in keyword_lower for term in ['mixed', 'multi', 'batch', 'selector', 'routing']):
            return 'mixed_type'
        
        return None
    
    def _calculate_suggested_weight(self, keyword: str, dimension: str) -> float:
        """计算建议的关键词权重"""
        # 基于关键词的特征计算初始权重
        base_weight = 3.0  # 默认权重
        
        keyword_lower = keyword.lower()
        
        # 根据关键词的重要性特征调整权重
        if any(term in keyword_lower for term in ['unified', 'generic', 'solution', 'workflow']):
            base_weight += 2.0
        
        if keyword.endswith(('Service', 'Controller', 'Manager')):
            base_weight += 1.5
        
        if keyword.endswith(('DTO', 'Entity', 'Model')):
            base_weight += 1.0
        
        # 检查关键词长度和复杂度
        if len(keyword) > 10:
            base_weight += 0.5
        
        if any(c.isupper() for c in keyword[1:]):  # CamelCase
            base_weight += 0.5
        
        return max(1.0, min(base_weight, 8.0))
    
    def _calculate_keyword_confidence(self, keyword: str, dimension: str) -> float:
        """计算关键词置信度"""
        confidence = 0.5  # 基础置信度
        
        keyword_lower = keyword.lower()
        
        # 检查与现有关键词的相似性
        existing_keywords = self.matrix.get(dimension, {}).keys()
        for existing in existing_keywords:
            if existing.lower() in keyword_lower or keyword_lower in existing.lower():
                confidence += 0.2
                break
        
        # 检查技术术语特征
        if any(keyword.endswith(suffix) for suffix in ['Service', 'Controller', 'DTO', 'Entity', 'API']):
            confidence += 0.2
        
        # 检查命名约定
        if any(c.isupper() for c in keyword[1:]):  # CamelCase
            confidence += 0.1
        
        return min(confidence, 0.95)


class EnhancedContentAnalyzer:
    """增强的内容分析器，支持自学习"""
    
    def __init__(self, keyword_matrix: SelfLearningKeywordMatrix):
        self.keyword_matrix = keyword_matrix
        self.context_window = 50
        self.requirement_analyzer = RequirementAnalyzer()
    
    def calculate_semantic_score(self, content: str, dimension: str, user_requirement: str = "") -> Dict[str, Any]:
        """计算语义匹配分数，支持自动关键词发现"""
        content_lower = content.lower()
        keywords = self.keyword_matrix.matrix.get(dimension, {})
        
        score = 0
        matched_keywords = []
        keyword_positions = {}
        
        # 精确匹配
        for keyword, _ in keywords.items():
            if keyword.lower() in content_lower:
                # 获取自适应权重
                weight = self.keyword_matrix.get_keyword_weight(dimension, keyword)
                score += weight
                matched_keywords.append(keyword)
                
                # 更新关键词使用统计
                self.keyword_matrix.update_keyword_usage(dimension, keyword, weight)
                
                # 记录关键词位置
                positions = [m.start() for m in re.finditer(
                    re.escape(keyword.lower()), content_lower
                )]
                keyword_positions[keyword] = positions
        
        # 发现新关键词（如果提供了用户需求）
        discovered_keywords = {}
        new_keyword_score = 0
        if user_requirement:
            discovered_keywords = self._discover_keywords_in_content(
                content + " " + user_requirement, dimension
            )
            new_keyword_score = self._score_discovered_keywords(discovered_keywords, dimension)
        
        # 上下文匹配奖励
        context_bonus = self._calculate_context_bonus(keyword_positions)
        
        # 结构匹配奖励
        structure_bonus = self._calculate_structure_bonus(content, dimension)
        
        # 密度奖励
        density_bonus = self._calculate_density_bonus(matched_keywords, len(content))
        
        total_score = score + context_bonus + structure_bonus + density_bonus + new_keyword_score
        max_score = self.keyword_matrix.max_scores.get(dimension, 25)
        
        return {
            'raw_score': min(total_score, max_score),
            'max_score': max_score,
            'matched_keywords': matched_keywords,
            'context_bonus': context_bonus,
            'structure_bonus': structure_bonus,
            'density_bonus': density_bonus,
            'discovered_keywords': discovered_keywords,
            'new_keyword_score': new_keyword_score
        }
    
    def _discover_keywords_in_content(self, content: str, dimension: str) -> Dict[str, float]:
        """在内容中发现新关键词"""
        discovered = self.requirement_analyzer.discover_potential_keywords(content)
        relevant_keywords = {}
        
        for category, keywords in discovered.items():
            for keyword in keywords:
                # 检查关键词是否已存在
                if keyword not in self.keyword_matrix.matrix.get(dimension, {}):
                    # 检查是否适合当前维度
                    suggested_dim = self.keyword_matrix._suggest_dimension_for_keyword(keyword)
                    if suggested_dim == dimension:
                        confidence = self.keyword_matrix._calculate_keyword_confidence(keyword, dimension)
                        if confidence > 0.6:
                            relevant_keywords[keyword] = confidence
        
        return relevant_keywords
    
    def _score_discovered_keywords(self, discovered_keywords: Dict[str, float], dimension: str) -> float:
        """为发现的关键词计算分数贡献"""
        total_score = 0
        for keyword, confidence in discovered_keywords.items():
            # 计算临时权重
            temp_weight = self.keyword_matrix._calculate_suggested_weight(keyword, dimension)
            # 根据置信度调整分数
            score_contribution = temp_weight * confidence * 0.5  # 新关键词权重降低
            total_score += score_contribution
        
        return min(total_score, 5)  # 限制新关键词的最大贡献分数
    
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
        
        return min(bonus, 5)
    
    def _calculate_structure_bonus(self, content: str, dimension: str) -> float:
        """计算结构匹配奖励"""
        bonus = 0
        
        if dimension == 'data_model' and 'classDiagram' in content:
            bonus += 3
        
        if dimension == 'api_enhancement' and 'sequenceDiagram' in content:
            bonus += 3
        
        if '```' in content:
            bonus += 2
        
        if re.search(r'^[\s]*[-*+]', content, re.MULTILINE):
            bonus += 1
        
        return min(bonus, 4)
    
    def _calculate_density_bonus(self, matched_keywords: List[str], content_length: int) -> float:
        """计算关键词密度奖励"""
        if content_length == 0:
            return 0
        
        density = len(matched_keywords) / (content_length / 100)
        
        if density > 5:
            return 3
        elif density > 3:
            return 2
        elif density > 1:
            return 1
        else:
            return 0


class SelfLearningMemoryScoringEngine:
    """自学习记忆项目评分引擎"""
    
    def __init__(self, matrix_file: Optional[str] = None):
        self.keyword_matrix = self._load_or_create_matrix(matrix_file)
        self.requirement_analyzer = RequirementAnalyzer()
        self.weight_calculator = self._create_weight_calculator()
        self.content_analyzer = EnhancedContentAnalyzer(self.keyword_matrix)
        
        # 历史记录
        self.scoring_history: List[Dict] = []
        self.feedback_history: List[UserFeedback] = []
        self.discovered_keywords_log: List[Dict] = []
        
        # 学习参数
        self.auto_learning_enabled = True
        self.keyword_discovery_enabled = True
        self.stabilization_enabled = True
    
    def _load_or_create_matrix(self, matrix_file: Optional[str]) -> SelfLearningKeywordMatrix:
        """加载或创建自学习关键词矩阵"""
        if matrix_file and Path(matrix_file).exists():
            try:
                with open(matrix_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    matrix = SelfLearningKeywordMatrix(data.get('version', '3.0.0'))
                    matrix.matrix = data.get('matrix', {})
                    matrix.metadata = data.get('metadata', {})
                    
                    # 加载关键词统计信息
                    if 'keyword_stats' in data:
                        matrix.keyword_stats = {}
                        for key, stats_data in data['keyword_stats'].items():
                            stats = KeywordStats(
                                keyword=stats_data['keyword'],
                                dimension=stats_data['dimension'],
                                usage_count=stats_data.get('usage_count', 0),
                                match_count=stats_data.get('match_count', 0),
                                total_score_contribution=stats_data.get('total_score_contribution', 0.0),
                                avg_score_contribution=stats_data.get('avg_score_contribution', 0.0),
                                confidence=stats_data.get('confidence', 0.0),
                                stability_score=stats_data.get('stability_score', 0.0)
                            )
                            # 解析时间戳
                            if 'first_seen' in stats_data:
                                stats.first_seen = datetime.fromisoformat(stats_data['first_seen'])
                            if 'last_seen' in stats_data:
                                stats.last_seen = datetime.fromisoformat(stats_data['last_seen'])
                            
                            matrix.keyword_stats[key] = stats
                    
                    return matrix
            except Exception as e:
                print(f"Failed to load matrix file: {e}")
        
        return SelfLearningKeywordMatrix()
    
    def _create_weight_calculator(self):
        """创建权重计算器"""
        class AdaptiveWeightCalculator:
            def __init__(self, matrix):
                self.matrix = matrix
                self.base_weights = {
                    'api_enhancement': 25,
                    'entity_support': 25,
                    'data_model': 20,
                    'validation': 15,
                    'mixed_type': 15
                }
            
            def calculate_weights(self, requirements: UserRequirement) -> Dict[str, float]:
                weights = self.base_weights.copy()
                
                # 根据关键词统计信息调整权重
                total_usage = self.matrix.metadata.get('total_usage_count', 1)
                for dimension in weights:
                    # 计算该维度关键词的平均使用率
                    dimension_usage = sum(
                        stats.usage_count for key, stats in self.matrix.keyword_stats.items()
                        if stats.dimension == dimension
                    )
                    
                    if total_usage > 0:
                        usage_ratio = dimension_usage / total_usage
                        # 根据使用情况微调权重
                        if usage_ratio > 0.3:
                            weights[dimension] *= 1.1
                        elif usage_ratio < 0.1:
                            weights[dimension] *= 0.9
                
                # 标准化权重
                total = sum(weights.values())
                return {k: (v / total) * 100 for k, v in weights.items()}
        
        return AdaptiveWeightCalculator(self.keyword_matrix)
    
    def score_memory_items(self, user_requirement: str, 
                          memory_items: List[MemoryItem]) -> List[ScoringResult]:
        """评分记忆项目列表，支持自学习"""
        # 分析用户需求
        requirements = self.requirement_analyzer.extract_requirements(user_requirement)
        
        # 发现新关键词
        if self.keyword_discovery_enabled:
            self._discover_and_add_keywords(user_requirement, memory_items)
        
        # 计算动态权重
        weights = self.weight_calculator.calculate_weights(requirements)
        
        results = []
        for memory_item in memory_items:
            result = self._score_single_memory(memory_item, requirements, weights, user_requirement)
            results.append(result)
        
        # 按总分排序
        results.sort(key=lambda x: x.total_score, reverse=True)
        
        # 记录评分历史
        self._record_scoring_session(user_requirement, requirements, weights, results)
        
        # 自动稳定化（如果启用）
        if self.stabilization_enabled:
            self._apply_stabilization()
        
        return results
    
    def _discover_and_add_keywords(self, user_requirement: str, memory_items: List[MemoryItem]):
        """发现并添加新关键词"""
        all_text = user_requirement + " "
        for item in memory_items:
            all_text += f"{item.title} {item.content} "
        
        # 发现潜在关键词
        discovered = self.requirement_analyzer.discover_potential_keywords(all_text)
        
        # 获取推荐
        recommendations = self.keyword_matrix.get_keyword_recommendations(discovered)
        
        # 自动添加高置信度的关键词
        added_keywords = []
        for rec in recommendations:
            if rec['confidence'] > self.keyword_matrix.keyword_discovery_threshold:
                success = self.keyword_matrix.add_discovered_keyword(
                    rec['dimension'], 
                    rec['keyword'], 
                    rec['suggested_weight'], 
                    rec['confidence']
                )
                if success:
                    added_keywords.append(rec)
        
        # 记录发现的关键词
        if added_keywords:
            self.discovered_keywords_log.append({
                'timestamp': datetime.now().isoformat(),
                'user_requirement': user_requirement,
                'added_keywords': added_keywords,
                'total_discovered': len(recommendations)
            })
    
    def _score_single_memory(self, memory_item: MemoryItem, 
                           requirements: UserRequirement, 
                           weights: Dict[str, float],
                           user_requirement: str) -> ScoringResult:
        """评分单个记忆项目"""
        score_breakdown = {}
        total_weighted_score = 0
        all_matched_keywords = []
        
        # 对每个维度进行评分
        for dimension in self.keyword_matrix.matrix.keys():
            dimension_result = self.content_analyzer.calculate_semantic_score(
                memory_item.content, dimension, user_requirement
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
                'matched_keywords': dimension_result['matched_keywords'],
                'discovered_keywords': dimension_result.get('discovered_keywords', {}),
                'new_keyword_score': dimension_result.get('new_keyword_score', 0)
            }
            
            all_matched_keywords.extend(dimension_result['matched_keywords'])
        
        # 计算置信度
        confidence = self._calculate_confidence(score_breakdown, len(memory_item.content), all_matched_keywords)
        
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
    
    def _calculate_confidence(self, score_breakdown: Dict[str, Dict], 
                            content_length: int, matched_keywords: List[str]) -> float:
        """计算置信度"""
        # 基于覆盖度的置信度
        coverage = sum(1 for scores in score_breakdown.values() 
                      if scores['raw_score'] > 0) / len(score_breakdown)
        
        # 基于内容长度的置信度
        length_factor = min(content_length / 1000, 1.0)
        
        # 基于关键词匹配数量的置信度
        keyword_factor = min(len(matched_keywords) / 10, 1.0)
        
        # 基于矩阵稳定性的置信度
        stability_factor = min(self.keyword_matrix.metadata.get('total_usage_count', 1) / 100, 1.0)
        
        # 综合置信度
        confidence = (coverage * 0.4 + length_factor * 0.2 + keyword_factor * 0.2 + stability_factor * 0.2) * 100
        
        return min(confidence, 95)
    
    def _identify_key_strengths(self, score_breakdown: Dict[str, Dict], 
                              memory_item: MemoryItem) -> List[str]:
        """识别记忆项目的关键优势"""
        strengths = []
        
        for dimension, scores in score_breakdown.items():
            if scores['weighted_score'] > scores['weight'] * 0.8:
                matched_keywords = scores['matched_keywords']
                if matched_keywords:
                    strength_desc = f"{dimension.replace('_', ' ').title()}: {', '.join(matched_keywords[:3])}"
                    strengths.append(strength_desc)
                
                # 添加新发现的关键词作为优势
                discovered = scores.get('discovered_keywords', {})
                if discovered:
                    top_discovered = sorted(discovered.items(), key=lambda x: x[1], reverse=True)[:2]
                    if top_discovered:
                        discovered_desc = f"Discovered in {dimension}: {', '.join([k for k, _ in top_discovered])}"
                        strengths.append(discovered_desc)
        
        return strengths[:5]
    
    def _apply_stabilization(self):
        """应用权重稳定化"""
        total_usage = self.keyword_matrix.metadata.get('total_usage_count', 0)
        
        if total_usage > self.keyword_matrix.stabilization_threshold:
            for stats_key, stats in self.keyword_matrix.keyword_stats.items():
                if stats.usage_count >= self.keyword_matrix.stabilization_threshold:
                    # 计算稳定化后的权重
                    current_weight = self.keyword_matrix.matrix[stats.dimension][stats.keyword]
                    
                    # 基于性能历史调整权重
                    if stats.avg_score_contribution > 0.7:
                        # 表现良好，适度增加权重
                        stabilized_weight = current_weight * 1.05
                    elif stats.avg_score_contribution < 0.3:
                        # 表现较差，适度减少权重
                        stabilized_weight = current_weight * 0.95
                    else:
                        # 表现一般，保持权重
                        stabilized_weight = current_weight
                    
                    # 应用权重衰减
                    stabilized_weight *= self.keyword_matrix.weight_decay
                    
                    # 更新权重
                    self.keyword_matrix.update_keyword_weight(
                        stats.dimension, 
                        stats.keyword, 
                        stabilized_weight, 
                        "Automatic stabilization"
                    )
    
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
            'algorithm_version': '3.0.0',
            'matrix_usage_count': self.keyword_matrix.metadata.get('total_usage_count', 0),
            'discovered_keywords_count': self.keyword_matrix.metadata.get('discovered_keywords_count', 0)
        }
        self.scoring_history.append(session)
    
    def add_user_feedback(self, memory_id: str, query: str, rating: int, 
                         matched_keywords: List[str], comment: str = ""):
        """添加用户反馈并触发学习"""
        feedback = UserFeedback(
            memory_id=memory_id,
            query=query,
            rating=rating,
            matched_keywords=matched_keywords,
            comment=comment
        )
        self.feedback_history.append(feedback)
        
        # 基于反馈调整关键词权重
        if self.auto_learning_enabled:
            self._learn_from_feedback(feedback)
    
    def _learn_from_feedback(self, feedback: UserFeedback):
        """从用户反馈中学习"""
        for keyword in feedback.matched_keywords:
            # 找到关键词所属维度
            dimension = None
            for dim, keywords in self.keyword_matrix.matrix.items():
                if keyword in keywords:
                    dimension = dim
                    break
            
            if dimension:
                current_weight = self.keyword_matrix.get_keyword_weight(dimension, keyword)
                
                # 根据评分调整权重
                if feedback.rating >= 4:
                    # 正面反馈，适度增加权重
                    adjustment = self.keyword_matrix.learning_rate * 0.5
                    new_weight = min(current_weight + adjustment, 10)
                elif feedback.rating <= 2:
                    # 负面反馈，适度减少权重
                    adjustment = self.keyword_matrix.learning_rate * 0.5
                    new_weight = max(current_weight - adjustment, 0.1)
                else:
                    # 中性反馈，保持权重
                    new_weight = current_weight
                
                # 更新权重
                self.keyword_matrix.update_keyword_weight(
                    dimension, 
                    keyword, 
                    new_weight, 
                    f"User feedback: rating={feedback.rating}"
                )
    
    def save_matrix(self, file_path: str):
        """保存自学习关键词矩阵"""
        # 转换关键词统计信息为可序列化格式
        serializable_stats = {}
        for key, stats in self.keyword_matrix.keyword_stats.items():
            serializable_stats[key] = {
                'keyword': stats.keyword,
                'dimension': stats.dimension,
                'usage_count': stats.usage_count,
                'match_count': stats.match_count,
                'total_score_contribution': stats.total_score_contribution,
                'avg_score_contribution': stats.avg_score_contribution,
                'first_seen': stats.first_seen.isoformat(),
                'last_seen': stats.last_seen.isoformat(),
                'confidence': stats.confidence,
                'stability_score': stats.stability_score
            }
        
        data = {
            'version': self.keyword_matrix.version,
            'created_at': self.keyword_matrix.created_at.isoformat(),
            'created_by': self.keyword_matrix.created_by,
            'description': self.keyword_matrix.description,
            'matrix': self.keyword_matrix.matrix,
            'metadata': self.keyword_matrix.metadata,
            'max_scores': self.keyword_matrix.max_scores,
            'keyword_stats': serializable_stats,
            'learning_parameters': {
                'learning_rate': self.keyword_matrix.learning_rate,
                'stabilization_threshold': self.keyword_matrix.stabilization_threshold,
                'keyword_discovery_threshold': self.keyword_matrix.keyword_discovery_threshold,
                'weight_decay': self.keyword_matrix.weight_decay
            },
            'scoring_history': self.scoring_history,
            'discovered_keywords_log': self.discovered_keywords_log
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        total_sessions = len(self.scoring_history)
        total_usage = self.keyword_matrix.metadata.get('total_usage_count', 0)
        discovered_count = self.keyword_matrix.metadata.get('discovered_keywords_count', 0)
        
        # 计算稳定关键词数量
        stable_keywords = sum(
            1 for stats in self.keyword_matrix.keyword_stats.values()
            if stats.stability_score >= 0.8
        )
        
        # 计算平均权重变化
        weight_changes = []
        for stats in self.keyword_matrix.keyword_stats.values():
            if len(stats.weight_history) > 1:
                initial_weight = stats.weight_history[0][1]
                current_weight = stats.weight_history[-1][1]
                change = abs(current_weight - initial_weight)
                weight_changes.append(change)
        
        avg_weight_change = np.mean(weight_changes) if weight_changes else 0
        
        return {
            'total_scoring_sessions': total_sessions,
            'total_keyword_usage': total_usage,
            'discovered_keywords': discovered_count,
            'stable_keywords': stable_keywords,
            'total_keywords': self.keyword_matrix.metadata.get('total_keywords', 0),
            'average_weight_change': avg_weight_change,
            'feedback_count': len(self.feedback_history),
            'matrix_version': self.keyword_matrix.version,
            'learning_enabled': self.auto_learning_enabled,
            'discovery_enabled': self.keyword_discovery_enabled,
            'stabilization_enabled': self.stabilization_enabled
        }
    
    def get_keyword_evolution_report(self) -> Dict[str, Any]:
        """获取关键词演化报告"""
        evolution_report = {
            'top_performing_keywords': [],
            'newly_discovered_keywords': [],
            'most_stable_keywords': [],
            'weight_evolution_summary': {}
        }
        
        # 获取表现最好的关键词
        performing_keywords = sorted(
            self.keyword_matrix.keyword_stats.values(),
            key=lambda x: x.avg_score_contribution,
            reverse=True
        )[:10]
        
        evolution_report['top_performing_keywords'] = [
            {
                'keyword': kw.keyword,
                'dimension': kw.dimension,
                'avg_contribution': kw.avg_score_contribution,
                'usage_count': kw.usage_count
            }
            for kw in performing_keywords
        ]
        
        # 获取最近发现的关键词
        recent_discoveries = [
            log for log in self.discovered_keywords_log
            if datetime.fromisoformat(log['timestamp']) > datetime.now() - timedelta(days=30)
        ]
        
        newly_discovered = []
        for log in recent_discoveries:
            for kw in log['added_keywords']:
                newly_discovered.append({
                    'keyword': kw['keyword'],
                    'dimension': kw['dimension'],
                    'confidence': kw['confidence'],
                    'discovered_at': log['timestamp']
                })
        
        evolution_report['newly_discovered_keywords'] = newly_discovered
        
        # 获取最稳定的关键词
        stable_keywords = sorted(
            self.keyword_matrix.keyword_stats.values(),
            key=lambda x: x.stability_score,
            reverse=True
        )[:10]
        
        evolution_report['most_stable_keywords'] = [
            {
                'keyword': kw.keyword,
                'dimension': kw.dimension,
                'stability_score': kw.stability_score,
                'usage_count': kw.usage_count
            }
            for kw in stable_keywords
        ]
        
        # 权重演化摘要
        for dimension in self.keyword_matrix.matrix.keys():
            dimension_stats = [
                stats for stats in self.keyword_matrix.keyword_stats.values()
                if stats.dimension == dimension
            ]
            
            if dimension_stats:
                avg_stability = np.mean([s.stability_score for s in dimension_stats])
                avg_usage = np.mean([s.usage_count for s in dimension_stats])
                avg_contribution = np.mean([s.avg_score_contribution for s in dimension_stats])
                
                evolution_report['weight_evolution_summary'][dimension] = {
                    'average_stability': avg_stability,
                    'average_usage': avg_usage,
                    'average_contribution': avg_contribution,
                    'keyword_count': len(dimension_stats)
                }
        
        return evolution_report


def main():
    """主函数 - 演示自学习功能"""
    # 创建自学习评分引擎
    engine = SelfLearningMemoryScoringEngine()
    
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
            - **新增工作流集成**: WorkflowIntegrationService支持多类型步骤管理
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
            4. **新增Solution验证**: SolutionValidationService验证Solution步骤
            5. **跨类型依赖检查**: CrossTypeValidator确保混合步骤的兼容性
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
    实现SolutionStepProcessor处理Solution类型的步骤，
    添加CrossTypeValidator进行跨类型验证。
    """
    
    # 执行评分
    print("=== 自学习记忆项目匹配度评分结果 ===\n")
    results = engine.score_memory_items(user_requirement, memory_items)
    
    # 输出结果
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title}")
        print(f"   总分: {result.total_score:.2f}")
        print(f"   置信度: {result.confidence:.1f}%")
        print(f"   关键优势: {', '.join(result.key_strengths)}")
        print(f"   匹配关键词: {', '.join(result.matched_keywords)}")
        
        # 显示发现的新关键词
        discovered_any = False
        for dimension, scores in result.score_breakdown.items():
            discovered = scores.get('discovered_keywords', {})
            if discovered:
                if not discovered_any:
                    print(f"   发现的新关键词:")
                    discovered_any = True
                print(f"     {dimension}: {list(discovered.keys())}")
        print()
    
    # 模拟多次调用以演示学习过程
    print("=== 模拟多次调用演示学习过程 ===\n")
    
    for i in range(5):
        # 稍微修改需求以模拟不同的查询
        modified_requirement = user_requirement + f" 第{i+1}次查询优化。"
        results = engine.score_memory_items(modified_requirement, memory_items)
        
        # 添加模拟反馈
        if results:
            engine.add_user_feedback(
                memory_id=results[0].memory_id,
                query=modified_requirement,
                rating=4 if i % 2 == 0 else 5,
                matched_keywords=results[0].matched_keywords[:3],
                comment=f"第{i+1}次反馈"
            )
    
    # 获取学习统计信息
    learning_stats = engine.get_learning_statistics()
    print("=== 学习统计信息 ===")
    for key, value in learning_stats.items():
        print(f"{key}: {value}")
    print()
    
    # 获取关键词演化报告
    evolution_report = engine.get_keyword_evolution_report()
    print("=== 关键词演化报告 ===")
    
    print("表现最好的关键词:")
    for kw in evolution_report['top_performing_keywords'][:5]:
        print(f"  {kw['keyword']} ({kw['dimension']}): 贡献度={kw['avg_contribution']:.3f}, 使用次数={kw['usage_count']}")
    
    print("\n新发现的关键词:")
    for kw in evolution_report['newly_discovered_keywords'][:5]:
        print(f"  {kw['keyword']} ({kw['dimension']}): 置信度={kw['confidence']:.3f}")
    
    print("\n最稳定的关键词:")
    for kw in evolution_report['most_stable_keywords'][:5]:
        print(f"  {kw['keyword']} ({kw['dimension']}): 稳定性={kw['stability_score']:.3f}")
    
    # 保存矩阵
    engine.save_matrix("self_learning_keyword_matrix.json")
    print("\n自学习关键词矩阵已保存到 self_learning_keyword_matrix.json")


if __name__ == "__main__":
    main() 