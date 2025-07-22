"""
ContextX上下文处理器

负责将团队记忆、配置和seven_stage_framework模板转换为结构化的上下文，支持：
- 记忆内容的智能聚合和过滤
- seven_stage_framework七阶段模块的组装
- 混合模式：记忆+七阶段框架的融合
- 基于场景的上下文定制
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .markdown_engine import MarkdownEngine, MemoryEntry, ContextSection
from .directory_manager import DirectoryManager


class ContextMode(Enum):
    """上下文生成模式"""
    MEMORY_ONLY = "memory_only"           # 仅使用记忆
    FRAMEWORK_ONLY = "framework_only"     # 仅使用七阶段框架
    HYBRID = "hybrid"                     # 混合模式：记忆+框架


class MemoryType(Enum):
    """记忆类型"""
    DECLARATIVE = "declarative"           # 声明性记忆
    PROCEDURAL = "procedural"             # 程序性记忆
    EPISODIC = "episodic"                 # 情景性记忆
    ALL = "all"                           # 所有记忆


@dataclass
class ContextGenerationConfig:
    """上下文生成配置"""
    team_name: str
    mode: ContextMode = ContextMode.HYBRID
    
    # 记忆相关配置
    include_memory_types: List[MemoryType] = field(default_factory=lambda: [MemoryType.ALL])
    max_memory_items: int = 50
    memory_importance_threshold: int = 2
    
    # 框架相关配置
    include_framework_stages: List[str] = field(default_factory=lambda: [
        "requirements", "business-model", "solution", "structure", 
        "tasks", "common-tasks", "constraints"
    ])
    
    # 过滤条件
    project_scope: Optional[str] = None
    time_range: Optional[Tuple[str, str]] = None
    memory_filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedContext:
    """生成的上下文结果"""
    team_name: str
    mode: ContextMode
    content: str
    source_memories: List[str] = field(default_factory=list)
    framework_stages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generation_time: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        # 直接返回内容，不包含元信息
        return self.content
    
    def to_markdown_with_metadata(self) -> str:
        """转换为包含元信息的完整Markdown格式"""
        md_content = [
            f"# {self.team_name.title()} Team Context",
            f"",
            f"**Generation Mode:** {self.mode.value}",
            f"**Generated:** {self.generation_time}",
            ""
        ]
        
        if self.source_memories:
            md_content.extend([
                f"**Memory Sources:** {len(self.source_memories)} items",
                ""
            ])
        
        if self.framework_stages:
            md_content.extend([
                f"**Framework Stages:** {', '.join(self.framework_stages)}",
                ""
            ])
        
        md_content.extend([
            "---",
            "",
            self.content
        ])
        
        if self.metadata:
            md_content.extend([
                "",
                "---",
                "",
                "## Generation Metadata",
                "",
                f"```json",
                json.dumps(self.metadata, indent=2, ensure_ascii=False),
                "```"
            ])
        
        return "\n".join(md_content)
    
    def save_to_file(self, output_path: Union[str, Path]) -> Path:
        """保存到文件"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_markdown(), encoding='utf-8')
        return output_path


class ContextProcessor:
    """上下文处理器"""
    
    def __init__(self, base_path: Path):
        """
        初始化上下文处理器
        
        Args:
            base_path: 团队数据根目录
        """
        self.base_path = Path(base_path)
        self.directory_manager = DirectoryManager(base_path)
        self.markdown_engine = MarkdownEngine()
        
        # Seven stage framework 路径
        self.framework_path = Path(__file__).parent.parent / "seven_stage_framework"
        
        # 阶段文件映射
        self.stage_files = {
            "overview": "00_overview.md",
            "requirements": "01_requirements.md",
            "business-model": "02_business_model.md",
            "solution": "03_solution.md",
            "structure": "04_structure.md",
            "tasks": "05_tasks.md",
            "common-tasks": "06_common_tasks.md",
            "constraints": "07_constraints.md"
        }
    
    def generate_context(self, config: ContextGenerationConfig, user_message: str = None) -> GeneratedContext:
        """
        生成结构化上下文
        
        Args:
            config: 上下文生成配置
            user_message: 用户消息，用于智能选择相关记忆
        
        Returns:
            生成的上下文
        """
        # 验证团队存在
        if not self.directory_manager.team_exists(config.team_name):
            raise ValueError(f"Team '{config.team_name}' does not exist")
        
        team_path = self.directory_manager.get_team_path(config.team_name)
        
        # 根据模式生成上下文
        if config.mode == ContextMode.MEMORY_ONLY:
            return self._generate_memory_only_context(config, team_path, user_message)
        elif config.mode == ContextMode.FRAMEWORK_ONLY:
            return self._generate_framework_only_context(config, team_path)
        elif config.mode == ContextMode.HYBRID:
            return self._generate_hybrid_context(config, team_path, user_message)
        else:
            raise ValueError(f"Unsupported context mode: {config.mode}")
    
    def _generate_memory_only_context(self, config: ContextGenerationConfig, team_path: Path, user_message: str = None) -> GeneratedContext:
        """生成仅基于记忆的上下文"""
        memories = self._load_team_memories(team_path, config)
        
        content_sections = []
        
        if memories:
            # 如果提供了用户消息，智能选择相关记忆
            if user_message:
                relevant_memories = self._find_relevant_memories_by_message(memories, user_message)
                selected_memories = relevant_memories[:10]  # 限制最多10个记忆
            else:
                # 否则按类型组织记忆
                selected_memories = memories
            
            if selected_memories:
                for memory in selected_memories:
                    content_sections.extend([
                        f"### {memory.id}",
                        f"**Project:** {memory.project}",
                        f"**Importance:** {'⭐' * memory.importance}",
                        f"**Tags:** {', '.join(memory.tags)}",
                        f"**Timestamp:** {memory.timestamp}",
                        "",
                        memory.content,
                        "",
                        "---",
                        ""
                    ])
        
        # 如果没有记忆，生成简洁的内容（不显示"No memories found"）
        if not memories:
            content_sections = [""]  # 空内容
        
        return GeneratedContext(
            team_name=config.team_name,
            mode=config.mode,
            content="\n".join(content_sections),
            source_memories=[m.id for m in memories],
            metadata={
                'memory_count': len(memories),
                'memory_types_included': [mt.value for mt in config.include_memory_types]
            }
        )
    
    def _generate_framework_only_context(self, config: ContextGenerationConfig, team_path: Path) -> GeneratedContext:
        """生成仅基于七阶段框架的上下文"""
        content_sections = []
        
        # 加载概述
        overview_content = self._load_framework_stage("overview")
        if overview_content:
            content_sections.extend([
                overview_content,
                "",
                "---",
                ""
            ])
        
        # 加载各阶段内容
        included_stages = []
        for stage in config.include_framework_stages:
            stage_content = self._load_framework_stage(stage)
            if stage_content:
                included_stages.append(stage)
                content_sections.extend([
                    stage_content,
                    "",
                    "---",
                    ""
                ])
        
        # 尝试加载团队自定义的上下文文件（如果存在）
        team_context_sections = self._load_team_context_files(team_path, config.include_framework_stages)
        if team_context_sections:
            content_sections.extend([
                "## Team-Specific Context",
                "",
                *team_context_sections
            ])
        
        return GeneratedContext(
            team_name=config.team_name,
            mode=config.mode,
            content="\n".join(content_sections),
            framework_stages=included_stages,
            metadata={
                'framework_stages_count': len(included_stages),
                'requested_stages': config.include_framework_stages
            }
        )
    
    def _generate_hybrid_context(self, config: ContextGenerationConfig, team_path: Path, user_message: str = None) -> GeneratedContext:
        """生成混合模式上下文（记忆+框架）"""
        memories = self._load_team_memories(team_path, config)
        
        content_sections = []
        used_memory_ids = set()  # 跟踪已使用的记忆，避免重复
        
        # 0. 添加混合模式指导提示
        content_sections.extend([
            "先理解记忆的内容，再基于七步框架结合user_message生成具体的结构化提示词",
            "",
            "---",
            ""
        ])
        
        # 1. 记忆内容优先放置在前面 - 仅在有相关性时加载
        if memories and user_message:
            # 只有在提供用户消息时才尝试匹配记忆，避免无关记忆污染上下文
            relevant_memories = self._find_relevant_memories_by_message(memories, user_message)
            if relevant_memories:
                # 限制最多5个最相关的记忆
                top_memories = relevant_memories[:5]
                for memory in top_memories:
                    content_sections.extend([
                        f"#团队记忆",
                        f"### {memory.id}",
                        f"**Project:** {memory.project}",
                        f"**Importance:** {'⭐' * memory.importance}",
                        f"**Tags:** {', '.join(memory.tags)}",
                        "",
                        memory.content,
                        "",
                        "---",
                        ""
                    ])
                    used_memory_ids.add(memory.id)
        
        # 2. 七阶段框架作为主体结构
        content_sections.extend([
            "# 七步框架模板内容",
            "",
            ""
        ])
        
        included_stages = []
        for stage in config.include_framework_stages:
            stage_content = self._load_framework_stage(stage)
            if stage_content:
                included_stages.append(stage)
                content_sections.extend([
                    stage_content,
                    ""
                ])
                
                # 3. 加载团队自定义上下文（如果存在且有实际内容）
                team_content = self._load_team_context_file(team_path, stage)
                if team_content and team_content.strip():
                    content_sections.extend([
                        team_content,
                        ""
                    ])
                
                content_sections.extend(["---", ""])
        
        return GeneratedContext(
            team_name=config.team_name,
            mode=config.mode,
            content="\n".join(content_sections),
            source_memories=list(used_memory_ids),  # 只包含实际使用的记忆ID
            framework_stages=included_stages,
            metadata={
                'memory_count': len(used_memory_ids),  # 实际使用的记忆数量
                'total_memories_available': len(memories),  # 总的可用记忆数量
                'framework_stages_count': len(included_stages),
                'hybrid_mode': True
            }
        )
    
    def _load_team_memories(self, team_path: Path, config: ContextGenerationConfig) -> List[MemoryEntry]:
        """加载团队记忆"""
        memories = []
        
        # 根据配置决定加载哪些类型的记忆
        memory_types_to_load = config.include_memory_types
        if MemoryType.ALL in memory_types_to_load:
            memory_types_to_load = [MemoryType.DECLARATIVE, MemoryType.PROCEDURAL, MemoryType.EPISODIC]
        
        # 加载声明性记忆
        if MemoryType.DECLARATIVE in memory_types_to_load:
            declarative_path = team_path / "memory" / "declarative.md"
            if declarative_path.exists():
                declarative_memories = self.markdown_engine.load_memories(declarative_path)
                for memory in declarative_memories:
                    memory.memory_type = "declarative"
                memories.extend(declarative_memories)
        
        # 加载程序性记忆
        if MemoryType.PROCEDURAL in memory_types_to_load:
            procedural_path = team_path / "memory" / "procedural.md"
            if procedural_path.exists():
                procedural_memories = self.markdown_engine.load_memories(procedural_path)
                for memory in procedural_memories:
                    memory.memory_type = "procedural"
                memories.extend(procedural_memories)
        
        # 加载情景性记忆
        if MemoryType.EPISODIC in memory_types_to_load:
            episodic_dir = team_path / "memory" / "episodic"
            if episodic_dir.exists():
                for episodic_file in episodic_dir.glob("*.md"):
                    episodic_memories = self.markdown_engine.load_memories(episodic_file)
                    for memory in episodic_memories:
                        memory.memory_type = "episodic"
                    memories.extend(episodic_memories)
        
        # 应用过滤器
        filtered_memories = self._apply_memory_filters(memories, config)
        
        # 按重要性和时间排序
        filtered_memories.sort(
            key=lambda m: (m.importance, m.timestamp), 
            reverse=True
        )
        
        # 限制数量
        return filtered_memories[:config.max_memory_items]
    
    def _apply_memory_filters(self, memories: List[MemoryEntry], config: ContextGenerationConfig) -> List[MemoryEntry]:
        """应用记忆过滤器"""
        filtered = memories
        
        # 重要性过滤
        filtered = [m for m in filtered if m.importance >= config.memory_importance_threshold]
        
        # 项目范围过滤
        if config.project_scope:
            filtered = [m for m in filtered if m.project == config.project_scope]
        
        # 时间范围过滤
        if config.time_range:
            start_time, end_time = config.time_range
            filtered = [
                m for m in filtered 
                if start_time <= m.timestamp <= end_time
            ]
        
        # 标签过滤
        if 'tags' in config.memory_filters:
            required_tags = config.memory_filters['tags']
            if isinstance(required_tags, str):
                required_tags = [required_tags]
            filtered = [
                m for m in filtered 
                if any(tag in m.tags for tag in required_tags)
            ]
        
        return filtered
    
    def _group_memories_by_type(self, memories: List[MemoryEntry]) -> Dict[str, List[MemoryEntry]]:
        """按类型分组记忆"""
        groups = {
            "declarative": [],
            "procedural": [],
            "episodic": []
        }
        
        for memory in memories:
            memory_type = getattr(memory, 'memory_type', 'declarative')
            if memory_type in groups:
                groups[memory_type].append(memory)
            else:
                groups['declarative'].append(memory)  # 默认归类为声明性记忆
        
        return groups
    
    def _load_framework_stage(self, stage: str) -> Optional[str]:
        """加载框架阶段内容"""
        if stage not in self.stage_files:
            return None
        
        stage_file = self.framework_path / self.stage_files[stage]
        if stage_file.exists():
            return stage_file.read_text(encoding='utf-8')
        return None
    
    def _load_team_context_file(self, team_path: Path, stage: str) -> Optional[str]:
        """加载团队特定的上下文文件，过滤掉元数据部分"""
        context_file = team_path / "context" / f"{stage}.md"
        if context_file.exists():
            content = context_file.read_text(encoding='utf-8')
            return self._filter_team_context_content(content)
        return None
    
    def _filter_team_context_content(self, content: str) -> str:
        """过滤团队上下文内容，去掉元数据部分，只保留实际内容"""
        lines = content.split('\n')
        filtered_lines = []
        skip_metadata = False
        
        for line in lines:
            # 跳过元数据相关的部分
            if line.strip().startswith('## 元数据') or line.strip().startswith('## 最近更新'):
                skip_metadata = True
                continue
            
            # 如果遇到新的二级标题，且不是元数据相关，停止跳过
            if line.strip().startswith('## ') and not any(keyword in line for keyword in ['元数据', '最近更新']):
                skip_metadata = False
            
            # 如果遇到三级标题，通常表示实际内容开始
            if line.strip().startswith('### '):
                skip_metadata = False
            
            # 如果不在跳过状态，且不是元数据行，则保留
            if not skip_metadata and not (line.strip().startswith('- **') and any(keyword in line for keyword in ['团队:', '生成时间:', '上下文类型:', '时间:', '触发:'])):
                filtered_lines.append(line)
        
        # 清理开头的空行和标题
        while filtered_lines and (not filtered_lines[0].strip() or filtered_lines[0].strip().startswith('#')):
            filtered_lines.pop(0)
        
        return '\n'.join(filtered_lines).strip()
    
    def _load_team_context_files(self, team_path: Path, stages: List[str]) -> List[str]:
        """加载团队所有上下文文件"""
        sections = []
        for stage in stages:
            content = self._load_team_context_file(team_path, stage)
            if content:
                sections.extend([
                    content,
                    "",
                    "---",
                    ""
                ])
        return sections
    
    def _find_memories_for_stage(self, memories: List[MemoryEntry], stage: str) -> List[MemoryEntry]:
        """为特定阶段找到相关记忆"""
        # 定义每个阶段的关键词
        stage_keywords = {
            "requirements": ["需求", "requirement", "需要", "目标", "goal", "objective"],
            "business-model": ["业务", "business", "模型", "model", "流程", "process"],
            "solution": ["解决方案", "solution", "方案", "approach", "策略", "strategy"],
            "structure": ["架构", "architecture", "结构", "structure", "设计", "design"],
            "tasks": ["任务", "task", "工作", "work", "实施", "implementation"],
            "common-tasks": ["通用", "common", "标准", "standard", "模板", "template"],
            "constraints": ["约束", "constraint", "限制", "limitation", "规则", "rule"]
        }
        
        keywords = stage_keywords.get(stage, [])
        if not keywords:
            return []
        
        relevant_memories = []
        for memory in memories:
            # 检查标签
            tag_match = any(
                any(keyword.lower() in tag.lower() for keyword in keywords)
                for tag in memory.tags
            )
            
            # 检查内容
            content_match = any(
                keyword.lower() in memory.content.lower() 
                for keyword in keywords
            )
            
            if tag_match or content_match:
                relevant_memories.append(memory)
        
        # 按重要性排序
        relevant_memories.sort(key=lambda m: m.importance, reverse=True)
        return relevant_memories
    
    def _find_relevant_memories_by_message(self, memories: List[MemoryEntry], user_message: str) -> List[MemoryEntry]:
        """根据用户消息智能选择相关记忆"""
        if not user_message or not memories:
            return []
        
        # 提取用户消息中的关键词
        message_keywords = self._extract_keywords_from_message(user_message.lower())
        
        # 如果没有提取到关键词，说明消息与技术内容无关，不加载任何记忆
        if not message_keywords:
            return []
        
        # 为每个记忆计算相关性分数
        scored_memories = []
        for memory in memories:
            score = self._calculate_memory_relevance_score(memory, message_keywords, user_message.lower())
            # 提高相关性阈值：只有分数>=3.0才认为是相关的记忆
            # 这样可以过滤掉弱相关的记忆，只保留真正相关的内容
            if score >= 3.0:
                scored_memories.append((memory, score))
        
        # 如果没有足够相关的记忆，返回空列表
        if not scored_memories:
            return []
        
        # 按相关性分数和重要性排序
        scored_memories.sort(key=lambda x: (x[1], x[0].importance), reverse=True)
        
        return [memory for memory, score in scored_memories]
    
    def _extract_keywords_from_message(self, message: str) -> List[str]:
        """从用户消息中提取关键词"""
        import re
        
        # 过滤停用词 - 扩展列表，过滤更多无关词汇
        stop_words = {
            # 英文停用词
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his',
            'get', 'make', 'go', 'come', 'know', 'think', 'see', 'want', 'use', 'find', 'give', 'tell', 'work',
            'call', 'try', 'ask', 'need', 'feel', 'become', 'leave', 'put', 'mean', 'keep', 'let', 'begin',
            # 中文停用词
            '我', '你', '他', '她', '它', '我们', '你们', '他们', '的', '了', '在', '是', '有', '这', '那',
            '一个', '请', '帮', '我要', '需要', '希望', '可以', '如何', '怎么', '什么', '为什么', '因为',
            '所以', '但是', '然后', '现在', '已经', '还是', '就是', '都是', '不是', '没有', '也是', '或者',
            '其他', '其它', '一些', '很多', '非常', '特别', '比较', '觉得', '应该', '可能', '一直', '总是',
            '从来', '从不', '永远', '马上', '立即', '现在', '以前', '以后', '今天', '明天', '昨天'
        }
        
        keywords = []
        
        # 处理英文词汇（按空格分割）
        english_words = re.findall(r'[a-zA-Z]+', message)
        for word in english_words:
            word_lower = word.lower()
            # 提高英文单词的最小长度要求，避免提取无意义的短词
            if len(word) >= 3 and word_lower not in stop_words:
                keywords.append(word_lower)
        
        # 处理中文关键词（使用简单的规则识别）
        chinese_text = re.sub(r'[^\u4e00-\u9fa5]', '', message)
        
        # 识别常见的技术术语和概念 - 更精准的匹配
        tech_patterns = [
            r'工作流', r'workflow', r'API', r'api', r'接口', r'数据库', r'database', 
            r'认证', r'authentication', r'权限', r'authorization', r'管理', r'management',
            r'服务', r'service', r'查询', r'query', r'分页', r'pagination', 
            r'架构', r'architecture', r'实现', r'implementation', r'配置', r'configuration',
            r'框架', r'framework', r'模型', r'model', r'业务', r'business', 
            r'流程', r'process', r'功能', r'feature', r'模块', r'module', r'组件', r'component',
            r'Rule', r'rule', r'Solution', r'solution', r'Prompt', r'prompt'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                if match.lower() not in [kw.lower() for kw in keywords]:
                    keywords.append(match.lower())
        
        # 如果没有找到关键词，使用简单的字符切分作为备选
        if not keywords and chinese_text:
            # 简单的中文双字词提取
            for i in range(len(chinese_text) - 1):
                two_char = chinese_text[i:i+2]
                if two_char not in stop_words:
                    keywords.append(two_char)
        
        return list(set(keywords))  # 去重
    
    def _calculate_memory_relevance_score(self, memory: MemoryEntry, message_keywords: List[str], full_message: str) -> float:
        """计算记忆与用户消息的相关性分数"""
        score = 0.0
        
        # 1. 标签匹配 (权重: 3.0)
        for tag in memory.tags:
            tag_lower = tag.lower()
            for keyword in message_keywords:
                if keyword in tag_lower or tag_lower in keyword:
                    score += 3.0
        
        # 2. 内容关键词匹配 (权重: 2.0)
        memory_content_lower = memory.content.lower()
        for keyword in message_keywords:
            if keyword in memory_content_lower:
                score += 2.0
        
        # 3. 项目名匹配 (权重: 1.5)
        if memory.project and memory.project.lower() != 'general':
            project_lower = memory.project.lower()
            for keyword in message_keywords:
                if keyword in project_lower or project_lower in keyword:
                    score += 1.5
        
        # 4. 完整短语匹配 (权重: 4.0)
        # 寻找用户消息中的2-3词组合是否在记忆内容中出现
        for i in range(len(message_keywords) - 1):
            phrase = " ".join(message_keywords[i:i+2])
            if phrase in memory_content_lower:
                score += 4.0
        
        # 5. 重要性加权
        score *= (memory.importance / 3.0)  # 重要性归一化到相对权重
        
        return score
    
    def _get_unmatched_memories(self, memories: List[MemoryEntry], stages: List[str]) -> List[MemoryEntry]:
        """获取未匹配到任何阶段的记忆"""
        matched_memory_ids = set()
        
        # 收集所有已匹配的记忆ID
        for stage in stages:
            stage_memories = self._find_memories_for_stage(memories, stage)
            matched_memory_ids.update(m.id for m in stage_memories)
        
        # 返回未匹配的记忆
        unmatched = [m for m in memories if m.id not in matched_memory_ids]
        return sorted(unmatched, key=lambda m: m.importance, reverse=True)


# 便捷函数
def create_memory_only_config(team_name: str, **kwargs) -> ContextGenerationConfig:
    """创建仅记忆模式的配置"""
    return ContextGenerationConfig(
        team_name=team_name,
        mode=ContextMode.MEMORY_ONLY,
        **kwargs
    )


def create_framework_only_config(team_name: str, stages: List[str] = None, **kwargs) -> ContextGenerationConfig:
    """创建仅框架模式的配置"""
    if stages is None:
        stages = ["requirements", "business-model", "solution", "structure", "tasks", "common-tasks", "constraints"]
    
    return ContextGenerationConfig(
        team_name=team_name,
        mode=ContextMode.FRAMEWORK_ONLY,
        include_framework_stages=stages,
        **kwargs
    )


def create_hybrid_config(team_name: str, stages: List[str] = None, **kwargs) -> ContextGenerationConfig:
    """创建混合模式的配置"""
    if stages is None:
        stages = ["requirements", "business-model", "solution", "structure", "tasks", "common-tasks", "constraints"]
    
    return ContextGenerationConfig(
        team_name=team_name,
        mode=ContextMode.HYBRID,
        include_framework_stages=stages,
        **kwargs
    ) 