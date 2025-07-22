"""
OpenAI模型实现模块

实现了基于OpenAI API的AI模型
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
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from src.agent.env_config import get_env_config
from .ai_model_base import AIModelBase


class OpenAIModel(AIModelBase):
    """OpenAI模型实现类"""
    
    def _get_provider(self) -> str:
        return "openai"
    
    def _get_token_param_name(self) -> str:
        """获取当前模型应该使用的token参数名称"""
        from .ai_model_factory import MODEL_CONFIGS
        model_config = MODEL_CONFIGS.get(self.model_name, {})
        return "max_completion_tokens" if model_config.get("use_completion_tokens", False) else "max_tokens"
    
    def _should_use_default_temperature(self) -> bool:
        """检查当前模型是否应该使用默认温度"""
        from .ai_model_factory import MODEL_CONFIGS
        model_config = MODEL_CONFIGS.get(self.model_name, {})
        return model_config.get("force_default_temperature", False)
    
    def _initialize_client(self):
        """初始化OpenAI客户端"""
        if not HAS_OPENAI:
            raise ImportError("需要安装openai库: pip install openai")
        
        # 获取API密钥
        env_config = get_env_config()
        self.api_key = env_config.openai_api_key
        
        if not self.api_key:
            raise ValueError("未找到OPENAI_API_KEY，请在.env文件中配置")
        
        # 创建客户端
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def test_connection(self) -> Dict[str, Any]:
        """测试OpenAI API连接"""
        try:
            print(f"✅ OpenAI API密钥已配置: {self.api_key[:8]}...{self.api_key[-4:]}")
            print("✅ OpenAI客户端创建成功")
            
            # 测试简单的API调用
            print("🔄 测试OpenAI API调用...")
            start_time = time.time()
            
            # 根据模型选择正确的token参数
            token_param = self._get_token_param_name()
            api_params = {
                "model": self.model_name,
                token_param: 500,
                "messages": [
                    {
                        "role": "user",
                        "content": "你好！请简单介绍一下你自己。"
                    }
                ]
            }
            
            # 只有在模型支持的情况下才设置temperature
            if not self._should_use_default_temperature():
                api_params["temperature"] = 0.3
            
            response = self.client.chat.completions.create(**api_params)
            
            end_time = time.time()
            
            result = {
                "success": True,
                "provider": self.provider,
                "response_time": end_time - start_time,
                "total_tokens": response.usage.total_tokens,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "response_length": len(response.choices[0].message.content),
                "response_content": response.choices[0].message.content,
                "model_name": self.model_name
            }
            
            print(f"✅ OpenAI API调用成功!")
            print(f"⏱️  响应时间: {result['response_time']:.2f}秒")
            print(f"🔢 使用令牌: {result['total_tokens']}")
            print(f"📝 响应长度: {result['response_length']}字符")
            print(f"📄 响应预览:")
            preview = result['response_content'][:200] + "..." if len(result['response_content']) > 200 else result['response_content']
            print(preview)
            
            return result
            
        except Exception as e:
            print(f"❌ OpenAI连接测试失败: {e}")
            return {
                "success": False,
                "provider": self.provider,
                "error": str(e),
                "model_name": self.model_name
            }
    
    def create_message(self, user_message: str, system_prompt: str = None, 
                      max_tokens: int = 20000, temperature: float = 0.7) -> Dict[str, Any]:
        """创建OpenAI消息"""
        return self._create_message_with_retry(user_message, system_prompt, max_tokens, temperature)
    
    def _create_message_with_retry(self, user_message: str, system_prompt: str = None, 
                                  max_tokens: int = 20000, temperature: float = 0.7, 
                                  max_retries: int = 3) -> Dict[str, Any]:
        """带重试机制的消息创建"""
        import time
        import random
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # 构建消息列表
                messages = []
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                
                messages.append({
                    "role": "user",
                    "content": user_message
                })
                
                # 根据模型选择正确的token参数
                token_param = self._get_token_param_name()
                api_params = {
                    "model": self.model_name,
                    token_param: max_tokens,
                    "messages": messages
                }
                
                # 只有在模型支持的情况下才设置temperature
                if not self._should_use_default_temperature():
                    api_params["temperature"] = temperature
                
                # 调用API
                response = self.client.chat.completions.create(**api_params)
                
                end_time = time.time()
                
                return {
                    "success": True,
                    "provider": self.provider,
                    "response_time": end_time - start_time,
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "response_content": response.choices[0].message.content,
                    "response_length": len(response.choices[0].message.content),
                    "model_name": self.model_name,
                    "system_prompt": system_prompt,
                    "user_message": user_message,
                    "system_prompt_length": len(system_prompt) if system_prompt else 0,
                    "user_message_length": len(user_message),
                    "retry_attempt": attempt + 1
                }
                
            except Exception as e:
                error_str = str(e)
                print(f"⚠️  API调用失败 (尝试 {attempt + 1}/{max_retries}): {error_str}")
                
                # 检查是否是429错误
                if "429" in error_str:
                    if attempt < max_retries - 1:
                        # 如果是429错误且还有重试机会，尝试降级策略
                        if attempt == 0:
                            # 第一次重试：减少max_tokens
                            max_tokens = min(max_tokens // 2, 8000)
                            print(f"🔄 降级策略1: 减少max_tokens到 {max_tokens}")
                        elif attempt == 1:
                            # 第二次重试：使用更便宜的模型
                            original_model = self.model_name
                            if "gpt-4" in self.model_name:
                                self.model_name = "gpt-3.5-turbo"
                                print(f"🔄 降级策略2: 切换到 {self.model_name}")
                        
                        # 等待时间：指数退避 + 随机延迟
                        wait_time = (2 ** attempt) + random.uniform(1, 3)
                        print(f"⏰ 等待 {wait_time:.1f} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                
                # 其他错误或重试次数用完
                return {
                    "success": False,
                    "provider": self.provider,
                    "error": error_str,
                    "model_name": self.model_name,
                    "system_prompt": system_prompt,
                    "user_message": user_message,
                    "retry_attempts": attempt + 1
                }
        
        # 所有重试都失败
        return {
            "success": False,
            "provider": self.provider,
            "error": f"所有 {max_retries} 次重试都失败",
            "model_name": self.model_name,
            "system_prompt": system_prompt,
            "user_message": user_message,
            "retry_attempts": max_retries
        } 