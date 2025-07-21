"""
Claude模型创建和管理模块

负责Claude客户端的创建、配置和基本连接测试
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("❌ 需要安装anthropic库: pip install anthropic")

from src.agent.env_config import get_env_config


class ClaudeModel:
    """Claude模型管理类"""
    
    def __init__(self, model_name="claude-sonnet-4-20250514"):
        """
        初始化Claude模型
        
        Args:
            model_name: Claude模型名称
        """
        if not HAS_ANTHROPIC:
            raise ImportError("需要安装anthropic库: pip install anthropic")
        
        self.model_name = model_name
        self.client = None
        self.api_key = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化Claude客户端"""
        # 获取API密钥
        env_config = get_env_config()
        self.api_key = env_config.anthropic_api_key
        
        if not self.api_key:
            raise ValueError("未找到ANTHROPIC_API_KEY，请在.env文件中配置")
        
        # 创建客户端
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def test_connection(self) -> dict:
        """
        测试Claude API连接
        
        Returns:
            测试结果字典
        """
        try:
            print(f"✅ API密钥已配置: {self.api_key[:8]}...{self.api_key[-4:]}")
            print("✅ Anthropic客户端创建成功")
            
            # 测试简单的API调用
            print("🔄 测试简单API调用...")
            start_time = time.time()
            
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=500,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": "你好！请简单介绍一下你自己。"
                    }
                ]
            )
            
            end_time = time.time()
            
            result = {
                "success": True,
                "response_time": end_time - start_time,
                "total_tokens": message.usage.input_tokens + message.usage.output_tokens,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "response_length": len(message.content[0].text),
                "response_content": message.content[0].text,
                "model_name": self.model_name
            }
            
            print(f"✅ API调用成功!")
            print(f"⏱️  响应时间: {result['response_time']:.2f}秒")
            print(f"🔢 使用令牌: {result['total_tokens']}")
            print(f"📝 响应长度: {result['response_length']}字符")
            print(f"📄 响应预览:")
            preview = result['response_content'][:200] + "..." if len(result['response_content']) > 200 else result['response_content']
            print(preview)
            
            return result
            
        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_name": self.model_name
            }
    
    def create_message(self, user_message: str, system_prompt: str = None, 
                      max_tokens: int = 20000, temperature: float = 0.7) -> dict:
        """
        创建Claude消息
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
            max_tokens: 最大令牌数
            temperature: 温度参数
        
        Returns:
            消息创建结果
        """
        try:
            start_time = time.time()
            
            # 构建消息参数
            message_params = {
                "model": self.model_name,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            }
            
            # 如果有系统提示词，添加到参数中
            if system_prompt:
                message_params["system"] = system_prompt
            
            # 调用API
            message = self.client.messages.create(**message_params)
            
            end_time = time.time()
            
            return {
                "success": True,
                "response_time": end_time - start_time,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "total_tokens": message.usage.input_tokens + message.usage.output_tokens,
                "response_content": message.content[0].text,
                "response_length": len(message.content[0].text),
                "model_name": self.model_name,
                "system_prompt": system_prompt,
                "user_message": user_message,
                "system_prompt_length": len(system_prompt) if system_prompt else 0,
                "user_message_length": len(user_message)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_name": self.model_name,
                "system_prompt": system_prompt,
                "user_message": user_message
            }
    
    def get_client_info(self) -> dict:
        """获取客户端信息"""
        return {
            "model_name": self.model_name,
            "api_key_preview": f"{self.api_key[:8]}...{self.api_key[-4:]}" if self.api_key else None,
            "client_initialized": self.client is not None
        }


def create_claude_model(model_name="claude-sonnet-4-20250514") -> ClaudeModel:
    """
    便捷函数：创建Claude模型实例
    
    Args:
        model_name: Claude模型名称
    
    Returns:
        ClaudeModel实例
    """
    return ClaudeModel(model_name=model_name) 