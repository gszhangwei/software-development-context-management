"""
ContextX Markdown存储引擎

负责处理Markdown格式的文件存储和解析，支持：
- 记忆条目的追加和检索
- 上下文文件的结构化管理
- 元数据的嵌入和提取
- 内容的搜索和过滤
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass


@dataclass
class MemoryEntry:
    """记忆条目数据结构"""
    id: str
    timestamp: str
    content: str
    tags: List[str]
    project: str = 'general'
    importance: int = 3
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ContextSection:
    """上下文章节数据结构"""
    title: str
    content: str
    level: int = 2
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MarkdownEngine:
    """Markdown存储引擎"""
    
    def __init__(self):
        # 修改正则表达式以支持多行内容
        self.memory_entry_pattern = re.compile(
            r'### 记忆项目 #(\w+)\n(.*?)(?=### 记忆项目 #|\Z)',
            re.MULTILINE | re.DOTALL
        )
        self.metadata_pattern = re.compile(r'- \*\*([^*]+)\*\*:\s*(.+?)(?=\n- \*\*|\Z)', re.DOTALL)
        
    def load_memories(self, file_path: Path) -> List[MemoryEntry]:
        """
        读取记忆文件并解析为记忆条目列表
        
        Args:
            file_path: 记忆文件路径
            
        Returns:
            记忆条目列表
        """
        if not file_path.exists():
            return []
        
        content = file_path.read_text(encoding='utf-8')
        entries = []
        
        # 使用正则表达式匹配记忆条目
        matches = self.memory_entry_pattern.findall(content)
        
        for entry_id, entry_content in matches:
            entry = self._parse_memory_entry(entry_id, entry_content)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_memory_entry(self, entry_id: str, entry_content: str) -> Optional[MemoryEntry]:
        """解析单个记忆条目"""
        metadata_matches = self.metadata_pattern.findall(entry_content)
        
        entry_data = {'id': entry_id}
        
        for key, value in metadata_matches:
            key = key.strip()
            value = value.strip()
            
            if key == '时间':
                entry_data['timestamp'] = value
            elif key == '内容':
                entry_data['content'] = value
            elif key == '标签':
                # 解析标签，移除#符号
                tags = [tag.strip().lstrip('#') for tag in value.split() if tag.strip()]
                entry_data['tags'] = tags
            elif key == '项目':
                entry_data['project'] = value
            elif key == '重要性':
                # 计算星号数量
                importance = value.count('⭐')
                entry_data['importance'] = max(1, min(5, importance))
        
        # 验证必需字段
        required_fields = ['content', 'timestamp']
        if not all(field in entry_data for field in required_fields):
            return None
        
        # 设置默认值
        entry_data.setdefault('tags', [])
        entry_data.setdefault('project', 'general')
        entry_data.setdefault('importance', 3)
        
        return MemoryEntry(**entry_data)
    
    def append_memory_entry(self, file_path: Path, entry: MemoryEntry) -> None:
        """
        向记忆文件追加新的记忆条目
        
        Args:
            file_path: 记忆文件路径
            entry: 记忆条目
        """
        # 确保文件和目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果文件不存在，创建初始内容
        if not file_path.exists():
            self._initialize_memory_file(file_path)
        
        # 生成记忆条目的Markdown格式
        entry_markdown = self._format_memory_entry(entry)
        
        # 追加到文件
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(entry_markdown)
    
    def _initialize_memory_file(self, file_path: Path) -> None:
        """初始化记忆文件"""
        team_name = file_path.parent.parent.name  # 从路径推断团队名称
        memory_type = file_path.stem  # 记忆类型
        
        header = f"""# 团队记忆：{team_name.replace('-', ' ').title()}

## 元数据
- **团队**: {team_name}
- **创建时间**: {datetime.now().isoformat()}
- **最后更新**: {datetime.now().isoformat()}
- **记忆类型**: {memory_type}

## 记忆条目

"""
        file_path.write_text(header, encoding='utf-8')
    
    def _format_memory_entry(self, entry: MemoryEntry) -> str:
        """格式化记忆条目为Markdown"""
        tags_str = ' '.join(f'#{tag}' for tag in entry.tags)
        importance_str = '⭐' * entry.importance
        
        return f"""### 记忆项目 #{entry.id}
- **时间**: {entry.timestamp}
- **内容**: {entry.content}
- **标签**: {tags_str}
- **项目**: {entry.project}
- **重要性**: {importance_str}

"""
    
    def update_memory_metadata(self, file_path: Path) -> None:
        """更新记忆文件的元数据"""
        if not file_path.exists():
            return
        
        content = file_path.read_text(encoding='utf-8')
        
        # 更新最后更新时间
        updated_content = re.sub(
            r'- \*\*最后更新\*\*: [^\n]+',
            f'- **最后更新**: {datetime.now().isoformat()}',
            content
        )
        
        if updated_content != content:
            file_path.write_text(updated_content, encoding='utf-8')
    
    def search_memories(self, entries: List[MemoryEntry], query: str = None, 
                       tags: List[str] = None, project: str = None,
                       min_importance: int = None) -> List[MemoryEntry]:
        """
        搜索记忆条目
        
        Args:
            entries: 记忆条目列表
            query: 搜索查询
            tags: 标签过滤
            project: 项目过滤
            min_importance: 最小重要性过滤
            
        Returns:
            匹配的记忆条目列表
        """
        filtered = entries.copy()
        
        # 按查询内容过滤
        if query:
            query_lower = query.lower()
            filtered = [
                entry for entry in filtered
                if query_lower in entry.content.lower() or
                   any(query_lower in tag.lower() for tag in entry.tags)
            ]
        
        # 按标签过滤
        if tags:
            tags_lower = [tag.lower() for tag in tags]
            filtered = [
                entry for entry in filtered
                if any(tag.lower() in tags_lower for tag in entry.tags)
            ]
        
        # 按项目过滤
        if project:
            filtered = [
                entry for entry in filtered
                if entry.project.lower() == project.lower()
            ]
        
        # 按重要性过滤
        if min_importance is not None:
            filtered = [
                entry for entry in filtered
                if entry.importance >= min_importance
            ]
        
        # 按重要性和时间排序
        filtered.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
        
        return filtered
    
    def read_context_file(self, file_path: Path) -> Dict[str, Any]:
        """
        读取上下文文件并解析结构
        
        Args:
            file_path: 上下文文件路径
            
        Returns:
            上下文数据字典
        """
        if not file_path.exists():
            return {'sections': [], 'metadata': {}}
        
        content = file_path.read_text(encoding='utf-8')
        
        # 解析标题和内容
        sections = self._parse_markdown_sections(content)
        
        # 提取元数据
        metadata = self._extract_context_metadata(content)
        
        return {
            'sections': sections,
            'metadata': metadata,
            'raw_content': content
        }
    
    def _parse_markdown_sections(self, content: str) -> List[ContextSection]:
        """解析Markdown章节"""
        sections = []
        
        # 匹配标题行
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # 检查是否是标题行
            if line.startswith('#'):
                # 保存前一个章节
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    sections.append(current_section)
                
                # 开始新章节
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                current_section = ContextSection(title=title, content='', level=level)
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        # 保存最后一个章节
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            sections.append(current_section)
        
        return sections
    
    def _extract_context_metadata(self, content: str) -> Dict[str, Any]:
        """从上下文中提取元数据"""
        metadata = {}
        
        # 查找元数据部分
        metadata_match = re.search(r'## 元数据\n((?:- \*\*[^*]+\*\*:[^\n]*\n?)+)', content)
        if metadata_match:
            metadata_content = metadata_match.group(1)
            metadata_matches = self.metadata_pattern.findall(metadata_content)
            
            for key, value in metadata_matches:
                metadata[key] = value.strip()
        
        return metadata
    
    def write_context_file(self, file_path: Path, sections: List[ContextSection], 
                          metadata: Dict[str, Any] = None) -> None:
        """
        写入上下文文件
        
        Args:
            file_path: 文件路径
            sections: 章节列表
            metadata: 元数据
        """
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 构建内容
        content_parts = []
        
        # 添加主标题
        main_title = file_path.stem.replace('-', ' ').title() + '上下文'
        content_parts.append(f'# {main_title}\n')
        
        # 添加元数据
        if metadata:
            content_parts.append('## 元数据')
            for key, value in metadata.items():
                content_parts.append(f'- **{key}**: {value}')
            content_parts.append('')
        
        # 添加章节
        for section in sections:
            header = '#' * section.level + ' ' + section.title
            content_parts.append(header)
            if section.content:
                content_parts.append(section.content)
            content_parts.append('')
        
        # 写入文件
        content = '\n'.join(content_parts)
        file_path.write_text(content, encoding='utf-8')
    
    def append_context_section(self, file_path: Path, section: ContextSection) -> None:
        """向上下文文件追加新章节"""
        # 如果文件不存在，先创建
        if not file_path.exists():
            self.write_context_file(file_path, [section])
            return
        
        # 读取现有内容
        current_content = file_path.read_text(encoding='utf-8')
        
        # 追加新章节
        header = '#' * section.level + ' ' + section.title
        new_content = f'\n{header}\n{section.content}\n'
        
        # 写回文件
        file_path.write_text(current_content + new_content, encoding='utf-8')
    
    def generate_memory_id(self) -> str:
        """生成记忆条目ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        import random
        suffix = ''.join(random.choices('0123456789ABCDEF', k=4))
        return f'{timestamp}_{suffix}'
    
    def load_memories(self, file_path: Path) -> List[MemoryEntry]:
        """
        读取记忆文件并解析为记忆条目列表
        
        Args:
            file_path: 记忆文件路径
            
        Returns:
            记忆条目列表
        """
        if not file_path.exists():
            return []
        
        content = file_path.read_text(encoding='utf-8')
        entries = []
        
        # 使用正则表达式匹配记忆条目
        matches = self.memory_entry_pattern.findall(content)
        
        for entry_id, entry_content in matches:
            entry = self._parse_memory_entry(entry_id, entry_content)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_memory_content(self, memory_id: str, content: str) -> Optional[MemoryEntry]:
        """解析记忆内容"""
        lines = content.split('\n')
        
        # 提取元数据
        tags = []
        project = 'general'
        importance = 3
        timestamp = datetime.now().isoformat()
        metadata = {}
        
        # 查找元数据行
        content_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('**Tags:**'):
                tag_str = line.replace('**Tags:**', '').strip()
                tags = [tag.strip() for tag in tag_str.split(',') if tag.strip()]
            elif line.startswith('**Project:**'):
                project = line.replace('**Project:**', '').strip()
            elif line.startswith('**Importance:**'):
                importance_str = line.replace('**Importance:**', '').strip()
                importance = len([c for c in importance_str if c == '⭐'])
            elif line.startswith('**Timestamp:**'):
                timestamp = line.replace('**Timestamp:**', '').strip()
            elif line and not line.startswith('**'):
                content_lines.append(line)
        
        memory_content = '\n'.join(content_lines).strip()
        
        if not memory_content:
            return None
        
        return MemoryEntry(
            id=memory_id,
            timestamp=timestamp,
            content=memory_content,
            tags=tags,
            project=project,
            importance=importance,
            metadata=metadata
        ) 