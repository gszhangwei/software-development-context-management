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
    
    # 启用学习机制（可选）
    print("🎓 是否启用自我学习机制？")
    enable_learning = input("请输入 'y' 启用学习, 其他任意键跳过: ").lower() == 'y'
    
    if enable_learning:
        generator.enable_learning(True)
        print("✅ 自我学习机制已启用")
    else:
        print("ℹ️ 自我学习机制未启用")
    
    # 生成system_prompt
    result = generator.generate_system_prompt(
        user_message=user_message,
        team_name="engineering_team",
        mode="hybrid",
        enable_learning=enable_learning  # 传递学习设置
    )
    
    if result["success"]:
        print("✅ System Prompt生成成功")
        print(f"📝 内容长度: {result['system_prompt_length']}字符")
        
        # 显示匹配的记忆信息
        if result.get("context_data") and "source_memories" in result["context_data"]:
            memory_count = len(result["context_data"]["source_memories"])
            print(f"🧠 匹配记忆数量: {memory_count}")
            if memory_count > 0:
                print(f"📋 记忆列表: {', '.join(result['context_data']['source_memories'][:5])}")
        
        if result.get("saved_to"):
            print(f"💾 已保存到: {result['saved_to']}")
        else:
            print("⚠️  保存位置信息不可用")
        
        # 如果启用了学习，显示学习统计信息
        if enable_learning:
            print("\n📊 学习统计信息:")
            stats = generator.get_learning_statistics("engineering_team")
            if "error" not in stats:
                print(f"   总关键词数: {stats.get('total_keywords', 0)}")
                print(f"   总使用次数: {stats.get('total_keyword_usage', 0)}")
                print(f"   发现关键词数: {stats.get('discovered_keywords', 0)}")
                print(f"   生成会话数: {stats.get('generation_sessions', {}).get('total_sessions', 0)}")
            
            # 询问是否提供使用反馈
            print("\n💬 是否提供System Prompt使用效果反馈？")
            provide_feedback = input("请输入 'y' 提供反馈, 其他任意键跳过: ").lower() == 'y'
            
            if provide_feedback and result.get("context_data") and "source_memories" in result["context_data"]:
                print("📝 请评价System Prompt的效果 (1-5分):")
                try:
                    effectiveness = int(input("评分: "))
                    if 1 <= effectiveness <= 5:
                        comment = input("反馈评论 (可选): ")
                        
                        feedback_result = generator.provide_usage_feedback(
                            team_name="engineering_team",
                            user_message=user_message,
                            system_prompt_effectiveness=effectiveness,
                            matched_memories=result["context_data"]["source_memories"],
                            comment=comment
                        )
                        
                        if feedback_result["success"]:
                            print(f"✅ {feedback_result['message']}")
                        else:
                            print(f"❌ 反馈提交失败: {feedback_result['message']}")
                    else:
                        print("⚠️ 评分必须在1-5之间")
                except ValueError:
                    print("⚠️ 请输入有效的数字评分")
    else:
        print(f"❌ 生成失败: {result['error']}")


if __name__ == "__main__":
    main() 