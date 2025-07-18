"""
PromptX上下文处理器

负责将团队记忆、配置和模板转换为结构化的上下文，支持：
- 记忆内容的智能聚合和过滤
- 上下文的动态生成和优化
- 多源数据的融合和结构化
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


class ContextType(Enum):
    """上下文类型枚举"""
    REQUIREMENTS = "requirements"
    BUSINESS_MODEL = "business-model"
    SOLUTION = "solution"
    STRUCTURE = "structure"
    TASKS = "tasks"
    COMMON_TASKS = "common-tasks"
    CONSTRAINTS = "constraints"


@dataclass
class ContextGenerationConfig:
    """上下文生成配置"""
    team_name: str
    context_types: List[ContextType] = field(default_factory=list)
    include_memories: bool = True
    include_all_types: bool = False
    memory_filters: Dict[str, Any] = field(default_factory=dict)
    max_memory_items: int = 50
    memory_importance_threshold: int = 2
    project_scope: Optional[str] = None
    time_range: Optional[Tuple[str, str]] = None
    
    def __post_init__(self):
        if self.include_all_types:
            self.context_types = list(ContextType)


@dataclass
class GeneratedContext:
    """生成的上下文结果"""
    team_name: str
    context_type: ContextType
    content: str
    source_memories: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generation_time: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md_content = [
            f"# {self.context_type.value.replace('-', ' ').title()} Context",
            f"",
            f"**Team:** {self.team_name}",
            f"**Generated:** {self.generation_time}",
            ""
        ]
        
        if self.source_memories:
            md_content.extend([
                "## Source Memories",
                "",
                *[f"- {memory_id}" for memory_id in self.source_memories],
                ""
            ])
        
        md_content.extend([
            "## Content",
            "",
            self.content
        ])
        
        if self.metadata:
            md_content.extend([
                "",
                "## Metadata",
                "",
                f"```json",
                json.dumps(self.metadata, indent=2, ensure_ascii=False),
                "```"
            ])
        
        return "\n".join(md_content)


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
        
        # 上下文生成模板
        self.context_templates = {
            ContextType.REQUIREMENTS: self._generate_requirements_context,
            ContextType.BUSINESS_MODEL: self._generate_business_model_context,
            ContextType.SOLUTION: self._generate_solution_context,
            ContextType.STRUCTURE: self._generate_structure_context,
            ContextType.TASKS: self._generate_tasks_context,
            ContextType.COMMON_TASKS: self._generate_common_tasks_context,
            ContextType.CONSTRAINTS: self._generate_constraints_context,
        }
    
    def generate_context(self, config: ContextGenerationConfig) -> List[GeneratedContext]:
        """
        生成结构化上下文
        
        Args:
            config: 上下文生成配置
        
        Returns:
            生成的上下文列表
        """
        # 验证团队存在
        if not self.directory_manager.team_exists(config.team_name):
            raise ValueError(f"Team '{config.team_name}' does not exist")
        
        team_path = self.directory_manager.get_team_path(config.team_name)
        
        # 加载团队记忆
        memories = []
        if config.include_memories:
            memories = self._load_team_memories(team_path, config)
        
        # 生成各类型上下文
        generated_contexts = []
        for context_type in config.context_types:
            if context_type in self.context_templates:
                try:
                    context = self._generate_single_context(
                        context_type, config, memories, team_path
                    )
                    generated_contexts.append(context)
                except Exception as e:
                    print(f"Warning: Failed to generate {context_type.value} context: {e}")
        
        return generated_contexts
    
    def _load_team_memories(self, team_path: Path, config: ContextGenerationConfig) -> List[MemoryEntry]:
        """加载团队记忆"""
        memories = []
        
        # 加载声明性记忆
        declarative_path = team_path / "memory" / "declarative.md"
        if declarative_path.exists():
            declarative_memories = self.markdown_engine.load_memories(declarative_path)
            memories.extend(declarative_memories)
        
        # 加载程序性记忆
        procedural_path = team_path / "memory" / "procedural.md"
        if procedural_path.exists():
            procedural_memories = self.markdown_engine.load_memories(procedural_path)
            memories.extend(procedural_memories)
        
        # 加载情景性记忆
        episodic_dir = team_path / "memory" / "episodic"
        if episodic_dir.exists():
            for episodic_file in episodic_dir.glob("*.md"):
                episodic_memories = self.markdown_engine.load_memories(episodic_file)
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
    
    def _generate_single_context(self, context_type: ContextType, config: ContextGenerationConfig, 
                                memories: List[MemoryEntry], team_path: Path) -> GeneratedContext:
        """生成单个类型的上下文"""
        generator = self.context_templates[context_type]
        
        # 生成上下文内容
        content = generator(config, memories, team_path)
        
        # 提取相关记忆ID
        source_memories = [m.id for m in memories if self._is_memory_relevant(m, context_type)]
        
        # 生成元数据
        metadata = {
            'memory_count': len(source_memories),
            'total_available_memories': len(memories),
            'generation_config': {
                'include_memories': config.include_memories,
                'memory_importance_threshold': config.memory_importance_threshold,
                'project_scope': config.project_scope
            }
        }
        
        return GeneratedContext(
            team_name=config.team_name,
            context_type=context_type,
            content=content,
            source_memories=source_memories,
            metadata=metadata
        )
    
    def _is_memory_relevant(self, memory: MemoryEntry, context_type: ContextType) -> bool:
        """判断记忆是否与特定上下文类型相关"""
        # 基于标签的相关性判断
        relevance_keywords = {
            ContextType.REQUIREMENTS: ['requirement', 'need', 'spec', 'demand', '需求', '规格'],
            ContextType.BUSINESS_MODEL: ['business', 'model', 'revenue', 'customer', '商业', '模式'],
            ContextType.SOLUTION: ['solution', 'approach', 'method', 'design', '解决方案', '设计'],
            ContextType.STRUCTURE: ['architecture', 'structure', 'component', 'module', '架构', '结构'],
            ContextType.TASKS: ['task', 'todo', 'action', 'work', '任务', '工作'],
            ContextType.COMMON_TASKS: ['common', 'general', 'standard', 'template', '通用', '标准'],
            ContextType.CONSTRAINTS: ['constraint', 'limit', 'restriction', 'rule', '约束', '限制']
        }
        
        keywords = relevance_keywords.get(context_type, [])
        
        # 检查标签
        for tag in memory.tags:
            if any(keyword.lower() in tag.lower() for keyword in keywords):
                return True
        
        # 检查内容
        content_lower = memory.content.lower()
        return any(keyword.lower() in content_lower for keyword in keywords)
    
    # 各类型上下文生成器
    def _generate_requirements_context(self, config: ContextGenerationConfig, 
                                     memories: List[MemoryEntry], team_path: Path) -> str:
        """生成需求分析上下文"""
        sections = []
        
        # 从现有文件加载基础内容
        requirements_file = team_path / "context" / "requirements.md"
        if requirements_file.exists():
            base_content = requirements_file.read_text(encoding='utf-8')
            sections.append("## Existing Requirements")
            sections.append(base_content)
        
        # 从记忆中提取需求相关内容
        requirement_memories = [
            m for m in memories 
            if self._is_memory_relevant(m, ContextType.REQUIREMENTS)
        ]
        
        if requirement_memories:
            sections.append("## Memory-Based Requirements")
            for memory in requirement_memories[:10]:  # 限制数量
                sections.append(f"### {memory.id}")
                sections.append(f"**Tags:** {', '.join(memory.tags)}")
                sections.append(f"**Project:** {memory.project}")
                sections.append(f"**Importance:** {'⭐' * memory.importance}")
                sections.append("")
                sections.append(memory.content)
                sections.append("")
        
        return "\n".join(sections) if sections else "No requirements context available."
    
    def _generate_business_model_context(self, config: ContextGenerationConfig,
                                       memories: List[MemoryEntry], team_path: Path) -> str:
        """生成业务模型上下文"""
        sections = []
        
        business_file = team_path / "context" / "business-model.md"
        if business_file.exists():
            base_content = business_file.read_text(encoding='utf-8')
            sections.append("## Business Model Framework")
            sections.append(base_content)
        
        # 从记忆中提取业务相关内容
        business_memories = [
            m for m in memories 
            if self._is_memory_relevant(m, ContextType.BUSINESS_MODEL)
        ]
        
        if business_memories:
            sections.append("## Business Insights from Memory")
            for memory in business_memories[:8]:
                sections.append(f"### {memory.id}")
                sections.append(memory.content)
                sections.append("")
        
        return "\n".join(sections) if sections else "No business model context available."
    
    def _generate_solution_context(self, config: ContextGenerationConfig,
                                 memories: List[MemoryEntry], team_path: Path) -> str:
        """生成解决方案上下文"""
        sections = []
        
        solution_file = team_path / "context" / "solution.md"
        if solution_file.exists():
            base_content = solution_file.read_text(encoding='utf-8')
            sections.append("## Solution Framework")
            sections.append(base_content)
        
        solution_memories = [
            m for m in memories 
            if self._is_memory_relevant(m, ContextType.SOLUTION)
        ]
        
        if solution_memories:
            sections.append("## Solution Approaches from Experience")
            for memory in solution_memories[:10]:
                sections.append(f"### {memory.id}")
                sections.append(f"**Applied to:** {memory.project}")
                sections.append(memory.content)
                sections.append("")
        
        return "\n".join(sections) if sections else "No solution context available."
    
    def _generate_structure_context(self, config: ContextGenerationConfig,
                                  memories: List[MemoryEntry], team_path: Path) -> str:
        """生成架构设计上下文"""
        sections = []
        
        structure_file = team_path / "context" / "structure.md"
        if structure_file.exists():
            base_content = structure_file.read_text(encoding='utf-8')
            sections.append("## Architecture Framework")
            sections.append(base_content)
        
        structure_memories = [
            m for m in memories 
            if self._is_memory_relevant(m, ContextType.STRUCTURE)
        ]
        
        if structure_memories:
            sections.append("## Architecture Patterns from Experience")
            for memory in structure_memories[:8]:
                sections.append(f"### {memory.id}")
                sections.append(memory.content)
                sections.append("")
        
        return "\n".join(sections) if sections else "No structure context available."
    
    def _generate_tasks_context(self, config: ContextGenerationConfig,
                              memories: List[MemoryEntry], team_path: Path) -> str:
        """生成任务编排上下文"""
        sections = []
        
        tasks_file = team_path / "context" / "tasks.md"
        if tasks_file.exists():
            base_content = tasks_file.read_text(encoding='utf-8')
            sections.append("## Task Framework")
            sections.append(base_content)
        
        task_memories = [
            m for m in memories 
            if self._is_memory_relevant(m, ContextType.TASKS)
        ]
        
        if task_memories:
            sections.append("## Task Experiences")
            for memory in task_memories[:12]:
                sections.append(f"### {memory.id}")
                sections.append(f"**Project:** {memory.project}")
                sections.append(memory.content)
                sections.append("")
        
        return "\n".join(sections) if sections else "No tasks context available."
    
    def _generate_common_tasks_context(self, config: ContextGenerationConfig,
                                     memories: List[MemoryEntry], team_path: Path) -> str:
        """生成通用任务上下文"""
        sections = []
        
        common_tasks_file = team_path / "context" / "common-tasks.md"
        if common_tasks_file.exists():
            base_content = common_tasks_file.read_text(encoding='utf-8')
            sections.append("## Common Tasks Framework")
            sections.append(base_content)
        
        common_memories = [
            m for m in memories 
            if self._is_memory_relevant(m, ContextType.COMMON_TASKS)
        ]
        
        if common_memories:
            sections.append("## Common Task Patterns")
            for memory in common_memories[:10]:
                sections.append(f"### {memory.id}")
                sections.append(memory.content)
                sections.append("")
        
        return "\n".join(sections) if sections else "No common tasks context available."
    
    def _generate_constraints_context(self, config: ContextGenerationConfig,
                                    memories: List[MemoryEntry], team_path: Path) -> str:
        """生成约束条件上下文"""
        sections = []
        
        constraints_file = team_path / "context" / "constraints.md"
        if constraints_file.exists():
            base_content = constraints_file.read_text(encoding='utf-8')
            sections.append("## Constraints Framework")
            sections.append(base_content)
        
        constraint_memories = [
            m for m in memories 
            if self._is_memory_relevant(m, ContextType.CONSTRAINTS)
        ]
        
        if constraint_memories:
            sections.append("## Known Constraints")
            for memory in constraint_memories[:8]:
                sections.append(f"### {memory.id}")
                sections.append(f"**Scope:** {memory.project}")
                sections.append(memory.content)
                sections.append("")
        
        return "\n".join(sections) if sections else "No constraints context available." 