"""
PromptX上下文处理器

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
    
    def generate_context(self, config: ContextGenerationConfig) -> GeneratedContext:
        """
        生成结构化上下文
        
        Args:
            config: 上下文生成配置
        
        Returns:
            生成的上下文
        """
        # 验证团队存在
        if not self.directory_manager.team_exists(config.team_name):
            raise ValueError(f"Team '{config.team_name}' does not exist")
        
        team_path = self.directory_manager.get_team_path(config.team_name)
        
        # 根据模式生成上下文
        if config.mode == ContextMode.MEMORY_ONLY:
            return self._generate_memory_only_context(config, team_path)
        elif config.mode == ContextMode.FRAMEWORK_ONLY:
            return self._generate_framework_only_context(config, team_path)
        elif config.mode == ContextMode.HYBRID:
            return self._generate_hybrid_context(config, team_path)
        else:
            raise ValueError(f"Unsupported context mode: {config.mode}")
    
    def _generate_memory_only_context(self, config: ContextGenerationConfig, team_path: Path) -> GeneratedContext:
        """生成仅基于记忆的上下文"""
        memories = self._load_team_memories(team_path, config)
        
        content_sections = ["# Team Memory Context", ""]
        
        if memories:
            # 按类型组织记忆
            memory_by_type = self._group_memories_by_type(memories)
            
            for memory_type, type_memories in memory_by_type.items():
                if type_memories:
                    content_sections.extend([
                        f"## {memory_type.title()} Memory",
                        ""
                    ])
                    
                    for memory in type_memories:
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
        content_sections = ["# Seven Stage Framework Context", ""]
        
        # 加载概述
        overview_content = self._load_framework_stage("overview")
        if overview_content:
            content_sections.extend([
                "## Framework Overview",
                "",
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
    
    def _generate_hybrid_context(self, config: ContextGenerationConfig, team_path: Path) -> GeneratedContext:
        """生成混合模式上下文（记忆+框架）"""
        memories = self._load_team_memories(team_path, config)
        
        content_sections = ["# Hybrid Context: Framework + Memory", ""]
        
        # 1. 七阶段框架作为主体结构
        included_stages = []
        for stage in config.include_framework_stages:
            stage_content = self._load_framework_stage(stage)
            if stage_content:
                included_stages.append(stage)
                content_sections.extend([
                    stage_content,
                    ""
                ])
                
                # 2. 为每个阶段添加相关的记忆内容（仅在有记忆时显示）
                relevant_memories = self._find_memories_for_stage(memories, stage)
                if relevant_memories:
                    
                    for memory in relevant_memories[:3]:  # 限制每个阶段最多3个记忆
                        content_sections.extend([
                            f"**{memory.id}** ({memory.project})",
                            f"*Importance: {'⭐' * memory.importance}, Tags: {', '.join(memory.tags)}*",
                            "",
                            memory.content,
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
        
        # 4. 添加未分类的重要记忆（仅在有记忆时显示）
        if memories:  # 只有当有记忆时才尝试添加未匹配的记忆
            unmatched_memories = self._get_unmatched_memories(memories, config.include_framework_stages)
            if unmatched_memories:
                content_sections.extend([
                    "## Additional Team Experience",
                    ""
                ])
                
                for memory in unmatched_memories[:5]:  # 最多5个
                    content_sections.extend([
                        f"### {memory.id}",
                        f"**Project:** {memory.project}",
                        f"**Tags:** {', '.join(memory.tags)}",
                        "",
                        memory.content,
                        "",
                        "---",
                        ""
                    ])
        
        return GeneratedContext(
            team_name=config.team_name,
            mode=config.mode,
            content="\n".join(content_sections),
            source_memories=[m.id for m in memories],
            framework_stages=included_stages,
            metadata={
                'memory_count': len(memories),
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
                    f"### {stage.replace('-', ' ').title()}",
                    "",
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