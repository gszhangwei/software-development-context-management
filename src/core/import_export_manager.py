"""
PromptX数据导入导出管理器

提供团队数据的导入导出功能，包括：
- 多种格式支持（JSON、Markdown、CSV、ZIP）
- 完整团队数据备份和恢复
- 选择性数据导出
- 跨系统数据迁移
"""

import json
import csv
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime
from dataclasses import dataclass, field

from .directory_manager import DirectoryManager
from .markdown_engine import MarkdownEngine, MemoryEntry
from .template_engine import TemplateEngine
from .collaboration_manager import CollaborationManager


@dataclass
class ExportConfig:
    """导出配置"""
    include_memories: bool = True
    include_contexts: bool = True
    include_templates: bool = True
    include_collaboration: bool = True
    include_config: bool = True
    export_format: str = "zip"  # zip, json, markdown
    memory_filters: Dict[str, Any] = field(default_factory=dict)
    date_range: Optional[tuple] = None
    compress: bool = True


@dataclass
class ImportConfig:
    """导入配置"""
    overwrite_existing: bool = False
    merge_memories: bool = True
    merge_templates: bool = True
    create_backup: bool = True
    validate_data: bool = True
    import_collaboration: bool = True


class ImportExportManager:
    """数据导入导出管理器"""
    
    def __init__(self, base_path: Path):
        """
        初始化导入导出管理器
        
        Args:
            base_path: 基础路径
        """
        self.base_path = Path(base_path)
        self.directory_manager = DirectoryManager(base_path)
        self.markdown_engine = MarkdownEngine()
        self.template_engine = TemplateEngine(base_path)
        self.collaboration_manager = CollaborationManager(base_path)
        
        # 备份目录
        self.backup_dir = self.base_path / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 导出目录
        self.export_dir = self.base_path / "exports"
        self.export_dir.mkdir(exist_ok=True)
    
    def export_team_data(self, team_name: str, config: ExportConfig, 
                        export_path: Optional[Path] = None) -> Path:
        """
        导出团队数据
        
        Args:
            team_name: 团队名称
            config: 导出配置
            export_path: 导出路径（可选）
            
        Returns:
            导出文件路径
        """
        if not self.directory_manager.team_exists(team_name):
            raise ValueError(f"Team '{team_name}' does not exist")
        
        # 生成导出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if export_path is None:
            if config.export_format == "zip":
                export_path = self.export_dir / f"{team_name}_export_{timestamp}.zip"
            elif config.export_format == "json":
                export_path = self.export_dir / f"{team_name}_export_{timestamp}.json"
            else:
                export_path = self.export_dir / f"{team_name}_export_{timestamp}"
                export_path.mkdir(exist_ok=True)
        
        # 收集要导出的数据
        export_data = self._collect_team_data(team_name, config)
        
        # 根据格式导出
        if config.export_format == "zip":
            self._export_as_zip(export_data, export_path, team_name)
        elif config.export_format == "json":
            self._export_as_json(export_data, export_path)
        else:  # markdown
            self._export_as_markdown(export_data, export_path, team_name)
        
        return export_path
    
    def import_team_data(self, import_path: Path, team_name: str, 
                        config: ImportConfig) -> Dict[str, Any]:
        """
        导入团队数据
        
        Args:
            import_path: 导入文件路径
            team_name: 目标团队名称
            config: 导入配置
            
        Returns:
            导入结果
        """
        if not import_path.exists():
            raise ValueError(f"Import file '{import_path}' does not exist")
        
        # 创建备份
        if config.create_backup and self.directory_manager.team_exists(team_name):
            backup_path = self._create_team_backup(team_name)
            print(f"Backup created: {backup_path}")
        
        # 读取导入数据
        import_data = self._read_import_data(import_path)
        
        # 验证数据
        if config.validate_data:
            validation_result = self._validate_import_data(import_data)
            if not validation_result['valid']:
                raise ValueError(f"Data validation failed: {validation_result['errors']}")
        
        # 执行导入
        import_result = self._perform_import(import_data, team_name, config)
        
        return import_result
    
    def create_full_system_backup(self) -> Path:
        """
        创建完整系统备份
        
        Returns:
            备份文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"full_system_backup_{timestamp}.zip"
        
        # 创建ZIP备份
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 备份所有团队数据
            teams_dir = self.base_path / "teams"
            if teams_dir.exists():
                for team_dir in teams_dir.iterdir():
                    if team_dir.is_dir():
                        for file_path in team_dir.rglob("*"):
                            if file_path.is_file():
                                arcname = file_path.relative_to(self.base_path)
                                zipf.write(file_path, arcname)
            
            # 备份协作数据
            collaboration_dir = self.base_path / "collaboration"
            if collaboration_dir.exists():
                for file_path in collaboration_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.base_path)
                        zipf.write(file_path, arcname)
            
            # 备份模板
            templates_dir = self.base_path / "templates"
            if templates_dir.exists():
                for file_path in templates_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.base_path)
                        zipf.write(file_path, arcname)
        
        return backup_path
    
    def restore_from_backup(self, backup_path: Path, target_path: Optional[Path] = None) -> bool:
        """
        从备份恢复系统
        
        Args:
            backup_path: 备份文件路径
            target_path: 目标路径（可选，默认为当前base_path）
            
        Returns:
            恢复是否成功
        """
        if not backup_path.exists():
            raise ValueError(f"Backup file '{backup_path}' does not exist")
        
        if target_path is None:
            target_path = self.base_path
        
        try:
            # 解压备份文件
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(target_path)
            
            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False
    
    def export_memories_to_csv(self, team_name: str, csv_path: Path,
                              filters: Optional[Dict[str, Any]] = None) -> int:
        """
        导出记忆到CSV文件
        
        Args:
            team_name: 团队名称
            csv_path: CSV文件路径
            filters: 过滤器
            
        Returns:
            导出的记忆数量
        """
        if not self.directory_manager.team_exists(team_name):
            raise ValueError(f"Team '{team_name}' does not exist")
        
        # 加载团队记忆
        memories = self._load_team_memories(team_name)
        
        # 应用过滤器
        if filters:
            memories = self._apply_memory_filters(memories, filters)
        
        # 写入CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'timestamp', 'content', 'tags', 'project', 'importance']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for memory in memories:
                writer.writerow({
                    'id': memory.id,
                    'timestamp': memory.timestamp,
                    'content': memory.content,
                    'tags': ','.join(memory.tags),
                    'project': memory.project,
                    'importance': memory.importance
                })
        
        return len(memories)
    
    def import_memories_from_csv(self, team_name: str, csv_path: Path) -> int:
        """
        从CSV文件导入记忆
        
        Args:
            team_name: 团队名称
            csv_path: CSV文件路径
            
        Returns:
            导入的记忆数量
        """
        if not csv_path.exists():
            raise ValueError(f"CSV file '{csv_path}' does not exist")
        
        if not self.directory_manager.team_exists(team_name):
            raise ValueError(f"Team '{team_name}' does not exist")
        
        imported_count = 0
        team_path = self.directory_manager.get_team_path(team_name)
        
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    memory = MemoryEntry(
                        id=row.get('id', f"imported_{datetime.now().strftime('%Y%m%d%H%M%S')}_{imported_count}"),
                        timestamp=row.get('timestamp', datetime.now().isoformat()),
                        content=row.get('content', ''),
                        tags=row.get('tags', '').split(',') if row.get('tags') else [],
                        project=row.get('project', 'general'),
                        importance=int(row.get('importance', 3))
                    )
                    
                    # 保存记忆
                    memory_file = team_path / "memory" / "imported.md"
                    self.markdown_engine.append_memory(memory_file, memory)
                    imported_count += 1
                    
                except Exception as e:
                    print(f"Failed to import memory from row {reader.line_num}: {e}")
        
        return imported_count
    
    def _collect_team_data(self, team_name: str, config: ExportConfig) -> Dict[str, Any]:
        """收集团队数据"""
        team_path = self.directory_manager.get_team_path(team_name)
        export_data = {
            'team_name': team_name,
            'export_timestamp': datetime.now().isoformat(),
            'export_config': config.__dict__
        }
        
        # 收集团队配置
        if config.include_config:
            config_file = team_path / "config.json"
            if config_file.exists():
                export_data['team_config'] = json.loads(config_file.read_text(encoding='utf-8'))
        
        # 收集记忆数据
        if config.include_memories:
            memories = self._load_team_memories(team_name)
            if config.memory_filters:
                memories = self._apply_memory_filters(memories, config.memory_filters)
            
            export_data['memories'] = [
                {
                    'id': memory.id,
                    'timestamp': memory.timestamp,
                    'content': memory.content,
                    'tags': memory.tags,
                    'project': memory.project,
                    'importance': memory.importance,
                    'metadata': memory.metadata
                }
                for memory in memories
            ]
        
        # 收集上下文数据
        if config.include_contexts:
            contexts = {}
            context_dir = team_path / "context"
            if context_dir.exists():
                for context_file in context_dir.glob("*.md"):
                    contexts[context_file.stem] = context_file.read_text(encoding='utf-8')
            export_data['contexts'] = contexts
        
        # 收集模板数据
        if config.include_templates:
            templates = []
            for template_name in self.template_engine.list_templates():
                template_info = self.template_engine.get_template_info(template_name)
                if template_info:
                    templates.append(template_info)
            export_data['templates'] = templates
        
        # 收集协作数据
        if config.include_collaboration:
            collaboration_data = {
                'permissions': [perm.to_dict() for perm in self.collaboration_manager.list_team_permissions(team_name)],
                'shared_resources': self.collaboration_manager.get_shared_resources(team_name)
            }
            export_data['collaboration'] = collaboration_data
        
        return export_data
    
    def _export_as_zip(self, export_data: Dict[str, Any], export_path: Path, team_name: str):
        """导出为ZIP格式"""
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加JSON元数据
            metadata = {
                'export_info': {
                    'team_name': export_data['team_name'],
                    'export_timestamp': export_data['export_timestamp'],
                    'export_config': export_data['export_config']
                }
            }
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False))
            
            # 添加团队配置
            if 'team_config' in export_data:
                zipf.writestr("team_config.json", json.dumps(export_data['team_config'], indent=2, ensure_ascii=False))
            
            # 添加记忆数据
            if 'memories' in export_data:
                zipf.writestr("memories.json", json.dumps(export_data['memories'], indent=2, ensure_ascii=False))
                
                # 同时创建Markdown格式的记忆
                memories_md = self._memories_to_markdown(export_data['memories'])
                zipf.writestr("memories.md", memories_md)
            
            # 添加上下文文件
            if 'contexts' in export_data:
                for context_name, context_content in export_data['contexts'].items():
                    zipf.writestr(f"contexts/{context_name}.md", context_content)
            
            # 添加模板
            if 'templates' in export_data:
                zipf.writestr("templates.json", json.dumps(export_data['templates'], indent=2, ensure_ascii=False))
            
            # 添加协作数据
            if 'collaboration' in export_data:
                zipf.writestr("collaboration.json", json.dumps(export_data['collaboration'], indent=2, ensure_ascii=False))
    
    def _export_as_json(self, export_data: Dict[str, Any], export_path: Path):
        """导出为JSON格式"""
        export_path.write_text(
            json.dumps(export_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    def _export_as_markdown(self, export_data: Dict[str, Any], export_path: Path, team_name: str):
        """导出为Markdown格式"""
        # 创建目录结构
        export_path.mkdir(exist_ok=True)
        
        # 创建README
        readme_content = f"""# {team_name} Export
        
Export Date: {export_data['export_timestamp']}

## Contents

- memories.md - Team memories
- contexts/ - Context files
- team_config.json - Team configuration
- collaboration.json - Collaboration data
"""
        (export_path / "README.md").write_text(readme_content, encoding='utf-8')
        
        # 导出记忆
        if 'memories' in export_data:
            memories_md = self._memories_to_markdown(export_data['memories'])
            (export_path / "memories.md").write_text(memories_md, encoding='utf-8')
        
        # 导出上下文
        if 'contexts' in export_data:
            contexts_dir = export_path / "contexts"
            contexts_dir.mkdir(exist_ok=True)
            for context_name, context_content in export_data['contexts'].items():
                (contexts_dir / f"{context_name}.md").write_text(context_content, encoding='utf-8')
        
        # 导出配置文件
        if 'team_config' in export_data:
            (export_path / "team_config.json").write_text(
                json.dumps(export_data['team_config'], indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        
        # 导出协作数据
        if 'collaboration' in export_data:
            (export_path / "collaboration.json").write_text(
                json.dumps(export_data['collaboration'], indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
    
    def _memories_to_markdown(self, memories: List[Dict[str, Any]]) -> str:
        """将记忆转换为Markdown格式"""
        md_lines = ["# Team Memories", ""]
        
        for memory in memories:
            md_lines.extend([
                f"## Memory: {memory['id']}",
                "",
                f"**Timestamp:** {memory['timestamp']}",
                f"**Tags:** {', '.join(memory['tags'])}",
                f"**Project:** {memory['project']}",
                f"**Importance:** {'⭐' * memory['importance']}",
                "",
                memory['content'],
                "",
                "---",
                ""
            ])
        
        return '\n'.join(md_lines)
    
    def _read_import_data(self, import_path: Path) -> Dict[str, Any]:
        """读取导入数据"""
        if import_path.suffix == '.zip':
            return self._read_zip_import(import_path)
        elif import_path.suffix == '.json':
            return json.loads(import_path.read_text(encoding='utf-8'))
        else:
            # 假设是目录格式
            return self._read_directory_import(import_path)
    
    def _read_zip_import(self, zip_path: Path) -> Dict[str, Any]:
        """读取ZIP格式的导入数据"""
        import_data = {}
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # 读取元数据
            if "metadata.json" in zipf.namelist():
                metadata = json.loads(zipf.read("metadata.json").decode('utf-8'))
                import_data.update(metadata)
            
            # 读取各种数据文件
            for filename in zipf.namelist():
                if filename.endswith('.json') and filename != 'metadata.json':
                    key = filename.replace('.json', '')
                    import_data[key] = json.loads(zipf.read(filename).decode('utf-8'))
        
        return import_data
    
    def _read_directory_import(self, dir_path: Path) -> Dict[str, Any]:
        """读取目录格式的导入数据"""
        import_data = {}
        
        # 读取JSON文件
        for json_file in dir_path.glob("*.json"):
            key = json_file.stem
            import_data[key] = json.loads(json_file.read_text(encoding='utf-8'))
        
        # 读取Markdown文件
        if (dir_path / "memories.md").exists():
            import_data['memories_md'] = (dir_path / "memories.md").read_text(encoding='utf-8')
        
        return import_data
    
    def _validate_import_data(self, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证导入数据"""
        validation_result = {'valid': True, 'errors': [], 'warnings': []}
        
        # 检查必需字段
        if 'team_name' not in import_data and 'export_info' not in import_data:
            validation_result['errors'].append("Missing team name information")
        
        # 验证记忆数据
        if 'memories' in import_data:
            for i, memory in enumerate(import_data['memories']):
                if not isinstance(memory, dict):
                    validation_result['errors'].append(f"Memory {i} is not a valid object")
                    continue
                
                required_fields = ['id', 'content']
                for field in required_fields:
                    if field not in memory:
                        validation_result['errors'].append(f"Memory {i} missing required field: {field}")
        
        validation_result['valid'] = len(validation_result['errors']) == 0
        return validation_result
    
    def _perform_import(self, import_data: Dict[str, Any], team_name: str, 
                       config: ImportConfig) -> Dict[str, Any]:
        """执行导入操作"""
        result = {
            'imported_memories': 0,
            'imported_contexts': 0,
            'imported_templates': 0,
            'errors': []
        }
        
        # 确保团队存在
        if not self.directory_manager.team_exists(team_name):
            if not config.overwrite_existing:
                raise ValueError(f"Team '{team_name}' does not exist and overwrite_existing is False")
            
            # 创建团队
            self.directory_manager.create_team(team_name, "Imported team", [])
        
        team_path = self.directory_manager.get_team_path(team_name)
        
        # 导入记忆
        if 'memories' in import_data and isinstance(import_data['memories'], list):
            for memory_data in import_data['memories']:
                try:
                    memory = MemoryEntry(
                        id=memory_data['id'],
                        timestamp=memory_data.get('timestamp', datetime.now().isoformat()),
                        content=memory_data['content'],
                        tags=memory_data.get('tags', []),
                        project=memory_data.get('project', 'general'),
                        importance=memory_data.get('importance', 3),
                        metadata=memory_data.get('metadata', {})
                    )
                    
                    # 保存记忆
                    memory_file = team_path / "memory" / "imported.md"
                    self.markdown_engine.append_memory(memory_file, memory)
                    result['imported_memories'] += 1
                    
                except Exception as e:
                    result['errors'].append(f"Failed to import memory {memory_data.get('id', 'unknown')}: {e}")
        
        # 导入上下文
        if 'contexts' in import_data and isinstance(import_data['contexts'], dict):
            context_dir = team_path / "context"
            context_dir.mkdir(exist_ok=True)
            
            for context_name, context_content in import_data['contexts'].items():
                try:
                    context_file = context_dir / f"{context_name}.md"
                    if config.overwrite_existing or not context_file.exists():
                        context_file.write_text(context_content, encoding='utf-8')
                        result['imported_contexts'] += 1
                except Exception as e:
                    result['errors'].append(f"Failed to import context {context_name}: {e}")
        
        return result
    
    def _load_team_memories(self, team_name: str) -> List[MemoryEntry]:
        """加载团队记忆"""
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
    
    def _apply_memory_filters(self, memories: List[MemoryEntry], 
                             filters: Dict[str, Any]) -> List[MemoryEntry]:
        """应用记忆过滤器"""
        filtered = memories
        
        # 项目过滤
        if 'project' in filters:
            filtered = [m for m in filtered if m.project == filters['project']]
        
        # 标签过滤
        if 'tags' in filters:
            required_tags = filters['tags']
            if isinstance(required_tags, str):
                required_tags = [required_tags]
            filtered = [
                m for m in filtered 
                if any(tag in m.tags for tag in required_tags)
            ]
        
        # 重要性过滤
        if 'min_importance' in filters:
            filtered = [m for m in filtered if m.importance >= filters['min_importance']]
        
        # 时间范围过滤
        if 'date_range' in filters:
            start_date, end_date = filters['date_range']
            filtered = [
                m for m in filtered 
                if start_date <= m.timestamp <= end_date
            ]
        
        return filtered
    
    def _create_team_backup(self, team_name: str) -> Path:
        """创建团队备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{team_name}_backup_{timestamp}.zip"
        
        team_path = self.directory_manager.get_team_path(team_name)
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in team_path.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(team_path)
                    zipf.write(file_path, arcname)
        
        return backup_path
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.zip"):
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """清理旧备份"""
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
        deleted_count = 0
        
        for backup_file in self.backup_dir.glob("*.zip"):
            if backup_file.stat().st_mtime < cutoff_time:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete backup {backup_file}: {e}")
        
        return deleted_count 