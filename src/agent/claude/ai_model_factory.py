"""
AI模型工厂模块

支持多个AI模型提供商：Claude (Anthropic), OpenAI, 等
提供统一的工厂接口来创建和管理不同的AI模型实例
"""

from typing import Dict, Any

# 导入基类和各个模型实现
from .ai_model_base import AIModelBase
from .claude_model_impl import ClaudeModel
from .openai_model_impl import OpenAIModel


# 模型配置映射
MODEL_CONFIGS = {
    # Claude models
    "claude-sonnet-4-20250514": {
        "provider": "anthropic",
        "class": ClaudeModel
    },
    "claude-3-5-sonnet-20241022": {
        "provider": "anthropic", 
        "class": ClaudeModel
    },
    "claude-3-5-haiku-20241022": {
        "provider": "anthropic",
        "class": ClaudeModel
    },
    "claude-3-opus-20240229": {
        "provider": "anthropic",
        "class": ClaudeModel
    },
    
    # OpenAI models
    "gpt-4o": {
        "provider": "openai",
        "class": OpenAIModel
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "class": OpenAIModel
    },
    "gpt-4-turbo": {
        "provider": "openai",
        "class": OpenAIModel
    },
    "gpt-3.5-turbo": {
        "provider": "openai",
        "class": OpenAIModel
    },
    "gpt-4.1": {
        "provider": "openai",
        "class": OpenAIModel
    },
    "gpt-4-turbo-2024-04-09": {
        "provider": "openai",
        "class": OpenAIModel
    },
    "gpt-4.1-mini": {
        "provider": "openai",
        "class": OpenAIModel
    },
    "o3-mini": {
        "provider": "openai",
        "class": OpenAIModel,
        "use_completion_tokens": True,
        "force_default_temperature": True
    },
    "o3": {
        "provider": "openai",
        "class": OpenAIModel,
        "use_completion_tokens": True,
        "force_default_temperature": True
    }
}


def create_ai_model(model_name: str = "claude-sonnet-4-20250514") -> AIModelBase:
    """
    便捷函数：创建AI模型实例
    
    Args:
        model_name: AI模型名称
    
    Returns:
        对应的AI模型实例
    """
    if model_name not in MODEL_CONFIGS:
        raise ValueError(f"不支持的模型: {model_name}. 支持的模型: {list(MODEL_CONFIGS.keys())}")
    
    config = MODEL_CONFIGS[model_name]
    model_class = config["class"]
    
    return model_class(model_name)


def list_available_models() -> Dict[str, Dict[str, str]]:
    """列出所有可用的模型"""
    result = {}
    for model_name, config in MODEL_CONFIGS.items():
        result[model_name] = {
            "provider": config["provider"],
            "class_name": config["class"].__name__
        }
    return result


def get_models_by_provider(provider: str) -> list:
    """获取指定提供商的所有模型"""
    return [
        model_name for model_name, config in MODEL_CONFIGS.items()
        if config["provider"] == provider
    ]


# 保持向后兼容
def create_claude_model(model_name="claude-sonnet-4-20250514") -> ClaudeModel:
    """
    便捷函数：创建Claude模型实例（向后兼容）
    
    Args:
        model_name: Claude模型名称
    
    Returns:
        ClaudeModel实例
    """
    if model_name not in MODEL_CONFIGS or MODEL_CONFIGS[model_name]["provider"] != "anthropic":
        raise ValueError(f"不是有效的Claude模型: {model_name}")
    
    return ClaudeModel(model_name)


# 新增便捷函数
def create_openai_model(model_name="gpt-4o") -> OpenAIModel:
    """
    便捷函数：创建OpenAI模型实例
    
    Args:
        model_name: OpenAI模型名称
    
    Returns:
        OpenAIModel实例
    """
    if model_name not in MODEL_CONFIGS or MODEL_CONFIGS[model_name]["provider"] != "openai":
        raise ValueError(f"不是有效的OpenAI模型: {model_name}")
    
    return OpenAIModel(model_name) 