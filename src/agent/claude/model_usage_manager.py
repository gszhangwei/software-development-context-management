"""
AI模型使用管理模块

负责多AI模型的团队上下文生成、API调用和结果处理
支持Claude、OpenAI等多种AI模型提供商
"""

import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.commands.team_context_command import TeamContextCommand
from .ai_model_factory import create_ai_model


class ModelUsageManager:
    """AI模型使用管理类"""
    
    def __init__(self, model_name="claude-sonnet-4-20250514", team_data_root="test_data"):
        """
        初始化AI模型使用管理器
        
        Args:
            model_name: AI模型名称（支持Claude和OpenAI模型）
            team_data_root: 团队数据根目录
        """
        # 使用通用的AI模型工厂，支持Claude和OpenAI等多种模型
        self.ai_model = create_ai_model(model_name)
        self.team_data_root = team_data_root
        self.context_command = TeamContextCommand(root_path=team_data_root)
    
    def get_available_teams(self) -> list:
        """获取可用的团队列表"""
        teams_path = Path(self.team_data_root) / "teams"
        if not teams_path.exists():
            return []
        
        return [d.name for d in teams_path.iterdir() if d.is_dir()]
    
    def generate_team_context(self, team_name: str, mode: str = "framework_only", user_message: str = None) -> Dict[str, Any]:
        """
        生成团队上下文
        
        Args:
            team_name: 团队名称
            mode: 上下文模式 (framework_only, memory_only, hybrid)
            user_message: 用户消息，用于智能选择相关记忆
        
        Returns:
            上下文生成结果
        """
        try:
            # 使用团队上下文命令生成上下文，使用json格式以获取content
            result = self.context_command.execute(
                team_name=team_name,
                mode=mode,
                stages="all",
                memory_types="all",
                project_scope=None,
                memory_importance=2,
                max_memory_items=50,
                tags_filter=None,
                output_format="json",  # 使用json格式确保能获取到content
                save_results=False,    # 不保存文件，只获取内容
                user_message=user_message  # 传递用户消息用于智能记忆选择
            )
            
            # result是CommandResult对象，不是字典
            if result.success:
                # 从data中获取内容
                content = ""
                if result.data and 'content' in result.data:
                    content = result.data['content']
                elif hasattr(result, 'content'):
                    content = result.content
                else:
                    # 如果没有content，使用消息作为内容
                    content = result.message
                
                return {
                    "success": True,
                    "content": content,
                    "team_name": team_name,
                    "mode": mode,
                    "length": len(content)
                }
            else:
                return {
                    "success": False,
                    "error": result.error or result.message,
                    "team_name": team_name,
                    "mode": mode
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Context generation failed: {str(e)}",
                "team_name": team_name,
                "mode": mode
            }
    
    def test_team_context_generation(self) -> Dict[str, Any]:
        """测试团队上下文生成功能"""
        available_teams = self.get_available_teams()
        
        if not available_teams:
            return {
                "success": False,
                "error": "No teams found",
                "teams_count": 0
            }
        
        # 显示可用团队
        print(f"📁 发现团队: {', '.join(available_teams)}")
        
        # 测试第一个团队的上下文生成
        test_team = available_teams[0]
        print(f"🔄 为团队 '{test_team}' 生成上下文...")
        
        results = {}
        modes = ["framework_only", "memory_only", "hybrid"]
        
        for mode in modes:
            print(f"\n   测试模式: {mode}")
            result = self.generate_team_context(test_team, mode)
            
            if result["success"]:
                content_length = result["length"]
                content_preview = result["content"][:200] if result["content"] else ""
                print(f"   ✅ {mode}: {content_length}字符")
                if content_preview:
                    print(f"   预览: {content_preview}...")
                results[mode] = result
            else:
                print(f"   ❌ {mode}: {result['error']}")
                results[mode] = result
        
        return {
            "success": True,
            "available_teams": available_teams,
            "teams_count": len(available_teams),
            "test_team": test_team,
            "mode_results": results
        }
    
    def chat_with_context(self, user_message: str, team_name: str, 
                         mode: str = "framework_only", max_tokens: int = 20000,
                         temperature: float = 0.7) -> Dict[str, Any]:
        """
        使用团队上下文与AI模型对话
        
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
        context_result = self.generate_team_context(team_name, mode, user_message)
        
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
        
        # 2. 调用AI模型API
        ai_result = self.ai_model.create_message(
            user_message=user_message,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if not ai_result["success"]:
            return {
                "success": False,
                "error": f"AI模型API调用失败: {ai_result['error']}",
                "team_name": team_name,
                "mode": mode,
                "system_prompt_length": len(system_prompt)
            }
        
        # 3. 整合结果
        return {
            "success": True,
            "team_name": team_name,
            "mode": mode,
            "user_message": user_message,
            "user_message_length": len(user_message),
            "system_prompt": system_prompt,
            "system_prompt_length": len(system_prompt),
            "response": ai_result["response_content"],
            "response_length": len(ai_result["response_content"]),
            "response_time": ai_result.get("response_time", 0),
            "input_tokens": ai_result.get("input_tokens", 0),
            "output_tokens": ai_result.get("output_tokens", 0),
            "total_tokens": ai_result.get("total_tokens", 0)
        }


def create_model_usage_manager(model_name="claude-sonnet-4-20250514", team_data_root="test_data") -> ModelUsageManager:
    """
    便捷函数：创建AI模型使用管理器
    
    Args:
        model_name: AI模型名称
        team_data_root: 团队数据根目录
    
    Returns:
        ModelUsageManager实例
    """
    return ModelUsageManager(model_name=model_name, team_data_root=team_data_root)


# 向后兼容的别名
def create_claude_usage(model_name="claude-sonnet-4-20250514", team_data_root="test_data") -> ModelUsageManager:
    """向后兼容：创建Claude使用管理器"""
    return create_model_usage_manager(model_name=model_name, team_data_root=team_data_root)


# 保持向后兼容的类别名
ClaudeUsage = ModelUsageManager 