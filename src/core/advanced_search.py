"""
ContextX高级记忆搜索引擎

提供智能的记忆搜索和语义匹配功能，包括：
- 基于TF-IDF的文本相似度计算
- 语义关键词扩展和同义词匹配
- 智能记忆推荐和关联分析
- 多维度搜索结果排序
"""

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set

from .directory_manager import DirectoryManager
from .markdown_engine import MarkdownEngine, MemoryEntry


@dataclass
class SearchResult:
    """搜索结果"""
    memory: MemoryEntry
    relevance_score: float
    match_type: str  # exact, semantic, tag, related
    matched_terms: List[str] = field(default_factory=list)
    context_snippet: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'memory_id': self.memory.id,
            'content': self.memory.content,
            'tags': self.memory.tags,
            'project': self.memory.project,
            'importance': self.memory.importance,
            'timestamp': self.memory.timestamp,
            'relevance_score': self.relevance_score,
            'match_type': self.match_type,
            'matched_terms': self.matched_terms,
            'context_snippet': self.context_snippet
        }


@dataclass
class SearchConfig:
    """搜索配置"""
    query: str
    team_name: str
    search_types: List[str] = field(default_factory=lambda: ['exact', 'semantic', 'tag'])
    max_results: int = 20
    min_relevance: float = 0.1
    include_related: bool = True
    boost_recent: bool = True
    boost_important: bool = True
    project_filter: Optional[str] = None
    tag_filter: Optional[List[str]] = None
    date_range: Optional[Tuple[str, str]] = None


class AdvancedSearchEngine:
    """高级记忆搜索引擎"""
    
    def __init__(self, base_path: Path):
        """
        初始化搜索引擎
        
        Args:
            base_path: 团队数据根目录
        """
        self.base_path = Path(base_path)
        self.directory_manager = DirectoryManager(base_path)
        self.markdown_engine = MarkdownEngine()
        
        # 初始化词汇表和索引
        self.vocabulary: Set[str] = set()
        self.idf_scores: Dict[str, float] = {}
        self.memory_index: Dict[str, Dict[str, Any]] = {}
        
        # 语义相关词典
        self.semantic_relations = self._load_semantic_relations()
        
        # 缓存
        self._search_cache: Dict[str, List[SearchResult]] = {}
        self._cache_ttl = 300  # 5分钟缓存
        self._last_index_update = 0
    
    def search_memories(self, config: SearchConfig) -> List[SearchResult]:
        """
        执行高级记忆搜索
        
        Args:
            config: 搜索配置
            
        Returns:
            搜索结果列表
        """
        # 检查缓存
        cache_key = self._generate_cache_key(config)
        if cache_key in self._search_cache:
            cached_time = self._search_cache[cache_key][0].memory.timestamp if self._search_cache[cache_key] else ""
            if self._is_cache_valid(cache_key):
                return self._search_cache[cache_key]
        
        # 更新索引
        self._update_search_index(config.team_name)
        
        # 执行多种搜索策略
        all_results = []
        
        if 'exact' in config.search_types:
            exact_results = self._exact_search(config)
            all_results.extend(exact_results)
        
        if 'semantic' in config.search_types:
            semantic_results = self._semantic_search(config)
            all_results.extend(semantic_results)
        
        if 'tag' in config.search_types:
            tag_results = self._tag_search(config)
            all_results.extend(tag_results)
        
        if config.include_related:
            related_results = self._related_search(config)
            all_results.extend(related_results)
        
        # 去重和合并结果
        merged_results = self._merge_and_deduplicate(all_results)
        
        # 应用过滤器
        filtered_results = self._apply_filters(merged_results, config)
        
        # 排序和评分
        ranked_results = self._rank_results(filtered_results, config)
        
        # 限制结果数量
        final_results = ranked_results[:config.max_results]
        
        # 缓存结果
        self._search_cache[cache_key] = final_results
        
        return final_results
    
    def _update_search_index(self, team_name: str):
        """更新搜索索引"""
        current_time = datetime.now().timestamp()
        
        # 检查是否需要更新索引
        if current_time - self._last_index_update < 60:  # 1分钟内不重复更新
            return
        
        # 加载团队记忆
        memories = self._load_all_team_memories(team_name)
        
        # 构建词汇表
        self._build_vocabulary(memories)
        
        # 计算IDF分数
        self._calculate_idf_scores(memories)
        
        # 构建记忆索引
        self._build_memory_index(memories)
        
        self._last_index_update = current_time
    
    def _load_all_team_memories(self, team_name: str) -> List[MemoryEntry]:
        """加载团队的所有记忆"""
        if not self.directory_manager.team_exists(team_name):
            return []
        
        team_path = self.directory_manager.get_team_path(team_name)
        memories = []
        
        # 加载各类记忆文件
        memory_files = [
            team_path / "memory" / "declarative.md",
            team_path / "memory" / "procedural.md"
        ]
        
        # 加载情景性记忆
        episodic_dir = team_path / "memory" / "episodic"
        if episodic_dir.exists():
            memory_files.extend(episodic_dir.glob("*.md"))
        
        for file_path in memory_files:
            if file_path.exists():
                file_memories = self.markdown_engine.load_memories(file_path)
                memories.extend(file_memories)
        
        return memories
    
    def _build_vocabulary(self, memories: List[MemoryEntry]):
        """构建词汇表"""
        self.vocabulary.clear()
        
        for memory in memories:
            # 提取内容中的词汇
            content_words = self._extract_words(memory.content)
            self.vocabulary.update(content_words)
            
            # 提取标签中的词汇
            for tag in memory.tags:
                tag_words = self._extract_words(tag)
                self.vocabulary.update(tag_words)
    
    def _extract_words(self, text: str) -> List[str]:
        """从文本中提取词汇"""
        # 移除标点符号并转为小写
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text.lower())
        
        # 分词（简单空格分割）
        words = text.split()
        
        # 过滤短词和停用词
        stop_words = {'的', '了', '在', '是', '有', '和', '与', '或', '但', '而', '则', '将', '会', '能', '可', '要', '不', '非', '无', '没', '也', '都', '很', '最', '更', '比', '及', '对', '于', 'the', 'is', 'at', 'which', 'on', 'and', 'or', 'but', 'for', 'to', 'of', 'in', 'a', 'an', 'as', 'by', 'with', 'from'}
        
        filtered_words = [
            word for word in words 
            if len(word) > 1 and word not in stop_words
        ]
        
        return filtered_words
    
    def _calculate_idf_scores(self, memories: List[MemoryEntry]):
        """计算IDF分数"""
        self.idf_scores.clear()
        total_docs = len(memories)
        
        if total_docs == 0:
            return
        
        # 统计每个词在多少个文档中出现
        word_doc_count = defaultdict(int)
        
        for memory in memories:
            content_words = set(self._extract_words(memory.content))
            tag_words = set()
            for tag in memory.tags:
                tag_words.update(self._extract_words(tag))
            
            doc_words = content_words.union(tag_words)
            
            for word in doc_words:
                word_doc_count[word] += 1
        
        # 计算IDF分数
        for word in self.vocabulary:
            doc_freq = word_doc_count.get(word, 0)
            if doc_freq > 0:
                idf = math.log(total_docs / doc_freq)
                self.idf_scores[word] = idf
            else:
                self.idf_scores[word] = 0
    
    def _build_memory_index(self, memories: List[MemoryEntry]):
        """构建记忆索引"""
        self.memory_index.clear()
        
        for memory in memories:
            # 计算TF-IDF向量
            content_words = self._extract_words(memory.content)
            tag_words = []
            for tag in memory.tags:
                tag_words.extend(self._extract_words(tag))
            
            all_words = content_words + tag_words
            word_count = Counter(all_words)
            total_words = len(all_words)
            
            tfidf_vector = {}
            for word, count in word_count.items():
                tf = count / total_words if total_words > 0 else 0
                idf = self.idf_scores.get(word, 0)
                tfidf_vector[word] = tf * idf
            
            # 存储索引信息
            self.memory_index[memory.id] = {
                'memory': memory,
                'tfidf_vector': tfidf_vector,
                'content_words': content_words,
                'tag_words': tag_words,
                'all_words': all_words
            }
    
    def _exact_search(self, config: SearchConfig) -> List[SearchResult]:
        """精确搜索"""
        results = []
        query_words = self._extract_words(config.query.lower())
        
        for memory_id, index_data in self.memory_index.items():
            memory = index_data['memory']
            content_lower = memory.content.lower()
            
            # 检查完整查询字符串匹配
            if config.query.lower() in content_lower:
                score = 1.0
                snippet = self._extract_context_snippet(memory.content, config.query)
                
                result = SearchResult(
                    memory=memory,
                    relevance_score=score,
                    match_type='exact',
                    matched_terms=[config.query],
                    context_snippet=snippet
                )
                results.append(result)
                continue
            
            # 检查词汇匹配
            matched_words = []
            for word in query_words:
                if word in index_data['all_words']:
                    matched_words.append(word)
            
            if matched_words:
                # 计算匹配度
                match_ratio = len(matched_words) / len(query_words) if query_words else 0
                if match_ratio > 0.3:  # 至少匹配30%的查询词
                    snippet = self._extract_context_snippet(memory.content, ' '.join(matched_words))
                    
                    result = SearchResult(
                        memory=memory,
                        relevance_score=match_ratio,
                        match_type='exact',
                        matched_terms=matched_words,
                        context_snippet=snippet
                    )
                    results.append(result)
        
        return results
    
    def _semantic_search(self, config: SearchConfig) -> List[SearchResult]:
        """语义搜索"""
        results = []
        query_words = self._extract_words(config.query.lower())
        
        # 扩展查询词汇（同义词等）
        expanded_words = self._expand_query_words(query_words)
        
        # 计算查询向量
        query_vector = self._calculate_query_vector(expanded_words)
        
        for memory_id, index_data in self.memory_index.items():
            memory = index_data['memory']
            memory_vector = index_data['tfidf_vector']
            
            # 计算余弦相似度
            similarity = self._calculate_cosine_similarity(query_vector, memory_vector)
            
            if similarity > config.min_relevance:
                # 找到匹配的词汇
                matched_terms = []
                for word in expanded_words:
                    if word in memory_vector:
                        matched_terms.append(word)
                
                snippet = self._extract_context_snippet(memory.content, ' '.join(matched_terms[:3]))
                
                result = SearchResult(
                    memory=memory,
                    relevance_score=similarity,
                    match_type='semantic',
                    matched_terms=matched_terms,
                    context_snippet=snippet
                )
                results.append(result)
        
        return results
    
    def _tag_search(self, config: SearchConfig) -> List[SearchResult]:
        """标签搜索"""
        results = []
        query_words = set(self._extract_words(config.query.lower()))
        
        for memory_id, index_data in self.memory_index.items():
            memory = index_data['memory']
            
            # 检查标签匹配
            matched_tags = []
            for tag in memory.tags:
                tag_words = set(self._extract_words(tag.lower()))
                if query_words.intersection(tag_words):
                    matched_tags.append(tag)
            
            if matched_tags:
                # 计算标签匹配度
                tag_score = len(matched_tags) / len(memory.tags) if memory.tags else 0
                
                result = SearchResult(
                    memory=memory,
                    relevance_score=tag_score,
                    match_type='tag',
                    matched_terms=matched_tags,
                    context_snippet=f"Tags: {', '.join(matched_tags)}"
                )
                results.append(result)
        
        return results
    
    def _related_search(self, config: SearchConfig) -> List[SearchResult]:
        """相关记忆搜索"""
        results = []
        query_words = self._extract_words(config.query.lower())
        
        # 基于项目和标签的相关性
        for memory_id, index_data in self.memory_index.items():
            memory = index_data['memory']
            
            # 项目相关性
            if config.project_filter and memory.project == config.project_filter:
                related_score = 0.3
                
                result = SearchResult(
                    memory=memory,
                    relevance_score=related_score,
                    match_type='related',
                    matched_terms=[f"project:{memory.project}"],
                    context_snippet=f"Related by project: {memory.project}"
                )
                results.append(result)
        
        return results
    
    def _expand_query_words(self, words: List[str]) -> List[str]:
        """扩展查询词汇"""
        expanded = words.copy()
        
        for word in words:
            # 查找同义词
            if word in self.semantic_relations:
                related_words = self.semantic_relations[word]
                expanded.extend(related_words[:3])  # 限制同义词数量
        
        return list(set(expanded))
    
    def _calculate_query_vector(self, words: List[str]) -> Dict[str, float]:
        """计算查询向量"""
        word_count = Counter(words)
        total_words = len(words)
        
        query_vector = {}
        for word, count in word_count.items():
            if word in self.idf_scores:
                tf = count / total_words if total_words > 0 else 0
                idf = self.idf_scores[word]
                query_vector[word] = tf * idf
        
        return query_vector
    
    def _calculate_cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """计算余弦相似度"""
        # 计算点积
        dot_product = 0
        for word in vec1:
            if word in vec2:
                dot_product += vec1[word] * vec2[word]
        
        # 计算向量长度
        norm1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
        norm2 = math.sqrt(sum(val ** 2 for val in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
    
    def _extract_context_snippet(self, content: str, query: str, snippet_length: int = 150) -> str:
        """提取上下文片段"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 查找查询词在内容中的位置
        index = content_lower.find(query_lower)
        if index == -1:
            # 如果没找到完整查询，尝试找第一个查询词
            query_words = self._extract_words(query_lower)
            for word in query_words:
                index = content_lower.find(word)
                if index != -1:
                    break
        
        if index == -1:
            # 如果还是没找到，返回开头片段
            return content[:snippet_length] + "..." if len(content) > snippet_length else content
        
        # 提取前后文
        start = max(0, index - snippet_length // 2)
        end = min(len(content), index + len(query) + snippet_length // 2)
        
        snippet = content[start:end]
        
        # 添加省略号
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def _merge_and_deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        """合并和去重结果"""
        merged = {}
        
        for result in results:
            memory_id = result.memory.id
            
            if memory_id in merged:
                # 合并结果，取较高的相关性分数
                existing = merged[memory_id]
                if result.relevance_score > existing.relevance_score:
                    # 保留更高分数的结果，但合并匹配词汇
                    result.matched_terms.extend(existing.matched_terms)
                    result.matched_terms = list(set(result.matched_terms))
                    merged[memory_id] = result
                else:
                    # 合并匹配词汇到现有结果
                    existing.matched_terms.extend(result.matched_terms)
                    existing.matched_terms = list(set(existing.matched_terms))
            else:
                merged[memory_id] = result
        
        return list(merged.values())
    
    def _apply_filters(self, results: List[SearchResult], config: SearchConfig) -> List[SearchResult]:
        """应用过滤器"""
        filtered = results
        
        # 最小相关性过滤
        filtered = [r for r in filtered if r.relevance_score >= config.min_relevance]
        
        # 项目过滤
        if config.project_filter:
            filtered = [r for r in filtered if r.memory.project == config.project_filter]
        
        # 标签过滤
        if config.tag_filter:
            filtered = [
                r for r in filtered 
                if any(tag in r.memory.tags for tag in config.tag_filter)
            ]
        
        # 日期范围过滤
        if config.date_range:
            start_date, end_date = config.date_range
            filtered = [
                r for r in filtered 
                if start_date <= r.memory.timestamp <= end_date
            ]
        
        return filtered
    
    def _rank_results(self, results: List[SearchResult], config: SearchConfig) -> List[SearchResult]:
        """排序结果"""
        def calculate_final_score(result: SearchResult) -> float:
            score = result.relevance_score
            
            # 重要性加权
            if config.boost_important:
                importance_boost = (result.memory.importance - 1) * 0.1  # 1-5分 -> 0-0.4分
                score += importance_boost
            
            # 时间加权（最近的记忆得分更高）
            if config.boost_recent:
                try:
                    memory_time = datetime.fromisoformat(result.memory.timestamp.replace('Z', '+00:00'))
                    current_time = datetime.now()
                    time_diff_days = (current_time - memory_time).days
                    
                    # 30天内的记忆得到时间加权
                    if time_diff_days <= 30:
                        recency_boost = (30 - time_diff_days) / 30 * 0.2
                        score += recency_boost
                except:
                    pass  # 忽略时间解析错误
            
            # 匹配类型加权
            type_weights = {
                'exact': 1.0,
                'semantic': 0.8,
                'tag': 0.6,
                'related': 0.4
            }
            type_weight = type_weights.get(result.match_type, 0.5)
            score *= type_weight
            
            return score
        
        # 计算最终分数并排序
        for result in results:
            result.relevance_score = calculate_final_score(result)
        
        return sorted(results, key=lambda r: r.relevance_score, reverse=True)
    
    def _load_semantic_relations(self) -> Dict[str, List[str]]:
        """加载语义关系词典"""
        # 简单的同义词字典
        relations = {
            # 技术相关
            'frontend': ['前端', 'ui', 'interface', '界面'],
            'backend': ['后端', 'server', '服务器', 'api'],
            'database': ['数据库', 'db', '存储', 'storage'],
            'api': ['接口', 'interface', '服务', 'service'],
            'bug': ['错误', 'error', '问题', 'issue'],
            'feature': ['功能', 'function', '特性', '需求'],
            'test': ['测试', 'testing', '验证', 'verify'],
            'deploy': ['部署', 'deployment', '发布', 'release'],
            
            # 项目管理相关
            'requirement': ['需求', 'req', '要求', 'demand'],
            'task': ['任务', 'work', '工作', 'job'],
            'milestone': ['里程碑', 'goal', '目标', 'target'],
            'deadline': ['截止时间', 'due', '期限', 'timeline'],
            
            # 团队相关
            'team': ['团队', 'group', '小组', '组织'],
            'member': ['成员', 'people', '人员', 'staff'],
            'leader': ['领导', 'manager', '经理', 'boss'],
            'meeting': ['会议', 'discussion', '讨论', 'talk']
        }
        
        return relations
    
    def _generate_cache_key(self, config: SearchConfig) -> str:
        """生成缓存键"""
        key_parts = [
            config.query,
            config.team_name,
            str(sorted(config.search_types)),
            str(config.max_results),
            str(config.min_relevance),
            config.project_filter or "",
            str(sorted(config.tag_filter or [])),
            str(config.date_range or "")
        ]
        return "|".join(key_parts)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        # 简单的时间基于缓存验证
        return len(self._search_cache) < 100  # 限制缓存大小
    
    def clear_cache(self):
        """清除搜索缓存"""
        self._search_cache.clear()
    
    def get_search_statistics(self, team_name: str) -> Dict[str, Any]:
        """获取搜索统计信息"""
        memories = self._load_all_team_memories(team_name)
        
        if not memories:
            return {
                'total_memories': 0,
                'vocabulary_size': 0,
                'indexed_terms': 0
            }
        
        self._update_search_index(team_name)
        
        # 统计信息
        total_words = sum(len(data['all_words']) for data in self.memory_index.values())
        unique_projects = set(memory.project for memory in memories)
        unique_tags = set(tag for memory in memories for tag in memory.tags)
        
        return {
            'total_memories': len(memories),
            'vocabulary_size': len(self.vocabulary),
            'indexed_terms': len(self.idf_scores),
            'total_words': total_words,
            'unique_projects': len(unique_projects),
            'unique_tags': len(unique_tags),
            'projects': list(unique_projects),
            'tags': list(unique_tags),
            'cache_size': len(self._search_cache)
        } 