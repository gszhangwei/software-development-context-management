"""
ContextX上下文内容优化引擎

提供智能的内容优化功能，包括：
- 内容去重和相似度检测
- 文本压缩和摘要生成
- 内容质量评估和改进建议
- 结构化内容重组
"""

import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from collections import Counter, defaultdict

from .markdown_engine import MarkdownEngine, MemoryEntry, ContextSection
from .advanced_search import AdvancedSearchEngine


@dataclass
class ContentAnalysis:
    """内容分析结果"""
    content: str
    word_count: int
    sentence_count: int
    readability_score: float
    duplicate_ratio: float
    key_phrases: List[str]
    quality_score: float
    improvement_suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'word_count': self.word_count,
            'sentence_count': self.sentence_count,
            'readability_score': self.readability_score,
            'duplicate_ratio': self.duplicate_ratio,
            'key_phrases': self.key_phrases,
            'quality_score': self.quality_score,
            'improvement_suggestions': self.improvement_suggestions
        }


@dataclass
class OptimizationConfig:
    """优化配置"""
    remove_duplicates: bool = True
    compress_content: bool = True
    max_content_length: int = 5000
    min_sentence_length: int = 10
    preserve_structure: bool = True
    generate_summary: bool = True
    quality_threshold: float = 0.6
    

class ContentOptimizer:
    """内容优化引擎"""
    
    def __init__(self):
        """初始化内容优化器"""
        self.markdown_engine = MarkdownEngine()
        
        # 优化规则
        self.redundant_patterns = [
            r'\b同样地?\b',
            r'\b另外\b',
            r'\b此外\b',
            r'\b然而\b',
            r'\b但是\b',
            r'\b因此\b',
            r'\b所以\b',
            r'\b总之\b',
            r'\b综上所述\b'
        ]
        
        # 质量指标权重
        self.quality_weights = {
            'readability': 0.3,
            'completeness': 0.2,
            'uniqueness': 0.2,
            'structure': 0.15,
            'clarity': 0.15
        }
    
    def optimize_content(self, content: str, config: OptimizationConfig) -> Tuple[str, ContentAnalysis]:
        """
        优化内容
        
        Args:
            content: 原始内容
            config: 优化配置
            
        Returns:
            优化后的内容和分析结果
        """
        # 分析原始内容
        original_analysis = self.analyze_content(content)
        
        optimized_content = content
        
        # 去除重复内容
        if config.remove_duplicates:
            optimized_content = self._remove_duplicates(optimized_content)
        
        # 压缩内容
        if config.compress_content:
            optimized_content = self._compress_content(optimized_content, config)
        
        # 改进结构
        if config.preserve_structure:
            optimized_content = self._improve_structure(optimized_content)
        
        # 生成摘要
        if config.generate_summary and len(optimized_content) > config.max_content_length:
            optimized_content = self._generate_summary(optimized_content, config.max_content_length)
        
        # 分析优化后内容
        final_analysis = self.analyze_content(optimized_content)
        
        # 添加优化建议
        final_analysis.improvement_suggestions = self._generate_improvement_suggestions(
            original_analysis, final_analysis, config
        )
        
        return optimized_content, final_analysis
    
    def analyze_content(self, content: str) -> ContentAnalysis:
        """
        分析内容质量
        
        Args:
            content: 要分析的内容
            
        Returns:
            内容分析结果
        """
        # 基本统计
        words = self._extract_words(content)
        sentences = self._extract_sentences(content)
        
        word_count = len(words)
        sentence_count = len(sentences)
        
        # 可读性评分
        readability_score = self._calculate_readability_score(words, sentences)
        
        # 重复率计算
        duplicate_ratio = self._calculate_duplicate_ratio(content)
        
        # 关键词短语提取
        key_phrases = self._extract_key_phrases(content)
        
        # 综合质量评分
        quality_score = self._calculate_quality_score(
            readability_score, duplicate_ratio, word_count, sentence_count
        )
        
        return ContentAnalysis(
            content=content,
            word_count=word_count,
            sentence_count=sentence_count,
            readability_score=readability_score,
            duplicate_ratio=duplicate_ratio,
            key_phrases=key_phrases,
            quality_score=quality_score
        )
    
    def deduplicate_memories(self, memories: List[MemoryEntry], similarity_threshold: float = 0.8) -> List[MemoryEntry]:
        """
        去重记忆条目
        
        Args:
            memories: 记忆条目列表
            similarity_threshold: 相似度阈值
            
        Returns:
            去重后的记忆列表
        """
        if not memories:
            return memories
        
        unique_memories = []
        content_hashes = set()
        
        for memory in memories:
            # 计算内容哈希
            content_hash = self._calculate_content_hash(memory.content)
            
            # 检查完全重复
            if content_hash in content_hashes:
                continue
            
            # 检查相似度重复
            is_duplicate = False
            for existing_memory in unique_memories:
                similarity = self._calculate_text_similarity(memory.content, existing_memory.content)
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    # 如果新记忆更重要或更新，替换现有记忆
                    if (memory.importance > existing_memory.importance or 
                        memory.timestamp > existing_memory.timestamp):
                        unique_memories.remove(existing_memory)
                        break
                    else:
                        break
            
            if not is_duplicate:
                unique_memories.append(memory)
                content_hashes.add(content_hash)
        
        return unique_memories
    
    def merge_similar_contents(self, contents: List[str], similarity_threshold: float = 0.7) -> List[str]:
        """
        合并相似内容
        
        Args:
            contents: 内容列表
            similarity_threshold: 相似度阈值
            
        Returns:
            合并后的内容列表
        """
        if not contents:
            return contents
        
        merged_contents = []
        used_indices = set()
        
        for i, content1 in enumerate(contents):
            if i in used_indices:
                continue
            
            similar_contents = [content1]
            used_indices.add(i)
            
            # 查找相似内容
            for j, content2 in enumerate(contents[i+1:], i+1):
                if j in used_indices:
                    continue
                
                similarity = self._calculate_text_similarity(content1, content2)
                if similarity >= similarity_threshold:
                    similar_contents.append(content2)
                    used_indices.add(j)
            
            # 合并相似内容
            if len(similar_contents) > 1:
                merged_content = self._merge_texts(similar_contents)
                merged_contents.append(merged_content)
            else:
                merged_contents.append(content1)
        
        return merged_contents
    
    def _remove_duplicates(self, content: str) -> str:
        """移除重复内容"""
        lines = content.split('\n')
        unique_lines = []
        seen_lines = set()
        
        for line in lines:
            line_stripped = line.strip()
            if line_stripped and line_stripped not in seen_lines:
                unique_lines.append(line)
                seen_lines.add(line_stripped)
            elif not line_stripped:  # 保留空行
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    def _compress_content(self, content: str, config: OptimizationConfig) -> str:
        """压缩内容"""
        # 移除多余的空白
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # 合并短句
        sentences = self._extract_sentences(content)
        compressed_sentences = []
        current_sentence = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < config.min_sentence_length:
                if current_sentence:
                    current_sentence += " " + sentence
                else:
                    current_sentence = sentence
            else:
                if current_sentence:
                    compressed_sentences.append(current_sentence + " " + sentence)
                    current_sentence = ""
                else:
                    compressed_sentences.append(sentence)
        
        if current_sentence:
            compressed_sentences.append(current_sentence)
        
        return ' '.join(compressed_sentences)
    
    def _improve_structure(self, content: str) -> str:
        """改进内容结构"""
        lines = content.split('\n')
        improved_lines = []
        
        current_section = []
        
        for line in lines:
            line = line.strip()
            
            # 检测标题行
            if line.startswith('#') or line.startswith('**') and line.endswith('**'):
                # 处理之前的段落
                if current_section:
                    improved_lines.extend(self._format_section(current_section))
                    current_section = []
                
                improved_lines.append(line)
            else:
                current_section.append(line)
        
        # 处理最后一个段落
        if current_section:
            improved_lines.extend(self._format_section(current_section))
        
        return '\n'.join(improved_lines)
    
    def _generate_summary(self, content: str, max_length: int) -> str:
        """生成内容摘要"""
        sentences = self._extract_sentences(content)
        
        if not sentences:
            return content[:max_length]
        
        # 计算句子重要性分数
        sentence_scores = []
        words_freq = self._calculate_word_frequency(content)
        
        for sentence in sentences:
            score = self._calculate_sentence_importance(sentence, words_freq)
            sentence_scores.append((sentence, score))
        
        # 按重要性排序
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 选择重要句子
        summary_sentences = []
        current_length = 0
        
        for sentence, score in sentence_scores:
            if current_length + len(sentence) <= max_length:
                summary_sentences.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        # 按原始顺序重新排列
        original_order = []
        for sentence in sentences:
            if sentence in summary_sentences:
                original_order.append(sentence)
        
        return ' '.join(original_order)
    
    def _extract_words(self, text: str) -> List[str]:
        """提取词汇"""
        # 移除标点符号并转为小写
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text.lower())
        words = text.split()
        return [word for word in words if len(word) > 1]
    
    def _extract_sentences(self, text: str) -> List[str]:
        """提取句子"""
        # 简单的句子分割
        sentences = re.split(r'[.!?。！？]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_readability_score(self, words: List[str], sentences: List[str]) -> float:
        """计算可读性分数"""
        if not sentences:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        
        # 简化的可读性公式
        # 理想句子长度是15-20个词
        ideal_length = 17.5
        length_penalty = abs(avg_sentence_length - ideal_length) / ideal_length
        
        # 词汇复杂度（长词比例）
        long_words = [w for w in words if len(w) > 6]
        complexity = len(long_words) / len(words) if words else 0
        
        # 综合评分
        readability = max(0, 1 - length_penalty * 0.3 - complexity * 0.4)
        
        return min(1.0, readability)
    
    def _calculate_duplicate_ratio(self, content: str) -> float:
        """计算重复率"""
        lines = content.split('\n')
        line_counts = Counter(line.strip() for line in lines if line.strip())
        
        if not line_counts:
            return 0.0
        
        duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        total_lines = len([line for line in lines if line.strip()])
        
        return duplicate_lines / total_lines if total_lines > 0 else 0.0
    
    def _extract_key_phrases(self, content: str) -> List[str]:
        """提取关键短语"""
        words = self._extract_words(content)
        word_freq = Counter(words)
        
        # 获取高频词汇
        common_words = [word for word, count in word_freq.most_common(10) if count > 1]
        
        # 查找包含高频词的短语
        phrases = []
        sentences = self._extract_sentences(content)
        
        for sentence in sentences:
            sentence_words = self._extract_words(sentence)
            for word in common_words:
                if word in sentence_words:
                    # 提取包含该词的短语（前后2个词）
                    word_index = sentence_words.index(word)
                    start = max(0, word_index - 2)
                    end = min(len(sentence_words), word_index + 3)
                    phrase = ' '.join(sentence_words[start:end])
                    if len(phrase) > 5:  # 过滤太短的短语
                        phrases.append(phrase)
        
        # 去重并限制数量
        unique_phrases = list(set(phrases))
        return unique_phrases[:5]
    
    def _calculate_quality_score(self, readability: float, duplicate_ratio: float, 
                                word_count: int, sentence_count: int) -> float:
        """计算质量分数"""
        # 可读性分数
        readability_score = readability * self.quality_weights['readability']
        
        # 唯一性分数（越少重复越好）
        uniqueness_score = (1 - duplicate_ratio) * self.quality_weights['uniqueness']
        
        # 完整性分数（基于长度）
        completeness_score = min(1.0, word_count / 100) * self.quality_weights['completeness']
        
        # 结构化分数（基于句子数量）
        structure_score = min(1.0, sentence_count / 10) * self.quality_weights['structure']
        
        # 清晰度分数（句子长度适中）
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        clarity_score = (1 - abs(avg_sentence_length - 15) / 15) * self.quality_weights['clarity']
        clarity_score = max(0, clarity_score)
        
        total_score = (readability_score + uniqueness_score + completeness_score + 
                      structure_score + clarity_score)
        
        return min(1.0, total_score)
    
    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希"""
        normalized_content = re.sub(r'\s+', ' ', content.strip().lower())
        return hashlib.md5(normalized_content.encode('utf-8')).hexdigest()
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        words1 = set(self._extract_words(text1))
        words2 = set(self._extract_words(text2))
        
        if not words1 and not words2:
            return 1.0
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _merge_texts(self, texts: List[str]) -> str:
        """合并多个文本"""
        # 提取所有句子
        all_sentences = []
        for text in texts:
            sentences = self._extract_sentences(text)
            all_sentences.extend(sentences)
        
        # 去重并保持最好的版本
        unique_sentences = []
        for sentence in all_sentences:
            is_duplicate = False
            for i, existing in enumerate(unique_sentences):
                similarity = self._calculate_text_similarity(sentence, existing)
                if similarity > 0.8:
                    # 保留更长的版本
                    if len(sentence) > len(existing):
                        unique_sentences[i] = sentence
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_sentences.append(sentence)
        
        return ' '.join(unique_sentences)
    
    def _format_section(self, section_lines: List[str]) -> List[str]:
        """格式化段落"""
        if not section_lines:
            return []
        
        # 移除空行
        content_lines = [line for line in section_lines if line.strip()]
        
        if not content_lines:
            return ['']
        
        # 如果是列表项，保持原格式
        if any(line.strip().startswith(('-', '*', '1.', '2.')) for line in content_lines):
            return content_lines + ['']
        
        # 合并为段落
        paragraph = ' '.join(content_lines)
        return [paragraph, '']
    
    def _calculate_word_frequency(self, content: str) -> Dict[str, int]:
        """计算词频"""
        words = self._extract_words(content)
        return Counter(words)
    
    def _calculate_sentence_importance(self, sentence: str, word_freq: Dict[str, int]) -> float:
        """计算句子重要性"""
        words = self._extract_words(sentence)
        
        if not words:
            return 0.0
        
        # 基于词频的重要性
        importance = sum(word_freq.get(word, 0) for word in words)
        
        # 句子长度加权（中等长度句子更重要）
        length_factor = 1.0
        if len(words) < 5:
            length_factor = 0.5
        elif len(words) > 30:
            length_factor = 0.7
        
        return importance * length_factor / len(words)
    
    def _generate_improvement_suggestions(self, original: ContentAnalysis, 
                                        optimized: ContentAnalysis, 
                                        config: OptimizationConfig) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 可读性建议
        if optimized.readability_score < 0.6:
            suggestions.append("建议简化句子结构，使用更简单的词汇提高可读性")
        
        # 重复内容建议
        if optimized.duplicate_ratio > 0.1:
            suggestions.append("发现重复内容，建议进一步去重或合并相似段落")
        
        # 长度建议
        if optimized.word_count > config.max_content_length * 2:
            suggestions.append("内容过长，建议创建摘要版本或拆分为多个章节")
        
        # 结构建议
        if optimized.sentence_count < 3:
            suggestions.append("内容较少，建议添加更多详细信息或示例")
        
        # 质量改进
        if optimized.quality_score < config.quality_threshold:
            suggestions.append("整体质量需要提升，建议重新组织内容结构")
        
        # 对比改进效果
        if optimized.quality_score > original.quality_score:
            improvement = (optimized.quality_score - original.quality_score) * 100
            suggestions.append(f"优化效果：质量分数提升了 {improvement:.1f}%")
        
        return suggestions 