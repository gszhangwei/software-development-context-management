"""
AI模型基类模块

定义了所有AI模型实现必须遵循的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class AIModelBase(ABC):
    """AI模型基类，定义统一接口"""
    
    def __init__(self, model_name: str):
        """
        初始化AI模型
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self.client = None
        self.api_key = None
        self.provider = self._get_provider()
        self._initialize_client()
    
    @abstractmethod
    def _get_provider(self) -> str:
        """获取提供商名称"""
        pass
    
    @abstractmethod
    def _initialize_client(self):
        """初始化客户端"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        pass
    
    @abstractmethod
    def create_message(self, user_message: str, system_prompt: str = None, 
                      max_tokens: int = 20000, temperature: float = 0.7) -> Dict[str, Any]:
        """创建消息"""
        pass
    
    def get_client_info(self) -> Dict[str, Any]:
        """获取客户端信息"""
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "api_key_preview": f"{self.api_key[:8]}...{self.api_key[-4:]}" if self.api_key else None,
            "client_initialized": self.client is not None
        } 