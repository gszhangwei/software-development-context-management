#!/usr/bin/env python3
"""
使用user_message.txt生成System Prompt
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.system_prompt_generator import create_system_prompt_generator


def main():
    # 读取用户消息
    user_message_file = Path("user_message.txt")
    if not user_message_file.exists():
        print("❌ 未找到 user_message.txt 文件")
        return
    
    user_message = user_message_file.read_text(encoding='utf-8').strip()
    
    # 创建生成器
    generator = create_system_prompt_generator()
    
    # 生成system_prompt
    result = generator.generate_system_prompt(
        user_message=user_message,
        team_name="engineering_team",
        mode="hybrid"
    )
    
    if result["success"]:
        print("✅ System Prompt生成成功")
        print(f"📝 内容长度: {result['system_prompt_length']}字符")
        if result.get("saved_to"):
            print(f"💾 已保存到: {result['saved_to']}")
        else:
            print("⚠️  保存位置信息不可用")
    else:
        print(f"❌ 生成失败: {result['error']}")


if __name__ == "__main__":
    main() 