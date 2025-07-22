"""
AI模型结果存储管理模块

负责分开存放系统提示词和AI模型生成的内容
支持Claude、OpenAI等多种AI模型的结果存储
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class ModelStorageManager:
    """AI模型结果存储管理类"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化存储管理器
        
        Args:
            output_dir: 输出目录根路径
        """
        self.output_dir = Path(output_dir)
        self.system_prompts_dir = self.output_dir / "system_prompts"
        self.responses_dir = self.output_dir / "ai_responses"  # 更通用的命名
        self.metadata_dir = self.output_dir / "metadata"
        
        # 创建目录
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所有必要的目录存在"""
        for directory in [self.system_prompts_dir, self.responses_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        return {
            "output_dir": str(self.output_dir),
            "system_prompts_dir": str(self.system_prompts_dir),
            "responses_dir": str(self.responses_dir),
            "metadata_dir": str(self.metadata_dir),
            "system_prompts_count": len(list(self.system_prompts_dir.glob("*.txt"))),
            "responses_count": len(list(self.responses_dir.glob("*.md"))),
            "metadata_count": len(list(self.metadata_dir.glob("*.json")))
        }
    
    def save_system_prompt(self, system_prompt: str, team_name: str, 
                          mode: str, timestamp: str = None) -> Path:
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
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(system_prompt)
        
        return file_path
    
    def save_ai_response(self, response_content: str, team_name: str, 
                        user_message: str, metadata: Dict[str, Any],
                        timestamp: str = None) -> Path:
        """
        保存AI模型响应内容
        
        Args:
            response_content: AI响应内容
            team_name: 团队名称
            user_message: 用户消息
            metadata: 元数据信息
            timestamp: 时间戳
        
        Returns:
            保存的文件路径
        """
        if timestamp is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        filename = f"{timestamp}_{team_name}_ai_response.md"
        file_path = self.responses_dir / filename
        
        # 写入内容（只保留AI生成的内容）
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
    
    def save_complete_result(self, result: Dict[str, Any], timestamp: str = None) -> Dict[str, Path]:
        """
        保存完整的对话结果（系统提示词 + 响应 + 元数据）
        
        Args:
            result: 包含完整对话信息的结果字典
            timestamp: 可选的时间戳
        
        Returns:
            保存的文件路径字典
        """
        if timestamp is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        saved_paths = {}
        
        # 1. 保存系统提示词
        if "system_prompt" in result and result["system_prompt"]:
            system_prompt_path = self.save_system_prompt(
                system_prompt=result["system_prompt"],
                team_name=result.get("team_name", "unknown"),
                mode=result.get("mode", "unknown"),
                timestamp=timestamp
            )
            saved_paths["system_prompt"] = system_prompt_path
        
        # 2. 保存AI响应
        if "response" in result and result["response"]:
            response_path = self.save_ai_response(
                response_content=result["response"],
                team_name=result.get("team_name", "unknown"),
                user_message=result.get("user_message", ""),
                metadata=result,
                timestamp=timestamp
            )
            saved_paths["response"] = response_path
        
        # 3. 保存元数据
        metadata = {
            "team_name": result.get("team_name", "unknown"),
            "mode": result.get("mode", "unknown"),
            "user_message_length": result.get("user_message_length", 0),
            "system_prompt_length": result.get("system_prompt_length", 0),
            "response_length": result.get("response_length", 0),
            "response_time": result.get("response_time", 0),
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
            "total_tokens": result.get("total_tokens", 0),
            "success": result.get("success", False)
        }
        
        metadata_path = self.save_metadata(metadata, timestamp)
        saved_paths["metadata"] = metadata_path
        
        return saved_paths
    
    def list_stored_results(self, limit: int = 10) -> Dict[str, Any]:
        """
        列出最近存储的结果
        
        Args:
            limit: 返回结果数量限制
        
        Returns:
            存储结果列表
        """
        # 获取所有元数据文件（按时间排序）
        metadata_files = sorted(
            self.metadata_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]
        
        results = []
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    
                # 查找对应的文件
                timestamp = metadata.get("timestamp", "")
                team_name = metadata.get("team_name", "unknown")
                mode = metadata.get("mode", "unknown")
                
                # 构建文件路径
                system_prompt_file = self.system_prompts_dir / f"{timestamp}_{team_name}_{mode}_system_prompt.txt"
                response_file = self.responses_dir / f"{timestamp}_{team_name}_ai_response.md"
                
                result_info = {
                    "timestamp": timestamp,
                    "saved_at": metadata.get("saved_at"),
                    "team_name": team_name,
                    "mode": mode,
                    "metadata_file": str(metadata_file),
                    "system_prompt_file": str(system_prompt_file) if system_prompt_file.exists() else None,
                    "response_file": str(response_file) if response_file.exists() else None,
                    "metadata": metadata
                }
                
                results.append(result_info)
                
            except Exception as e:
                print(f"读取元数据文件 {metadata_file} 时出错: {e}")
                continue
        
        return {
            "total_found": len(results),
            "limit": limit,
            "results": results
        }


def create_model_storage_manager(output_dir: str = "output") -> ModelStorageManager:
    """
    便捷函数：创建AI模型存储管理器
    
    Args:
        output_dir: 输出目录
    
    Returns:
        ModelStorageManager实例
    """
    return ModelStorageManager(output_dir=output_dir)


# 向后兼容的别名
def create_claude_storage(output_dir: str = "output") -> ModelStorageManager:
    """向后兼容：创建Claude存储管理器"""
    return create_model_storage_manager(output_dir=output_dir)


# 保持向后兼容的类别名
ClaudeStorage = ModelStorageManager 