"""
PromptX团队协作管理器

提供团队间协作和知识共享功能，包括：
- 团队间知识共享和访问控制
- 协作项目管理
- 跨团队记忆同步
- 协作工作流和审批机制
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .directory_manager import DirectoryManager
from .markdown_engine import MarkdownEngine, MemoryEntry
from .advanced_search import AdvancedSearchEngine


class AccessLevel(Enum):
    """访问权限级别"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class ShareType(Enum):
    """共享类型"""
    MEMORY = "memory"
    CONTEXT = "context"
    TEMPLATE = "template"
    PROJECT = "project"


@dataclass
class SharePermission:
    """共享权限"""
    id: str
    source_team: str
    target_team: str
    share_type: ShareType
    resource_id: str
    access_level: AccessLevel
    created_by: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'source_team': self.source_team,
            'target_team': self.target_team,
            'share_type': self.share_type.value,
            'resource_id': self.resource_id,
            'access_level': self.access_level.value,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharePermission':
        """从字典创建共享权限"""
        return cls(
            id=data['id'],
            source_team=data['source_team'],
            target_team=data['target_team'],
            share_type=ShareType(data['share_type']),
            resource_id=data['resource_id'],
            access_level=AccessLevel(data['access_level']),
            created_by=data['created_by'],
            created_at=data.get('created_at', datetime.now().isoformat()),
            expires_at=data.get('expires_at'),
            description=data.get('description', '')
        )
    
    def is_expired(self) -> bool:
        """检查权限是否过期"""
        if not self.expires_at:
            return False
        
        try:
            expiry_time = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.now() > expiry_time
        except:
            return False


@dataclass
class CollaborationProject:
    """协作项目"""
    id: str
    name: str
    description: str
    teams: List[str]
    owner_team: str
    created_by: str
    status: str = "active"  # active, paused, completed, archived
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    shared_resources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'teams': self.teams,
            'owner_team': self.owner_team,
            'created_by': self.created_by,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'shared_resources': self.shared_resources,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationProject':
        """从字典创建协作项目"""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            teams=data['teams'],
            owner_team=data['owner_team'],
            created_by=data['created_by'],
            status=data.get('status', 'active'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            shared_resources=data.get('shared_resources', []),
            metadata=data.get('metadata', {})
        )


class CollaborationManager:
    """团队协作管理器"""
    
    def __init__(self, base_path: Path):
        """
        初始化协作管理器
        
        Args:
            base_path: 基础路径
        """
        self.base_path = Path(base_path)
        self.directory_manager = DirectoryManager(base_path)
        self.markdown_engine = MarkdownEngine()
        self.search_engine = AdvancedSearchEngine(base_path)
        
        # 协作数据目录
        self.collaboration_dir = self.base_path / "collaboration"
        self.collaboration_dir.mkdir(exist_ok=True)
        
        # 权限和项目存储
        self.permissions_file = self.collaboration_dir / "permissions.json"
        self.projects_file = self.collaboration_dir / "projects.json"
        
        # 缓存
        self._permissions_cache: Dict[str, SharePermission] = {}
        self._projects_cache: Dict[str, CollaborationProject] = {}
        
        # 加载数据
        self._load_permissions()
        self._load_projects()
    
    def create_share_permission(self, source_team: str, target_team: str, 
                              share_type: ShareType, resource_id: str,
                              access_level: AccessLevel, created_by: str,
                              description: str = "", expires_in_days: Optional[int] = None) -> str:
        """
        创建共享权限
        
        Args:
            source_team: 源团队
            target_team: 目标团队
            share_type: 共享类型
            resource_id: 资源ID
            access_level: 访问级别
            created_by: 创建者
            description: 描述
            expires_in_days: 过期天数
            
        Returns:
            权限ID
        """
        # 验证团队存在
        if not self.directory_manager.team_exists(source_team):
            raise ValueError(f"Source team '{source_team}' does not exist")
        
        if not self.directory_manager.team_exists(target_team):
            raise ValueError(f"Target team '{target_team}' does not exist")
        
        # 计算过期时间
        expires_at = None
        if expires_in_days:
            expiry_time = datetime.now() + timedelta(days=expires_in_days)
            expires_at = expiry_time.isoformat()
        
        # 创建权限
        permission = SharePermission(
            id=str(uuid.uuid4()),
            source_team=source_team,
            target_team=target_team,
            share_type=share_type,
            resource_id=resource_id,
            access_level=access_level,
            created_by=created_by,
            expires_at=expires_at,
            description=description
        )
        
        # 保存权限
        self._permissions_cache[permission.id] = permission
        self._save_permissions()
        
        return permission.id
    
    def check_access_permission(self, team: str, resource_team: str, 
                              share_type: ShareType, resource_id: str,
                              required_level: AccessLevel = AccessLevel.READ) -> bool:
        """
        检查访问权限
        
        Args:
            team: 请求团队
            resource_team: 资源所属团队
            share_type: 共享类型
            resource_id: 资源ID
            required_level: 所需权限级别
            
        Returns:
            是否有权限
        """
        # 如果是同一团队，直接允许
        if team == resource_team:
            return True
        
        # 检查共享权限
        for permission in self._permissions_cache.values():
            if (permission.target_team == team and 
                permission.source_team == resource_team and
                permission.share_type == share_type and
                permission.resource_id == resource_id and
                not permission.is_expired()):
                
                # 检查权限级别
                return self._check_access_level(permission.access_level, required_level)
        
        return False
    
    def get_shared_resources(self, team: str, share_type: Optional[ShareType] = None) -> List[Dict[str, Any]]:
        """
        获取团队可访问的共享资源
        
        Args:
            team: 团队名称
            share_type: 共享类型过滤器
            
        Returns:
            共享资源列表
        """
        shared_resources = []
        
        for permission in self._permissions_cache.values():
            if permission.target_team == team and not permission.is_expired():
                if share_type is None or permission.share_type == share_type:
                    resource_info = {
                        'permission_id': permission.id,
                        'source_team': permission.source_team,
                        'share_type': permission.share_type.value,
                        'resource_id': permission.resource_id,
                        'access_level': permission.access_level.value,
                        'description': permission.description,
                        'created_at': permission.created_at,
                        'expires_at': permission.expires_at
                    }
                    
                    # 尝试加载资源详细信息
                    try:
                        resource_details = self._load_resource_details(permission)
                        resource_info.update(resource_details)
                    except:
                        pass  # 忽略加载失败的资源
                    
                    shared_resources.append(resource_info)
        
        return shared_resources
    
    def create_collaboration_project(self, name: str, description: str, 
                                   owner_team: str, teams: List[str],
                                   created_by: str) -> str:
        """
        创建协作项目
        
        Args:
            name: 项目名称
            description: 项目描述
            owner_team: 所有者团队
            teams: 参与团队列表
            created_by: 创建者
            
        Returns:
            项目ID
        """
        # 验证所有团队存在
        for team in [owner_team] + teams:
            if not self.directory_manager.team_exists(team):
                raise ValueError(f"Team '{team}' does not exist")
        
        # 创建项目
        project = CollaborationProject(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            teams=list(set([owner_team] + teams)),  # 去重并包含所有者团队
            owner_team=owner_team,
            created_by=created_by
        )
        
        # 保存项目
        self._projects_cache[project.id] = project
        self._save_projects()
        
        return project.id
    
    def add_team_to_project(self, project_id: str, team: str, added_by: str) -> bool:
        """
        向项目添加团队
        
        Args:
            project_id: 项目ID
            team: 团队名称
            added_by: 添加者
            
        Returns:
            是否成功
        """
        if project_id not in self._projects_cache:
            return False
        
        if not self.directory_manager.team_exists(team):
            return False
        
        project = self._projects_cache[project_id]
        if team not in project.teams:
            project.teams.append(team)
            project.updated_at = datetime.now().isoformat()
            project.metadata['last_modified_by'] = added_by
            
            self._save_projects()
        
        return True
    
    def share_memory_to_project(self, project_id: str, source_team: str, 
                              memory_id: str, shared_by: str) -> bool:
        """
        向项目共享记忆
        
        Args:
            project_id: 项目ID
            source_team: 源团队
            memory_id: 记忆ID
            shared_by: 共享者
            
        Returns:
            是否成功
        """
        if project_id not in self._projects_cache:
            return False
        
        project = self._projects_cache[project_id]
        
        # 检查源团队是否在项目中
        if source_team not in project.teams:
            return False
        
        # 为项目中的其他团队创建共享权限
        for team in project.teams:
            if team != source_team:
                try:
                    self.create_share_permission(
                        source_team=source_team,
                        target_team=team,
                        share_type=ShareType.MEMORY,
                        resource_id=memory_id,
                        access_level=AccessLevel.READ,
                        created_by=shared_by,
                        description=f"Shared through project: {project.name}"
                    )
                except:
                    pass  # 忽略已存在的权限
        
        # 记录共享资源
        resource_key = f"{source_team}:{ShareType.MEMORY.value}:{memory_id}"
        if resource_key not in project.shared_resources:
            project.shared_resources.append(resource_key)
            project.updated_at = datetime.now().isoformat()
            self._save_projects()
        
        return True
    
    def sync_memories_across_teams(self, source_team: str, target_team: str,
                                 memory_filter: Optional[Dict[str, Any]] = None) -> int:
        """
        跨团队同步记忆
        
        Args:
            source_team: 源团队
            target_team: 目标团队
            memory_filter: 记忆过滤器
            
        Returns:
            同步的记忆数量
        """
        if not self.directory_manager.team_exists(source_team):
            raise ValueError(f"Source team '{source_team}' does not exist")
        
        if not self.directory_manager.team_exists(target_team):
            raise ValueError(f"Target team '{target_team}' does not exist")
        
        # 加载源团队记忆
        source_memories = self._load_team_memories(source_team)
        
        # 应用过滤器
        if memory_filter:
            source_memories = self._apply_memory_filter(source_memories, memory_filter)
        
        # 同步到目标团队
        synced_count = 0
        target_team_path = self.directory_manager.get_team_path(target_team)
        
        for memory in source_memories:
            try:
                # 检查是否有共享权限
                if self.check_access_permission(
                    target_team, source_team, ShareType.MEMORY, 
                    memory.id, AccessLevel.READ
                ):
                    # 创建同步记忆（添加来源标记）
                    synced_memory = MemoryEntry(
                        id=f"sync_{memory.id}",
                        timestamp=datetime.now().isoformat(),
                        content=f"[Synced from {source_team}]\n\n{memory.content}",
                        tags=memory.tags + ['synced', f'from_{source_team}'],
                        project=memory.project,
                        importance=memory.importance,
                        metadata={
                            **memory.metadata,
                            'synced_from_team': source_team,
                            'original_id': memory.id,
                            'sync_time': datetime.now().isoformat()
                        }
                    )
                    
                    # 保存到目标团队
                    sync_file = target_team_path / "memory" / "synced.md"
                    self.markdown_engine.append_memory(sync_file, synced_memory)
                    synced_count += 1
                    
            except Exception as e:
                print(f"Failed to sync memory {memory.id}: {e}")
        
        return synced_count
    
    def get_collaboration_analytics(self, team: Optional[str] = None) -> Dict[str, Any]:
        """
        获取协作分析数据
        
        Args:
            team: 团队名称（可选，用于筛选）
            
        Returns:
            分析数据
        """
        analytics = {
            'total_permissions': len(self._permissions_cache),
            'active_permissions': 0,
            'expired_permissions': 0,
            'total_projects': len(self._projects_cache),
            'active_projects': 0,
            'team_collaboration_matrix': {},
            'most_shared_resources': {},
            'collaboration_trends': []
        }
        
        # 分析权限状态
        for permission in self._permissions_cache.values():
            if team and permission.source_team != team and permission.target_team != team:
                continue
                
            if permission.is_expired():
                analytics['expired_permissions'] += 1
            else:
                analytics['active_permissions'] += 1
        
        # 分析项目状态
        for project in self._projects_cache.values():
            if team and team not in project.teams:
                continue
                
            if project.status == 'active':
                analytics['active_projects'] += 1
        
        # 构建协作矩阵
        collaboration_matrix = {}
        for permission in self._permissions_cache.values():
            if not permission.is_expired():
                source = permission.source_team
                target = permission.target_team
                
                if source not in collaboration_matrix:
                    collaboration_matrix[source] = {}
                
                if target not in collaboration_matrix[source]:
                    collaboration_matrix[source][target] = 0
                
                collaboration_matrix[source][target] += 1
        
        analytics['team_collaboration_matrix'] = collaboration_matrix
        
        # 分析最多共享的资源类型
        resource_types = {}
        for permission in self._permissions_cache.values():
            if not permission.is_expired():
                resource_type = permission.share_type.value
                resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
        
        analytics['most_shared_resources'] = resource_types
        
        return analytics
    
    def _check_access_level(self, granted_level: AccessLevel, required_level: AccessLevel) -> bool:
        """检查权限级别是否满足要求"""
        level_hierarchy = {
            AccessLevel.NONE: 0,
            AccessLevel.READ: 1,
            AccessLevel.WRITE: 2,
            AccessLevel.ADMIN: 3
        }
        
        return level_hierarchy[granted_level] >= level_hierarchy[required_level]
    
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
    
    def _apply_memory_filter(self, memories: List[MemoryEntry], 
                           memory_filter: Dict[str, Any]) -> List[MemoryEntry]:
        """应用记忆过滤器"""
        filtered = memories
        
        # 标签过滤
        if 'tags' in memory_filter:
            required_tags = memory_filter['tags']
            if isinstance(required_tags, str):
                required_tags = [required_tags]
            filtered = [
                m for m in filtered 
                if any(tag in m.tags for tag in required_tags)
            ]
        
        # 项目过滤
        if 'project' in memory_filter:
            filtered = [
                m for m in filtered 
                if m.project == memory_filter['project']
            ]
        
        # 重要性过滤
        if 'min_importance' in memory_filter:
            filtered = [
                m for m in filtered 
                if m.importance >= memory_filter['min_importance']
            ]
        
        # 时间范围过滤
        if 'date_range' in memory_filter:
            start_date, end_date = memory_filter['date_range']
            filtered = [
                m for m in filtered 
                if start_date <= m.timestamp <= end_date
            ]
        
        return filtered
    
    def _load_resource_details(self, permission: SharePermission) -> Dict[str, Any]:
        """加载资源详细信息"""
        details = {}
        
        if permission.share_type == ShareType.MEMORY:
            # 加载记忆详情
            memories = self._load_team_memories(permission.source_team)
            for memory in memories:
                if memory.id == permission.resource_id:
                    details.update({
                        'content_preview': memory.content[:200] + "..." if len(memory.content) > 200 else memory.content,
                        'tags': memory.tags,
                        'importance': memory.importance,
                        'project': memory.project
                    })
                    break
        
        return details
    
    def _load_permissions(self):
        """加载权限数据"""
        if self.permissions_file.exists():
            try:
                data = json.loads(self.permissions_file.read_text(encoding='utf-8'))
                for perm_data in data:
                    permission = SharePermission.from_dict(perm_data)
                    self._permissions_cache[permission.id] = permission
            except Exception as e:
                print(f"Error loading permissions: {e}")
    
    def _save_permissions(self):
        """保存权限数据"""
        try:
            data = [perm.to_dict() for perm in self._permissions_cache.values()]
            self.permissions_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            print(f"Error saving permissions: {e}")
    
    def _load_projects(self):
        """加载项目数据"""
        if self.projects_file.exists():
            try:
                data = json.loads(self.projects_file.read_text(encoding='utf-8'))
                for proj_data in data:
                    project = CollaborationProject.from_dict(proj_data)
                    self._projects_cache[project.id] = project
            except Exception as e:
                print(f"Error loading projects: {e}")
    
    def _save_projects(self):
        """保存项目数据"""
        try:
            data = [proj.to_dict() for proj in self._projects_cache.values()]
            self.projects_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            print(f"Error saving projects: {e}")
    
    def revoke_permission(self, permission_id: str) -> bool:
        """撤销权限"""
        if permission_id in self._permissions_cache:
            del self._permissions_cache[permission_id]
            self._save_permissions()
            return True
        return False
    
    def list_team_permissions(self, team: str, as_source: bool = True) -> List[SharePermission]:
        """列出团队的权限"""
        permissions = []
        for permission in self._permissions_cache.values():
            if as_source and permission.source_team == team:
                permissions.append(permission)
            elif not as_source and permission.target_team == team:
                permissions.append(permission)
        return permissions
    
    def get_project_details(self, project_id: str) -> Optional[CollaborationProject]:
        """获取项目详情"""
        return self._projects_cache.get(project_id) 