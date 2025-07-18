"""
ContextX团队命令基础框架

定义所有团队命令的基础接口和通用功能，支持：
- 统一的命令接口
- 参数验证和解析
- 错误处理和日志记录
- 输出格式化
"""

import abc
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass

from ..core.directory_manager import DirectoryManager
from ..core.markdown_engine import MarkdownEngine


@dataclass
class CommandResult:
    """命令执行结果"""
    success: bool
    message: str
    data: Any = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'success': self.success,
            'message': self.message
        }
        
        if self.data is not None:
            result['data'] = self.data
            
        if self.error:
            result['error'] = self.error
            
        return result


class BaseCommand(abc.ABC):
    """基础命令抽象类"""
    
    def __init__(self, root_path: Union[str, Path] = None):
        """
        初始化基础命令
        
        Args:
            root_path: ContextX根目录路径
        """
        self.directory_manager = DirectoryManager(root_path)
        self.markdown_engine = MarkdownEngine()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 设置日志格式
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @abc.abstractmethod
    def execute(self, *args, **kwargs) -> CommandResult:
        """
        执行命令的抽象方法
        
        子类必须实现此方法来定义具体的命令逻辑
        
        Returns:
            CommandResult: 命令执行结果
        """
        pass
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """命令名称"""
        pass
    
    @property
    @abc.abstractmethod
    def description(self) -> str:
        """命令描述"""
        pass
    
    def validate_team_exists(self, team_name: str) -> bool:
        """
        验证团队是否存在
        
        Args:
            team_name: 团队名称
            
        Returns:
            bool: 团队是否存在
        """
        return self.directory_manager.team_exists(team_name)
    
    def get_team_path(self, team_name: str) -> Path:
        """
        获取团队路径
        
        Args:
            team_name: 团队名称
            
        Returns:
            Path: 团队路径
        """
        return self.directory_manager.get_team_path(team_name)
    
    def get_team_config(self, team_name: str) -> Dict[str, Any]:
        """
        获取团队配置
        
        Args:
            team_name: 团队名称
            
        Returns:
            Dict: 团队配置
            
        Raises:
            FileNotFoundError: 团队不存在
        """
        return self.directory_manager.get_team_config(team_name)
    
    def validate_stage(self, stage: str) -> bool:
        """
        验证上下文阶段是否有效
        
        Args:
            stage: 阶段名称
            
        Returns:
            bool: 阶段是否有效
        """
        valid_stages = {
            'requirements', 'business-model', 'solution', 
            'structure', 'tasks', 'common-tasks', 'constraints',
            'full'  # 特殊阶段，表示生成所有阶段
        }
        return stage in valid_stages
    
    def handle_error(self, error: Exception, context: str = "") -> CommandResult:
        """
        统一错误处理
        
        Args:
            error: 异常对象
            context: 错误上下文
            
        Returns:
            CommandResult: 错误结果
        """
        error_message = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(error_message, exc_info=True)
        
        return CommandResult(
            success=False,
            message=f"命令执行失败: {error_message}",
            error=error_message
        )
    
    def format_success_message(self, action: str, details: str = "") -> str:
        """
        格式化成功消息
        
        Args:
            action: 执行的动作
            details: 详细信息
            
        Returns:
            str: 格式化的消息
        """
        message = f"✅ {action}成功"
        if details:
            message += f": {details}"
        return message
    
    def format_list_output(self, items: List[Any], title: str = "列表") -> str:
        """
        格式化列表输出
        
        Args:
            items: 列表项
            title: 列表标题
            
        Returns:
            str: 格式化的列表
        """
        if not items:
            return f"📋 {title}: 暂无数据"
        
        output_lines = [f"📋 {title} ({len(items)}项):"]
        for i, item in enumerate(items, 1):
            output_lines.append(f"  {i}. {item}")
        
        return "\n".join(output_lines)
    
    def parse_tags(self, tags_str: str) -> List[str]:
        """
        解析标签字符串
        
        Args:
            tags_str: 标签字符串，支持逗号、空格分隔
            
        Returns:
            List[str]: 标签列表
        """
        if not tags_str:
            return []
        
        # 支持多种分隔符
        import re
        tags = re.split(r'[,\s]+', tags_str.strip())
        
        # 清理和去重
        return list(set(tag.strip().lstrip('#') for tag in tags if tag.strip()))
    
    def format_memory_entries(self, entries: List[Any]) -> str:
        """
        格式化记忆条目输出
        
        Args:
            entries: 记忆条目列表
            
        Returns:
            str: 格式化的输出
        """
        if not entries:
            return "🧠 暂无记忆条目"
        
        output_lines = [f"🧠 找到 {len(entries)} 条记忆:"]
        
        for i, entry in enumerate(entries, 1):
            tags_str = ' '.join(f'#{tag}' for tag in entry.tags) if entry.tags else ''
            importance_str = '⭐' * entry.importance
            
            output_lines.extend([
                f"\n📝 {i}. **记忆 #{entry.id}** ({entry.timestamp})",
                f"   内容: {entry.content}",
                f"   项目: {entry.project} | 重要性: {importance_str}",
                f"   标签: {tags_str}" if tags_str else ""
            ])
        
        return "\n".join(line for line in output_lines if line)
    
    def get_help_text(self) -> str:
        """
        获取命令帮助文本
        
        Returns:
            str: 帮助文本
        """
        return f"""
🔧 命令: {self.name}
📋 描述: {self.description}

使用 '{self.name} --help' 获取详细帮助信息
        """.strip()


class TeamCommandMixin:
    """团队命令混入类，提供团队相关的通用功能"""
    
    def ensure_team_exists(self, team_name: str) -> CommandResult:
        """
        确保团队存在，如不存在则提供创建建议
        
        Args:
            team_name: 团队名称
            
        Returns:
            CommandResult: 验证结果
        """
        if not self.validate_team_exists(team_name):
            available_teams = self.directory_manager.list_teams()
            
            if available_teams:
                teams_list = ', '.join(available_teams)
                message = f"❌ 团队 '{team_name}' 不存在\n\n📋 可用团队: {teams_list}\n\n💡 创建新团队: team_create {team_name}"
            else:
                message = f"❌ 团队 '{team_name}' 不存在，且系统中暂无任何团队\n\n💡 创建第一个团队: team_create {team_name}"
            
            return CommandResult(
                success=False,
                message=message
            )
        
        return CommandResult(success=True, message="团队验证成功")
    
    def get_team_summary(self, team_name: str) -> str:
        """
        获取团队摘要信息
        
        Args:
            team_name: 团队名称
            
        Returns:
            str: 团队摘要
        """
        try:
            config = self.get_team_config(team_name)
            members_count = len(config.get('members', []))
            created_at = config.get('created_at', '未知')[:10]  # 只显示日期部分
            
            return f"👥 {team_name} | 成员: {members_count}人 | 创建: {created_at}"
        except Exception:
            return f"👥 {team_name} | 配置异常" 