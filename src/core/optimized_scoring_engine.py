#!/usr/bin/env python3
"""
优化的记忆评分引擎

针对团队记忆管理的性能优化版本，包含：
1. 评分结果缓存机制
2. 预计算关键词权重
3. 异步评分支持
4. 批量评分优化
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import threading

from .markdown_engine import MemoryEntry


@dataclass
class CachedScore:
    """缓存的评分结果"""
    score: float
    confidence: float
    matched_keywords: List[str]
    key_strengths: List[str]
    timestamp: datetime
    hit_count: int = 0
    
    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """检查缓存是否过期"""
        return (datetime.now() - self.timestamp).seconds > ttl_seconds


@dataclass 
class PrecomputedWeight:
    """预计算的关键词权重"""
    keyword: str
    dimension: str
    weight: float
    confidence: float
    last_updated: datetime
    usage_frequency: int = 0


class OptimizedScoringEngine:
    """优化的记忆评分引擎"""
    
    def __init__(self, cache_dir: Path = None, max_cache_size: int = 1000):
        """
        初始化优化评分引擎
        
        Args:
            cache_dir: 缓存目录
            max_cache_size: 最大缓存大小
        """
        self.cache_dir = cache_dir or Path(".scoring_cache")
        self.max_cache_size = max_cache_size
        
        # 内存缓存
        self._score_cache: Dict[str, CachedScore] = {}
        self._precomputed_weights: Dict[str, PrecomputedWeight] = {}
        self._cache_lock = threading.RLock()
        
        # 性能统计
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_queries': 0,
            'avg_response_time': 0.0,
            'precomputed_weight_hits': 0
        }
        
        # 线程池用于异步评分
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # 初始化
        self._load_cache()
        self._load_precomputed_weights()
        
        # 增强评分引擎（可选）
        self._enhanced_engine = None
        self._try_load_enhanced_engine()
    
    def _try_load_enhanced_engine(self):
        """尝试加载增强评分引擎"""
        try:
            from src.scoring_self_evolution import SelfLearningMemoryScoringEngine
            self._enhanced_engine = SelfLearningMemoryScoringEngine()
        except ImportError:
            pass
    
    def _generate_cache_key(self, user_message: str, memory_id: str) -> str:
        """生成缓存键"""
        content = f"{user_message}:{memory_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _load_cache(self):
        """从磁盘加载缓存"""
        cache_file = self.cache_dir / "score_cache.json"
        if not cache_file.exists():
            return
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            for key, data in cache_data.items():
                self._score_cache[key] = CachedScore(
                    score=data['score'],
                    confidence=data['confidence'],
                    matched_keywords=data['matched_keywords'],
                    key_strengths=data['key_strengths'],
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    hit_count=data.get('hit_count', 0)
                )
        except Exception as e:
            print(f"⚠️ 加载评分缓存失败: {e}")
    
    def _save_cache(self):
        """保存缓存到磁盘"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / "score_cache.json"
        
        try:
            cache_data = {}
            for key, cached_score in self._score_cache.items():
                cache_data[key] = {
                    'score': cached_score.score,
                    'confidence': cached_score.confidence,
                    'matched_keywords': cached_score.matched_keywords,
                    'key_strengths': cached_score.key_strengths,
                    'timestamp': cached_score.timestamp.isoformat(),
                    'hit_count': cached_score.hit_count
                }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 保存评分缓存失败: {e}")
    
    def _load_precomputed_weights(self):
        """加载预计算权重"""
        weights_file = self.cache_dir / "precomputed_weights.json"
        if not weights_file.exists():
            self._initialize_default_weights()
            return
        
        try:
            with open(weights_file, 'r', encoding='utf-8') as f:
                weights_data = json.load(f)
            
            for key, data in weights_data.items():
                self._precomputed_weights[key] = PrecomputedWeight(
                    keyword=data['keyword'],
                    dimension=data['dimension'],
                    weight=data['weight'],
                    confidence=data['confidence'],
                    last_updated=datetime.fromisoformat(data['last_updated']),
                    usage_frequency=data.get('usage_frequency', 0)
                )
        except Exception as e:
            print(f"⚠️ 加载预计算权重失败: {e}")
            self._initialize_default_weights()
    
    def _initialize_default_weights(self):
        """初始化默认权重"""
        default_weights = {
            # 高权重技术关键词
            'api': {'dimension': 'technical', 'weight': 3.5, 'confidence': 0.9},
            'workflow': {'dimension': 'business', 'weight': 3.0, 'confidence': 0.9},
            'authentication': {'dimension': 'security', 'weight': 3.2, 'confidence': 0.8},
            'database': {'dimension': 'technical', 'weight': 2.8, 'confidence': 0.9},
            'validation': {'dimension': 'quality', 'weight': 2.5, 'confidence': 0.8},
            
            # 中权重业务关键词
            'management': {'dimension': 'business', 'weight': 2.0, 'confidence': 0.7},
            'service': {'dimension': 'technical', 'weight': 2.2, 'confidence': 0.8},
            'architecture': {'dimension': 'design', 'weight': 2.8, 'confidence': 0.9},
            'implementation': {'dimension': 'development', 'weight': 2.3, 'confidence': 0.8},
            
            # 低权重通用关键词
            'design': {'dimension': 'design', 'weight': 1.5, 'confidence': 0.6},
            'model': {'dimension': 'design', 'weight': 1.8, 'confidence': 0.7},
            'configuration': {'dimension': 'technical', 'weight': 1.5, 'confidence': 0.7}
        }
        
        for keyword, data in default_weights.items():
            key = f"{data['dimension']}:{keyword}"
            self._precomputed_weights[key] = PrecomputedWeight(
                keyword=keyword,
                dimension=data['dimension'],
                weight=data['weight'],
                confidence=data['confidence'],
                last_updated=datetime.now()
            )
    
    def _save_precomputed_weights(self):
        """保存预计算权重"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        weights_file = self.cache_dir / "precomputed_weights.json"
        
        try:
            weights_data = {}
            for key, weight in self._precomputed_weights.items():
                weights_data[key] = {
                    'keyword': weight.keyword,
                    'dimension': weight.dimension,
                    'weight': weight.weight,
                    'confidence': weight.confidence,
                    'last_updated': weight.last_updated.isoformat(),
                    'usage_frequency': weight.usage_frequency
                }
            
            with open(weights_file, 'w', encoding='utf-8') as f:
                json.dump(weights_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 保存预计算权重失败: {e}")
    
    def get_precomputed_weight(self, keyword: str, dimension: str = 'technical') -> float:
        """获取预计算权重"""
        key = f"{dimension}:{keyword.lower()}"
        
        with self._cache_lock:
            if key in self._precomputed_weights:
                weight_obj = self._precomputed_weights[key]
                weight_obj.usage_frequency += 1
                self._stats['precomputed_weight_hits'] += 1
                return weight_obj.weight
        
        # 如果没有预计算权重，返回默认值
        return 1.0
    
    def calculate_memory_score(self, user_message: str, memory: MemoryEntry, 
                             use_cache: bool = True) -> Tuple[float, Dict]:
        """
        计算记忆评分（优化版本）
        
        Args:
            user_message: 用户消息
            memory: 记忆条目
            use_cache: 是否使用缓存
            
        Returns:
            评分和详细信息的元组
        """
        start_time = time.time()
        self._stats['total_queries'] += 1
        
        # 生成缓存键
        cache_key = self._generate_cache_key(user_message, memory.id)
        
        # 检查缓存
        if use_cache:
            with self._cache_lock:
                if cache_key in self._score_cache:
                    cached = self._score_cache[cache_key]
                    if not cached.is_expired():
                        cached.hit_count += 1
                        self._stats['cache_hits'] += 1
                        
                        return cached.score, {
                            'confidence': cached.confidence,
                            'matched_keywords': cached.matched_keywords,
                            'key_strengths': cached.key_strengths,
                            'cached': True
                        }
        
        self._stats['cache_misses'] += 1
        
        # 尝试使用增强评分引擎
        if self._enhanced_engine:
            try:
                score, details = self._calculate_enhanced_score(user_message, memory)
            except Exception as e:
                print(f"⚠️ 增强评分失败，使用优化评分: {e}")
                score, details = self._calculate_optimized_score(user_message, memory)
        else:
            score, details = self._calculate_optimized_score(user_message, memory)
        
        # 缓存结果
        if use_cache:
            with self._cache_lock:
                # 清理过期缓存
                self._cleanup_expired_cache()
                
                # 添加新缓存
                if len(self._score_cache) < self.max_cache_size:
                    self._score_cache[cache_key] = CachedScore(
                        score=score,
                        confidence=details.get('confidence', 0.8),
                        matched_keywords=details.get('matched_keywords', []),
                        key_strengths=details.get('key_strengths', []),
                        timestamp=datetime.now()
                    )
        
        # 更新性能统计
        response_time = time.time() - start_time
        self._stats['avg_response_time'] = (
            (self._stats['avg_response_time'] * (self._stats['total_queries'] - 1) + response_time) 
            / self._stats['total_queries']
        )
        
        details['cached'] = False
        return score, details
    
    def _calculate_enhanced_score(self, user_message: str, memory: MemoryEntry) -> Tuple[float, Dict]:
        """使用增强评分引擎计算分数"""
        from src.scoring_self_evolution import MemoryItem
        
        memory_item = MemoryItem(
            id=memory.id,
            title=getattr(memory, 'title', memory.id),
            content=memory.content,
            tags=memory.tags,
            project=memory.project,
            importance=memory.importance
        )
        
        results = self._enhanced_engine.score_memory_items(user_message, [memory_item])
        
        if results:
            result = results[0]
            return result.total_score, {
                'confidence': result.confidence,
                'matched_keywords': result.matched_keywords,
                'key_strengths': result.key_strengths,
                'score_breakdown': result.score_breakdown
            }
        
        return 0.0, {'confidence': 0.0, 'matched_keywords': [], 'key_strengths': []}
    
    def _calculate_optimized_score(self, user_message: str, memory: MemoryEntry) -> Tuple[float, Dict]:
        """使用优化算法计算分数"""
        score = 0.0
        matched_keywords = []
        key_strengths = []
        
        # 提取关键词
        message_keywords = self._extract_keywords(user_message.lower())
        memory_content_lower = memory.content.lower()
        memory_tags_lower = [tag.lower() for tag in memory.tags]
        
        # 1. 标签匹配（使用预计算权重）
        tag_score = 0.0
        for tag in memory_tags_lower:
            for keyword in message_keywords:
                if keyword in tag or tag in keyword:
                    weight = self.get_precomputed_weight(keyword, 'tag')
                    tag_score += weight * 2.0  # 标签匹配权重较高
                    matched_keywords.append(keyword)
        
        # 2. 内容匹配（使用预计算权重）
        content_score = 0.0
        for keyword in message_keywords:
            if keyword in memory_content_lower:
                weight = self.get_precomputed_weight(keyword, 'content')
                content_score += weight * 1.5
                matched_keywords.append(keyword)
        
        # 3. 项目匹配
        project_score = 0.0
        if memory.project and memory.project.lower() != 'general':
            project_lower = memory.project.lower()
            for keyword in message_keywords:
                if keyword in project_lower:
                    project_score += 1.0
                    matched_keywords.append(keyword)
        
        # 4. 重要性加权
        importance_multiplier = memory.importance / 3.0
        
        # 计算总分
        total_score = (tag_score + content_score + project_score) * importance_multiplier
        
        # 确定关键优势
        if tag_score > 2.0:
            key_strengths.append("strong_tag_match")
        if content_score > 3.0:
            key_strengths.append("strong_content_match")
        if project_score > 0:
            key_strengths.append("project_relevance")
        if memory.importance >= 4:
            key_strengths.append("high_importance")
        
        # 计算置信度
        confidence = min(1.0, (len(matched_keywords) * 0.2 + memory.importance * 0.1))
        
        return total_score, {
            'confidence': confidence,
            'matched_keywords': list(set(matched_keywords)),
            'key_strengths': key_strengths,
            'score_components': {
                'tag_score': tag_score,
                'content_score': content_score,
                'project_score': project_score,
                'importance_multiplier': importance_multiplier
            }
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（优化版本）"""
        import re
        
        # 使用预定义的技术关键词模式
        tech_patterns = [
            r'\b(?:api|workflow|database|service|authentication|authorization)\b',
            r'\b(?:management|architecture|implementation|configuration)\b',
            r'\b(?:validation|design|model|framework|solution)\b'
        ]
        
        keywords = set()
        
        # 提取技术关键词
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.update(match.lower() for match in matches)
        
        # 提取英文单词（长度>=3）
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        keywords.update(word.lower() for word in english_words)
        
        return list(keywords)
    
    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        expired_keys = [
            key for key, cached_score in self._score_cache.items()
            if cached_score.is_expired()
        ]
        
        for key in expired_keys:
            del self._score_cache[key]
    
    async def calculate_memory_score_async(self, user_message: str, memory: MemoryEntry) -> Tuple[float, Dict]:
        """异步计算记忆评分"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            self.calculate_memory_score, 
            user_message, 
            memory
        )
    
    def batch_calculate_scores(self, user_message: str, memories: List[MemoryEntry], 
                             max_workers: int = 4) -> List[Tuple[str, float, Dict]]:
        """批量计算评分"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_memory = {
                executor.submit(self.calculate_memory_score, user_message, memory): memory
                for memory in memories
            }
            
            for future in future_to_memory:
                memory = future_to_memory[future]
                try:
                    score, details = future.result()
                    results.append((memory.id, score, details))
                except Exception as e:
                    print(f"⚠️ 评分失败 {memory.id}: {e}")
                    results.append((memory.id, 0.0, {'error': str(e)}))
        
        return results
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        cache_hit_rate = (
            self._stats['cache_hits'] / max(1, self._stats['total_queries'])
        ) * 100
        
        return {
            **self._stats,
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'cache_size': len(self._score_cache),
            'precomputed_weights_count': len(self._precomputed_weights),
            'uptime': datetime.now().isoformat()
        }
    
    def update_keyword_weight(self, keyword: str, dimension: str, new_weight: float, confidence: float = 0.8):
        """更新关键词权重"""
        key = f"{dimension}:{keyword.lower()}"
        
        with self._cache_lock:
            self._precomputed_weights[key] = PrecomputedWeight(
                keyword=keyword.lower(),
                dimension=dimension,
                weight=new_weight,
                confidence=confidence,
                last_updated=datetime.now()
            )
    
    def save_state(self):
        """保存引擎状态"""
        self._save_cache()
        self._save_precomputed_weights()
    
    def __del__(self):
        """析构函数，保存状态"""
        try:
            self.save_state()
            if hasattr(self, '_executor'):
                self._executor.shutdown(wait=False)
        except:
            pass