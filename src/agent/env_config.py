"""
环境配置管理模块

用于管理API密钥和其他环境配置
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# 尝试导入dotenv来加载.env文件
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


@dataclass
class EnvConfig:
    """环境配置类"""
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None


def get_env_config() -> EnvConfig:
    """
    获取环境配置
    
    Returns:
        EnvConfig实例
    """
    # 尝试加载.env文件
    _load_env_file()
    return EnvConfig(
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )


def _load_env_file():
    """加载.env文件"""
    if HAS_DOTENV:
        # 查找.env文件，从当前模块向上搜索
        current_path = Path(__file__).parent
        for _ in range(5):  # 最多向上搜索5层目录
            env_file = current_path / '.env'
            if env_file.exists():
                load_dotenv(env_file)
                break
            current_path = current_path.parent
    else:
        # 如果没有dotenv库，尝试手动加载.env文件
        _manual_load_env_file()


def _manual_load_env_file():
    """手动加载.env文件（当没有python-dotenv时）"""
    current_path = Path(__file__).parent
    for _ in range(5):  # 最多向上搜索5层目录
        env_file = current_path / '.env'
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # 移除引号
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            os.environ[key] = value
                break
            except Exception as e:
                # 忽略读取错误，继续搜索
                pass
        current_path = current_path.parent 