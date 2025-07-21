"""
Claude结果存储模块

负责分开存放系统提示词和Claude生成的内容
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class ClaudeStorage:
    """Claude结果存储管理类"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化存储管理器
        
        Args:
            output_dir: 输出目录根路径
        """
        self.output_dir = Path(output_dir)
        self.system_prompts_dir = self.output_dir / "system_prompts"
        self.responses_dir = self.output_dir / "claude_responses"
        self.metadata_dir = self.output_dir / "metadata"
        
        # 创建目录
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所有必要的目录存在"""
        for directory in [self.system_prompts_dir, self.responses_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_system_prompt(self, system_prompt: str, team_name: str, mode: str, 
                          timestamp: str = None) -> Path:
        """
        保存系统提示词
        
        Args:
            system_prompt: 系统提示词内容
            team_name: 团队名称
            mode: 上下文模式
            timestamp: 时间戳
        
        Returns:
            保存的文件路径
        """
        if timestamp is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        filename = f"{timestamp}_{team_name}_{mode}_system_prompt.txt"
        file_path = self.system_prompts_dir / filename
        
        # 写入内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# 系统提示词\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**团队**: {team_name}\n")
            f.write(f"**模式**: {mode}\n")
            f.write(f"**长度**: {len(system_prompt)}字符\n\n")
            f.write("---\n\n")
            f.write(system_prompt)
        
        return file_path
    
    def save_claude_response(self, response_content: str, team_name: str, 
                           user_message: str, metadata: Dict[str, Any],
                           timestamp: str = None) -> Path:
        """
        保存Claude响应内容
        
        Args:
            response_content: Claude响应内容
            team_name: 团队名称
            user_message: 用户消息
            metadata: 元数据信息
            timestamp: 时间戳
        
        Returns:
            保存的文件路径
        """
        if timestamp is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        filename = f"{timestamp}_{team_name}_claude_response.md"
        file_path = self.responses_dir / filename
        
        # 写入内容（只保留Claude生成的内容）
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response_content)
        
        return file_path
    
    def save_metadata(self, metadata: Dict[str, Any], timestamp: str = None) -> Path:
        """
        保存元数据
        
        Args:
            metadata: 元数据字典
            timestamp: 时间戳
        
        Returns:
            保存的文件路径
        """
        if timestamp is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        filename = f"{timestamp}_metadata.json"
        file_path = self.metadata_dir / filename
        
        # 添加时间戳到元数据
        metadata_with_timestamp = {
            "saved_at": datetime.now().isoformat(),
            "timestamp": timestamp,
            **metadata
        }
        
        # 写入JSON文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_with_timestamp, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def save_complete_result(self, result: Dict[str, Any]) -> Dict[str, Path]:
        """
        保存完整的结果（系统提示词、响应内容、元数据分开存放）
        
        Args:
            result: 完整的结果字典
        
        Returns:
            保存的文件路径字典
        """
        if not result.get("success"):
            raise ValueError("无法保存失败的结果")
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        team_name = result.get("team_name", "unknown")
        mode = result.get("mode", "unknown")
        
        saved_paths = {}
        
        # 1. 保存系统提示词
        if "system_prompt" in result:
            system_prompt_path = self.save_system_prompt(
                result["system_prompt"], 
                team_name, 
                mode, 
                timestamp
            )
            saved_paths["system_prompt"] = system_prompt_path
        
        # 2. 保存Claude响应
        if "response_content" in result:
            response_path = self.save_claude_response(
                result["response_content"],
                team_name,
                result.get("user_message", ""),
                result,
                timestamp
            )
            saved_paths["response"] = response_path
        
        # 3. 保存元数据
        metadata = {
            "team_name": team_name,
            "mode": mode,
            "system_prompt_length": result.get("system_prompt_length", 0),
            "user_message_length": result.get("user_message_length", 0),
            "response_length": result.get("response_length", 0),
            "response_time": result.get("response_time", 0),
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
            "total_tokens": result.get("total_tokens", 0),
            "model_name": result.get("model_name", "unknown")
        }
        
        metadata_path = self.save_metadata(metadata, timestamp)
        saved_paths["metadata"] = metadata_path
        
        return saved_paths
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        def count_files(directory: Path) -> int:
            return len(list(directory.glob("*"))) if directory.exists() else 0
        
        return {
            "output_dir": str(self.output_dir),
            "system_prompts_dir": str(self.system_prompts_dir),
            "responses_dir": str(self.responses_dir),
            "metadata_dir": str(self.metadata_dir),
            "system_prompts_count": count_files(self.system_prompts_dir),
            "responses_count": count_files(self.responses_dir),
            "metadata_count": count_files(self.metadata_dir)
        }
    
    def list_recent_files(self, file_type: str = "all", limit: int = 5) -> Dict[str, list]:
        """
        列出最近的文件
        
        Args:
            file_type: 文件类型 ("system_prompts", "responses", "metadata", "all")
            limit: 返回文件数量限制
        
        Returns:
            最近文件列表
        """
        def get_recent_files(directory: Path, pattern: str = "*") -> list:
            if not directory.exists():
                return []
            
            files = list(directory.glob(pattern))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return [str(f.name) for f in files[:limit]]
        
        result = {}
        
        if file_type in ["system_prompts", "all"]:
            result["system_prompts"] = get_recent_files(self.system_prompts_dir)
        
        if file_type in ["responses", "all"]:
            result["responses"] = get_recent_files(self.responses_dir)
        
        if file_type in ["metadata", "all"]:
            result["metadata"] = get_recent_files(self.metadata_dir)
        
        return result


def create_claude_storage(output_dir: str = "output") -> ClaudeStorage:
    """
    便捷函数：创建Claude存储管理器
    
    Args:
        output_dir: 输出目录
    
    Returns:
        ClaudeStorage实例
    """
    return ClaudeStorage(output_dir=output_dir) 