"""
Claude模型实现模块

实现了基于Anthropic Claude API的AI模型
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 检查依赖包
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from src.agent.env_config import get_env_config
from .ai_model_base import AIModelBase


class ClaudeModel(AIModelBase):
    """Claude模型实现类"""
    
    def _get_provider(self) -> str:
        return "anthropic"
    
    def _initialize_client(self):
        """初始化Claude客户端"""
        if not HAS_ANTHROPIC:
            raise ImportError("需要安装anthropic库: pip install anthropic")
        
        # 获取API密钥
        env_config = get_env_config()
        self.api_key = env_config.anthropic_api_key
        
        if not self.api_key:
            raise ValueError("未找到ANTHROPIC_API_KEY，请在.env文件中配置")
        
        # 创建客户端
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def test_connection(self) -> Dict[str, Any]:
        """测试Claude API连接"""
        try:
            print(f"✅ Anthropic API密钥已配置: {self.api_key[:8]}...{self.api_key[-4:]}")
            print("✅ Anthropic客户端创建成功")
            
            # 测试简单的API调用
            print("🔄 测试Claude API调用...")
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
                "provider": self.provider,
                "response_time": end_time - start_time,
                "total_tokens": message.usage.input_tokens + message.usage.output_tokens,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "response_length": len(message.content[0].text),
                "response_content": message.content[0].text,
                "model_name": self.model_name
            }
            
            print(f"✅ Claude API调用成功!")
            print(f"⏱️  响应时间: {result['response_time']:.2f}秒")
            print(f"🔢 使用令牌: {result['total_tokens']}")
            print(f"📝 响应长度: {result['response_length']}字符")
            print(f"📄 响应预览:")
            preview = result['response_content'][:200] + "..." if len(result['response_content']) > 200 else result['response_content']
            print(preview)
            
            return result
            
        except Exception as e:
            print(f"❌ Claude连接测试失败: {e}")
            return {
                "success": False,
                "provider": self.provider,
                "error": str(e),
                "model_name": self.model_name
            }
    
    def create_message(self, user_message: str, system_prompt: str = None, 
                      max_tokens: int = 20000, temperature: float = 0.7) -> Dict[str, Any]:
        """创建Claude消息"""
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
                "provider": self.provider,
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
                "provider": self.provider,
                "error": str(e),
                "model_name": self.model_name,
                "system_prompt": system_prompt,
                "user_message": user_message
            } 