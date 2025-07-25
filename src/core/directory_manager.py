"""
ContextX团队目录结构管理器

负责管理基于team隔离的目录结构，支持：
- 团队目录创建和初始化
- 目录结构验证和修复
- 路径解析和安全检查
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime


class DirectoryManager:
    """团队目录结构管理器"""
    
    # 标准目录结构模板
    TEAM_STRUCTURE = {
        'memory': {
            'declarative.md': '# 团队声明性记忆\n\n',
            'procedural.md': '# 团队程序性记忆\n\n',
            'episodic/': {}
        },
        'context': {
            'requirements.md': '# 需求分析上下文\n\n',
            'business-model.md': '# 业务模型上下文\n\n',
            'solution.md': '# 解决方案上下文\n\n',
            'structure.md': '# 架构设计上下文\n\n',
            'tasks.md': '# 任务编排上下文\n\n',
            'common-tasks.md': '# 通用任务上下文\n\n',
            'constraints.md': '# 约束条件上下文\n\n'
        },
        'projects/': {},
        'config.json': None  # 将动态生成
    }
    
    # 项目目录结构模板
    PROJECT_STRUCTURE = {
        'memory': {
            'declarative.md': '# 项目声明性记忆\n\n',
            'procedural.md': '# 项目程序性记忆\n\n',
            'episodic/': {}
        },
        'context': {
            'requirements.md': '# 项目需求分析上下文\n\n',
            'business-model.md': '# 项目业务模型上下文\n\n',
            'solution.md': '# 项目解决方案上下文\n\n',
            'structure.md': '# 项目架构设计上下文\n\n',
            'tasks.md': '# 项目任务编排上下文\n\n',
            'common-tasks.md': '# 项目通用任务上下文\n\n',
            'constraints.md': '# 项目约束条件上下文\n\n'
        },
        'config.json': None  # 将动态生成
    }
    
    def __init__(self, root_path: Union[str, Path] = None):
        """
        初始化目录管理器
        
        Args:
            root_path: ContextX根目录路径，默认为当前目录下的.ContextX
        """
        if root_path is None:
            root_path = Path.cwd() / '.ContextX'
        
        self.root_path = Path(root_path)
        self.teams_path = self.root_path / 'teams'
        self.global_path = self.root_path / 'global'
        
        # 确保根目录存在
        self._ensure_root_structure()
    
    def _ensure_root_structure(self) -> None:
        """确保根目录结构存在"""
        self.root_path.mkdir(exist_ok=True)
        self.teams_path.mkdir(exist_ok=True)
        self.global_path.mkdir(exist_ok=True)
        
        # 创建全局目录结构
        (self.global_path / 'templates').mkdir(exist_ok=True)
        (self.global_path / 'standards').mkdir(exist_ok=True)
    
    def create_team(self, team_name: str, description: str = "", 
                   members: List[str] = None) -> Path:
        """
        创建新团队目录结构
        
        Args:
            team_name: 团队名称
            description: 团队描述
            members: 团队成员列表
            
        Returns:
            团队目录路径
            
        Raises:
            ValueError: 团队名称无效
            FileExistsError: 团队已存在
        """
        # 验证团队名称
        if not self._validate_team_name(team_name):
            raise ValueError(f"无效的团队名称: {team_name}")
        
        team_path = self.teams_path / team_name
        
        # 检查团队是否已存在
        if team_path.exists():
            raise FileExistsError(f"团队 '{team_name}' 已存在")
        
        # 创建团队目录结构
        self._create_team_structure(team_path)
        
        # 生成团队配置
        config = self._generate_team_config(team_name, description, members or [])
        self._write_team_config(team_path, config)
        
        return team_path
    
    def _validate_team_name(self, team_name: str) -> bool:
        """验证团队名称是否符合规范"""
        if not team_name:
            return False
        
        # 只允许字母、数字、连字符和下划线
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
        return all(c in allowed_chars for c in team_name)
    
    def _create_team_structure(self, team_path: Path) -> None:
        """创建团队目录结构"""
        def create_structure(base_path: Path, structure: Dict):
            for name, content in structure.items():
                path = base_path / name
                
                if name.endswith('/'):
                    # 目录
                    path.mkdir(exist_ok=True)
                    if isinstance(content, dict):
                        create_structure(path, content)
                elif content is None:
                    # 跳过，稍后处理
                    continue
                elif isinstance(content, str):
                    # 文件内容
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if not path.exists():
                        path.write_text(content, encoding='utf-8')
                elif isinstance(content, dict):
                    # 这是一个目录，但名称没有以'/'结尾
                    path.mkdir(parents=True, exist_ok=True)
                    create_structure(path, content)
        
        create_structure(team_path, self.TEAM_STRUCTURE)
    
    def _generate_team_config(self, team_name: str, description: str, 
                            members: List[str]) -> Dict:
        """生成团队配置"""
        return {
            'name': team_name,
            'description': description,
            'members': members,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'version': '1.0.0',
            'settings': {
                'memory_retention_days': 365,
                'auto_context_generation': True,
                'context_stages': [
                    'requirements',
                    'business-model', 
                    'solution',
                    'structure',
                    'tasks',
                    'common-tasks',
                    'constraints'
                ]
            }
        }
    
    def _write_team_config(self, team_path: Path, config: Dict) -> None:
        """写入团队配置文件"""
        config_path = team_path / 'config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def get_team_path(self, team_name: str) -> Path:
        """获取团队目录路径"""
        team_path = self.teams_path / team_name
        if not team_path.exists():
            raise FileNotFoundError(f"团队 '{team_name}' 不存在")
        return team_path
    
    def list_teams(self) -> List[str]:
        """列出所有团队"""
        teams = []
        if self.teams_path.exists():
            for item in self.teams_path.iterdir():
                if item.is_dir() and (item / 'config.json').exists():
                    teams.append(item.name)
        return sorted(teams)
    
    def get_team_config(self, team_name: str) -> Dict:
        """获取团队配置"""
        team_path = self.get_team_path(team_name)
        config_path = team_path / 'config.json'
        
        if not config_path.exists():
            raise FileNotFoundError(f"团队 '{team_name}' 配置文件不存在")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_team_config(self, team_name: str, updates: Dict) -> None:
        """更新团队配置"""
        config = self.get_team_config(team_name)
        config.update(updates)
        config['updated_at'] = datetime.now().isoformat()
        
        team_path = self.get_team_path(team_name)
        self._write_team_config(team_path, config)
    
    def get_memory_path(self, team_name: str, memory_type: str = 'declarative') -> Path:
        """获取团队记忆文件路径"""
        team_path = self.get_team_path(team_name)
        
        if memory_type == 'episodic':
            return team_path / 'memory' / 'episodic'
        else:
            return team_path / 'memory' / f'{memory_type}.md'
    
    def get_context_path(self, team_name: str, stage: str) -> Path:
        """获取团队上下文文件路径"""
        team_path = self.get_team_path(team_name)
        return team_path / 'context' / f'{stage}.md'
    
    def get_project_path(self, team_name: str, project_name: str) -> Path:
        """获取项目上下文路径"""
        team_path = self.get_team_path(team_name)
        project_path = team_path / 'projects' / project_name
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path
    
    def validate_team_structure(self, team_name: str) -> Dict[str, bool]:
        """验证团队目录结构完整性"""
        team_path = self.get_team_path(team_name)
        validation_result = {}
        
        def validate_structure(base_path: Path, structure: Dict, result_path: str = ""):
            for name, content in structure.items():
                current_path = f"{result_path}/{name}" if result_path else name
                path = base_path / name
                
                if name.endswith('/'):
                    # 目录
                    result = path.exists() and path.is_dir()
                    validation_result[current_path] = result
                    
                    if result and isinstance(content, dict):
                        validate_structure(path, content, current_path.rstrip('/'))
                elif content is not None:
                    # 文件
                    validation_result[current_path] = path.exists() and path.is_file()
        
        validate_structure(team_path, self.TEAM_STRUCTURE)
        return validation_result
    
    def repair_team_structure(self, team_name: str) -> List[str]:
        """修复团队目录结构"""
        team_path = self.get_team_path(team_name)
        repaired = []
        
        def repair_structure(base_path: Path, structure: Dict):
            for name, content in structure.items():
                path = base_path / name
                
                if name.endswith('/'):
                    # 目录
                    if not path.exists():
                        path.mkdir(parents=True, exist_ok=True)
                        repaired.append(f"创建目录: {path}")
                    
                    if isinstance(content, dict):
                        repair_structure(path, content)
                elif content is not None:
                    # 文件
                    if not path.exists():
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(content, encoding='utf-8')
                        repaired.append(f"创建文件: {path}")
        
        repair_structure(team_path, self.TEAM_STRUCTURE)
        return repaired
    
    def get_team_path(self, team_name: str) -> Path:
        """获取团队路径"""
        return self.teams_path / team_name
    
    def team_exists(self, team_name: str) -> bool:
        """检查团队是否存在"""
        team_path = self.get_team_path(team_name)
        return team_path.exists() and team_path.is_dir()
    
    # === 项目级别管理方法 ===
    
    def create_project(self, team_name: str, project_name: str, description: str = "") -> Path:
        """
        在指定团队下创建新项目目录结构
        
        Args:
            team_name: 团队名称
            project_name: 项目名称
            description: 项目描述
            
        Returns:
            项目目录路径
            
        Raises:
            ValueError: 团队或项目名称无效
            FileNotFoundError: 团队不存在
            FileExistsError: 项目已存在
        """
        # 验证团队存在
        if not self.team_exists(team_name):
            raise FileNotFoundError(f"团队 '{team_name}' 不存在")
        
        # 验证项目名称
        if not self._validate_team_name(project_name):  # 复用团队名称验证逻辑
            raise ValueError(f"无效的项目名称: {project_name}")
        
        project_path = self.get_project_path(team_name, project_name)
        
        # 检查项目是否已存在
        if project_path.exists():
            raise FileExistsError(f"项目 '{project_name}' 在团队 '{team_name}' 中已存在")
        
        # 创建项目目录结构
        self._create_project_structure(project_path)
        
        # 生成项目配置
        config = self._generate_project_config(project_name, description)
        self._write_project_config(project_path, config)
        
        return project_path
    
    def get_project_path(self, team_name: str, project_name: str) -> Path:
        """获取项目目录路径"""
        return self.get_team_path(team_name) / "projects" / project_name
    
    def project_exists(self, team_name: str, project_name: str) -> bool:
        """检查项目是否存在"""
        return self.get_project_path(team_name, project_name).exists()
    
    def list_projects(self, team_name: str) -> List[str]:
        """列出团队下的所有项目"""
        if not self.team_exists(team_name):
            return []
        
        projects_dir = self.get_team_path(team_name) / "projects"
        if not projects_dir.exists():
            return []
        
        return [p.name for p in projects_dir.iterdir() if p.is_dir()]
    
    def _create_project_structure(self, project_path: Path) -> None:
        """创建项目目录结构"""
        def create_structure(base_path: Path, structure: Dict):
            for name, content in structure.items():
                path = base_path / name
                
                if name.endswith('/'):
                    # 目录
                    path.mkdir(exist_ok=True)
                    if isinstance(content, dict):
                        create_structure(path, content)
                elif isinstance(content, dict):
                    # 嵌套字典表示子目录结构
                    path.mkdir(exist_ok=True)
                    create_structure(path, content)
                else:
                    # 文件
                    if content is not None:
                        path.write_text(content, encoding='utf-8')
                    elif name == 'config.json':
                        # config.json需要特殊处理，跳过这里，在后面单独创建
                        pass
        
        # 创建项目根目录
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 创建项目结构
        create_structure(project_path, self.PROJECT_STRUCTURE)
    
    def _generate_project_config(self, project_name: str, description: str) -> Dict:
        """生成项目配置"""
        return {
            'name': project_name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'version': '1.0.0',
            'type': 'project',
            'memory_config': {
                'max_entries_per_type': 100,
                'auto_cleanup_days': 90,
                'importance_threshold': 1
            }
        }
    
    def _write_project_config(self, project_path: Path, config: Dict) -> None:
        """写入项目配置文件"""
        config_path = project_path / 'config.json'
        config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def repair_project_structure(self, team_name: str, project_name: str) -> List[str]:
        """修复项目目录结构"""
        project_path = self.get_project_path(team_name, project_name)
        repaired = []
        
        def repair_structure(base_path: Path, structure: Dict):
            for name, content in structure.items():
                path = base_path / name
                
                if name.endswith('/'):
                    # 目录
                    if not path.exists():
                        path.mkdir(parents=True, exist_ok=True)
                        repaired.append(f"创建目录: {path}")
                    
                    if isinstance(content, dict):
                        repair_structure(path, content)
                elif isinstance(content, dict):
                    # 嵌套字典表示子目录结构
                    if not path.exists():
                        path.mkdir(parents=True, exist_ok=True)
                        repaired.append(f"创建目录: {path}")
                    repair_structure(path, content)
                else:
                    # 文件
                    if not path.exists() and content is not None:
                        path.write_text(content, encoding='utf-8')
                        repaired.append(f"创建文件: {path}")
                    elif name == 'config.json' and not path.exists():
                        # config.json需要特殊处理，跳过这里
                        pass
        
        repair_structure(project_path, self.PROJECT_STRUCTURE)
        return repaired 