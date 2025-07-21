"""
Claude模型使用模块

负责团队上下文生成、Claude API调用和结果处理
"""

import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.commands.team_context_command import TeamContextCommand
from .claude_model import create_claude_model


class ClaudeUsage:
    """Claude使用管理类"""
    
    def __init__(self, model_name="claude-sonnet-4-20250514", team_data_root="test_data"):
        """
        初始化Claude使用管理器
        
        Args:
            model_name: Claude模型名称
            team_data_root: 团队数据根目录
        """
        self.claude_model = create_claude_model(model_name)
        self.team_data_root = team_data_root
        self.context_command = TeamContextCommand(root_path=team_data_root)
    
    def get_available_teams(self) -> list:
        """获取可用的团队列表"""
        teams_path = Path(self.team_data_root) / "teams"
        if not teams_path.exists():
            return []
        
        return [d.name for d in teams_path.iterdir() if d.is_dir()]
    
    def generate_team_context(self, team_name: str, mode: str = "framework_only", 
                            max_memory_items: int = 10) -> Dict[str, Any]:
        """
        生成团队上下文
        
        Args:
            team_name: 团队名称
            mode: 生成模式 (framework_only, memory_only, hybrid)
            max_memory_items: 最大记忆项数
        
        Returns:
            上下文生成结果
        """
        try:
            result = self.context_command.execute(
                team_name=team_name,
                action="generate",
                mode=mode,
                output_format="json",
                save_results=False,
                max_memory_items=max_memory_items
            )
            
            if result.success and hasattr(result, 'data') and result.data:
                content = result.data.get('content', '')
                return {
                    "success": True,
                    "content": content,
                    "content_length": len(content),
                    "team_name": team_name,
                    "mode": mode,
                    "metadata": result.data
                }
            else:
                return {
                    "success": False,
                    "error": result.message if hasattr(result, 'message') else '生成失败',
                    "team_name": team_name,
                    "mode": mode
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "team_name": team_name,
                "mode": mode
            }
    
    def test_team_context_generation(self) -> Dict[str, Any]:
        """
        测试团队上下文生成功能
        
        Returns:
            测试结果
        """
        teams = self.get_available_teams()
        if not teams:
            return {
                "success": False,
                "error": "未找到任何团队",
                "teams_found": 0
            }
        
        test_team = teams[0]
        results = {}
        modes = ["framework_only", "memory_only", "hybrid"]
        
        print(f"📁 发现团队: {', '.join(teams[:5])}")
        print(f"🔄 为团队 '{test_team}' 生成上下文...")
        
        for mode in modes:
            print(f"\n   测试模式: {mode}")
            result = self.generate_team_context(test_team, mode, max_memory_items=5)
            
            if result["success"]:
                print(f"   ✅ {mode}: {result['content_length']}字符")
                if result['content']:
                    print(f"   预览: {result['content'][:100]}...")
            else:
                print(f"   ❌ {mode}: {result['error']}")
            
            results[mode] = result
        
        return {
            "success": True,
            "test_team": test_team,
            "teams_found": len(teams),
            "results": results
        }
    
    def chat_with_context(self, user_message: str, team_name: str, 
                         mode: str = "framework_only", max_tokens: int = 20000,
                         temperature: float = 0.7) -> Dict[str, Any]:
        """
        使用团队上下文与Claude对话
        
        Args:
            user_message: 用户消息
            team_name: 团队名称
            mode: 上下文模式
            max_tokens: 最大令牌数
            temperature: 温度参数
        
        Returns:
            对话结果
        """
        # 1. 生成团队上下文
        context_result = self.generate_team_context(team_name, mode)
        
        if not context_result["success"]:
            return {
                "success": False,
                "error": f"上下文生成失败: {context_result['error']}",
                "team_name": team_name,
                "mode": mode
            }
        
        system_prompt = context_result["content"]
        if not system_prompt:
            system_prompt = f"你是一个为{team_name}团队工作的AI助手。请提供有用、准确的响应。"
        
        # 2. 调用Claude API
        claude_result = self.claude_model.create_message(
            user_message=user_message,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if not claude_result["success"]:
            return {
                "success": False,
                "error": f"Claude API调用失败: {claude_result['error']}",
                "team_name": team_name,
                "mode": mode,
                "system_prompt_length": len(system_prompt)
            }
        
        # 3. 整合结果
        return {
            "success": True,
            "team_name": team_name,
            "mode": mode,
            "system_prompt": system_prompt,
            "system_prompt_length": len(system_prompt),
            "user_message": user_message,
            "user_message_length": len(user_message),
            "response_content": claude_result["response_content"],
            "response_length": claude_result["response_length"],
            "response_time": claude_result["response_time"],
            "input_tokens": claude_result["input_tokens"],
            "output_tokens": claude_result["output_tokens"],
            "total_tokens": claude_result["total_tokens"],
            "model_name": claude_result["model_name"]
        }
    
    def get_usage_info(self) -> Dict[str, Any]:
        """获取使用信息"""
        return {
            "claude_model": self.claude_model.get_client_info(),
            "team_data_root": self.team_data_root,
            "available_teams": self.get_available_teams()
        }


def create_claude_usage(model_name="claude-sonnet-4-20250514", team_data_root="test_data") -> ClaudeUsage:
    """
    便捷函数：创建Claude使用管理器
    
    Args:
        model_name: Claude模型名称
        team_data_root: 团队数据根目录
    
    Returns:
        ClaudeUsage实例
    """
    return ClaudeUsage(model_name=model_name, team_data_root=team_data_root) 