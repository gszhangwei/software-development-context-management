"""
PromptX团队记忆管理命令

负责团队记忆的保存、检索和管理，支持：
- 记忆条目的保存和追加
- 记忆列表的查看和过滤
- 记忆的导出和备份
- 不同类型记忆的管理（声明性、程序性、情景性）
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .base_command import BaseCommand, CommandResult, TeamCommandMixin
from ..core.markdown_engine import MemoryEntry


class TeamMemoryCommand(BaseCommand, TeamCommandMixin):
    """团队记忆管理命令"""
    
    @property
    def name(self) -> str:
        return "team_memory"
    
    @property
    def description(self) -> str:
        return "管理团队记忆，支持保存、列表、导出等操作"
    
    def execute(self, team_name: str, action: str, content: str = None, 
                tags: str = None, project: str = None, memory_type: str = 'declarative',
                **kwargs) -> CommandResult:
        """
        执行团队记忆命令
        
        Args:
            team_name: 团队名称
            action: 操作类型 (save, list, export)
            content: 记忆内容（save操作时必需）
            tags: 标签字符串
            project: 项目名称
            memory_type: 记忆类型 (declarative, procedural, episodic)
            **kwargs: 其他参数
            
        Returns:
            CommandResult: 命令执行结果
        """
        try:
            # 验证团队存在
            team_check = self.ensure_team_exists(team_name)
            if not team_check.success:
                return team_check
            
            # 根据操作类型分发
            if action == 'save':
                return self._save_memory(team_name, content, tags, project, memory_type, **kwargs)
            elif action == 'list':
                return self._list_memories(team_name, memory_type, **kwargs)
            elif action == 'export':
                return self._export_memories(team_name, memory_type, **kwargs)
            else:
                return CommandResult(
                    success=False,
                    message=f"❌ 不支持的操作: {action}\n\n📋 支持的操作: save, list, export"
                )
                
        except Exception as e:
            return self.handle_error(e, f"执行团队记忆命令 {action}")
    
    def _save_memory(self, team_name: str, content: str, tags: str, 
                    project: str, memory_type: str, importance: int = 3) -> CommandResult:
        """
        保存记忆条目
        
        Args:
            team_name: 团队名称
            content: 记忆内容
            tags: 标签字符串
            project: 项目名称
            memory_type: 记忆类型
            importance: 重要性等级 (1-5)
            
        Returns:
            CommandResult: 保存结果
        """
        if not content:
            return CommandResult(
                success=False,
                message="❌ 记忆内容不能为空\n\n💡 使用方法: team_memory <team> save \"记忆内容\" [--tags=\"标签\"] [--project=\"项目\"]"
            )
        
        try:
            # 生成记忆条目
            entry = MemoryEntry(
                id=self.markdown_engine.generate_memory_id(),
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                content=content.strip(),
                tags=self.parse_tags(tags) if tags else [],
                project=project or 'general',
                importance=max(1, min(5, importance))
            )
            
            # 获取记忆文件路径
            memory_path = self.directory_manager.get_memory_path(team_name, memory_type)
            
            # 处理情景记忆（episodic）的特殊情况
            if memory_type == 'episodic':
                if not project:
                    return CommandResult(
                        success=False,
                        message="❌ 情景记忆必须指定项目名称\n\n💡 使用: --project=\"项目名称\""
                    )
                
                # 情景记忆按项目分文件存储
                project_file = memory_path / f"{project}.md"
                memory_path = project_file
            
            # 保存记忆条目
            self.markdown_engine.append_memory_entry(memory_path, entry)
            
            # 更新元数据
            self.markdown_engine.update_memory_metadata(memory_path)
            
            # 构建成功消息
            tags_info = f" | 标签: {', '.join(entry.tags)}" if entry.tags else ""
            project_info = f" | 项目: {entry.project}"
            importance_info = f" | 重要性: {'⭐' * entry.importance}"
            
            success_message = self.format_success_message(
                "记忆保存",
                f"团队: {team_name} | 类型: {memory_type}{project_info}{tags_info}{importance_info}"
            )
            
            return CommandResult(
                success=True,
                message=success_message,
                data={
                    'entry_id': entry.id,
                    'team': team_name,
                    'memory_type': memory_type,
                    'file_path': str(memory_path)
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "保存记忆")
    
    def _list_memories(self, team_name: str, memory_type: str, 
                      query: str = None, tags: str = None, project: str = None,
                      limit: int = 20, min_importance: int = None) -> CommandResult:
        """
        列出记忆条目
        
        Args:
            team_name: 团队名称
            memory_type: 记忆类型
            query: 搜索查询
            tags: 标签过滤
            project: 项目过滤
            limit: 结果数量限制
            min_importance: 最小重要性
            
        Returns:
            CommandResult: 列表结果
        """
        try:
            # 读取记忆文件
            entries = self._load_team_memories(team_name, memory_type, project)
            
            # 应用过滤条件
            if query or tags or project or min_importance:
                tag_list = self.parse_tags(tags) if tags else None
                entries = self.markdown_engine.search_memories(
                    entries, query, tag_list, project, min_importance
                )
            
            # 限制结果数量
            if limit and len(entries) > limit:
                entries = entries[:limit]
                truncated_note = f"\n\n📌 显示前 {limit} 条结果，总共 {len(entries)} 条记忆"
            else:
                truncated_note = ""
            
            # 格式化输出
            if not entries:
                message = f"🧠 {team_name} 团队暂无匹配的{memory_type}记忆"
                if query or tags or project:
                    message += f"\n\n🔍 搜索条件: "
                    conditions = []
                    if query:
                        conditions.append(f"查询=\"{query}\"")
                    if tags:
                        conditions.append(f"标签=\"{tags}\"")
                    if project:
                        conditions.append(f"项目=\"{project}\"")
                    message += " | ".join(conditions)
            else:
                formatted_entries = self.format_memory_entries(entries)
                filter_info = self._format_filter_info(query, tags, project, min_importance)
                message = f"🧠 {team_name} 团队的{memory_type}记忆{filter_info}:\n\n{formatted_entries}{truncated_note}"
            
            return CommandResult(
                success=True,
                message=message,
                data={
                    'entries': [entry.__dict__ for entry in entries],
                    'count': len(entries),
                    'memory_type': memory_type
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "列出记忆")
    
    def _export_memories(self, team_name: str, memory_type: str, 
                        format_type: str = 'markdown', output_file: str = None) -> CommandResult:
        """
        导出记忆数据
        
        Args:
            team_name: 团队名称
            memory_type: 记忆类型
            format_type: 导出格式 (markdown, json)
            output_file: 输出文件路径
            
        Returns:
            CommandResult: 导出结果
        """
        try:
            # 读取记忆数据
            entries = self._load_team_memories(team_name, memory_type)
            
            if not entries:
                return CommandResult(
                    success=False,
                    message=f"❌ {team_name} 团队暂无{memory_type}记忆可导出"
                )
            
            # 生成输出文件名
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"{team_name}_{memory_type}_memories_{timestamp}.{format_type}"
            
            output_path = Path(output_file)
            
            # 根据格式导出
            if format_type == 'json':
                self._export_to_json(entries, output_path, team_name, memory_type)
            else:  # markdown
                self._export_to_markdown(entries, output_path, team_name, memory_type)
            
            return CommandResult(
                success=True,
                message=self.format_success_message(
                    "记忆导出",
                    f"{len(entries)}条记忆已导出到 {output_path}"
                ),
                data={
                    'output_file': str(output_path),
                    'entries_count': len(entries),
                    'format': format_type
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "导出记忆")
    
    def _load_team_memories(self, team_name: str, memory_type: str, 
                           project: str = None) -> List[MemoryEntry]:
        """加载团队记忆数据"""
        entries = []
        
        if memory_type == 'episodic':
            # 情景记忆按项目分文件
            episodic_path = self.directory_manager.get_memory_path(team_name, 'episodic')
            
            if project:
                # 加载特定项目的记忆
                project_file = episodic_path / f"{project}.md"
                if project_file.exists():
                    entries.extend(self.markdown_engine.read_memory_file(project_file))
            else:
                # 加载所有项目的记忆
                if episodic_path.exists():
                    for md_file in episodic_path.glob("*.md"):
                        entries.extend(self.markdown_engine.read_memory_file(md_file))
        else:
            # 声明性和程序性记忆
            memory_path = self.directory_manager.get_memory_path(team_name, memory_type)
            entries = self.markdown_engine.read_memory_file(memory_path)
        
        return entries
    
    def _format_filter_info(self, query: str, tags: str, project: str, 
                           min_importance: int) -> str:
        """格式化过滤信息"""
        conditions = []
        
        if query:
            conditions.append(f"查询=\"{query}\"")
        if tags:
            conditions.append(f"标签=\"{tags}\"")
        if project:
            conditions.append(f"项目=\"{project}\"")
        if min_importance:
            conditions.append(f"重要性≥{min_importance}")
        
        if conditions:
            return f" (过滤: {' | '.join(conditions)})"
        return ""
    
    def _export_to_json(self, entries: List[MemoryEntry], output_path: Path, 
                       team_name: str, memory_type: str) -> None:
        """导出为JSON格式"""
        import json
        
        export_data = {
            'meta': {
                'team': team_name,
                'memory_type': memory_type,
                'export_time': datetime.now().isoformat(),
                'entries_count': len(entries)
            },
            'entries': [entry.__dict__ for entry in entries]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def _export_to_markdown(self, entries: List[MemoryEntry], output_path: Path,
                           team_name: str, memory_type: str) -> None:
        """导出为Markdown格式"""
        lines = [
            f"# {team_name} 团队 - {memory_type} 记忆导出",
            "",
            f"- **导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **记忆类型**: {memory_type}",
            f"- **记忆条目数**: {len(entries)}",
            "",
            "## 记忆条目",
            ""
        ]
        
        for i, entry in enumerate(entries, 1):
            tags_str = ' '.join(f'#{tag}' for tag in entry.tags) if entry.tags else '无'
            importance_str = '⭐' * entry.importance
            
            lines.extend([
                f"### {i}. 记忆 #{entry.id}",
                "",
                f"- **时间**: {entry.timestamp}",
                f"- **项目**: {entry.project}",
                f"- **重要性**: {importance_str}",
                f"- **标签**: {tags_str}",
                "",
                f"**内容**: {entry.content}",
                "",
                "---",
                ""
            ])
        
        output_path.write_text('\n'.join(lines), encoding='utf-8') 