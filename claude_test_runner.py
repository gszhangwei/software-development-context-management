#!/usr/bin/env python3
"""
多模型AI API集成测试运行器

功能特性：
1. 🤖 多模型支持：同时支持 Claude 和 OpenAI 模型
2. 🔍 智能检测：自动检测 .env 文件中的 API keys
3. 🥇 优先级逻辑：Claude > OpenAI（如果两个都可用，优先使用 Claude）
4. ⚙️  自适应配置：根据模型类型自动调整参数（如 max_tokens）
5. 🧪 综合测试：API连接、上下文生成、集成测试
6. 📊 批量测试：支持测试所有可用模型
7. 💾 结果保存：自动保存系统提示词、AI响应和元数据
8. 🎯 演示模式：可视化展示 API key 优先级逻辑

支持的模型：
- Claude: claude-sonnet-4-20250514, claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-opus-20240229
- OpenAI: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo

使用方法：
1. 在项目根目录创建 .env 文件并配置 API keys
2. 运行 python claude_test_runner.py
3. 选择测试模式进行测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.claude import (
    create_model_runner, 
    list_available_models, 
    get_models_by_provider
)
from src.agent.env_config import get_env_config


def detect_available_models() -> dict:
    """
    检测可用的模型
    
    Returns:
        包含可用模型信息的字典
    """
    print("🔍 检测可用的API配置...")
    
    # 获取环境配置
    env_config = get_env_config()
    
    available_models = {
        "claude": [],
        "openai": [],
        "selected_model": None,
        "selected_provider": None
    }
    
    # 检查Claude API Key
    if env_config.anthropic_api_key:
        claude_models = get_models_by_provider("anthropic")
        available_models["claude"] = claude_models
        print(f"✅ 发现 Claude API Key，可用模型: {len(claude_models)}个")
        for model in claude_models[:3]:  # 显示前3个
            print(f"   - {model}")
        if len(claude_models) > 3:
            print(f"   - ...还有{len(claude_models) - 3}个模型")
    else:
        print("❌ 未找到 ANTHROPIC_API_KEY")
    
    # 检查OpenAI API Key
    if env_config.openai_api_key:
        openai_models = get_models_by_provider("openai")
        available_models["openai"] = openai_models
        print(f"✅ 发现 OpenAI API Key，可用模型: {len(openai_models)}个")
        for model in openai_models[:3]:  # 显示前3个
            print(f"   - {model}")
        if len(openai_models) > 3:
            print(f"   - ...还有{len(openai_models) - 3}个模型")
    else:
        print("❌ 未找到 OPENAI_API_KEY")
    
    # 选择模型（优先级：Claude > OpenAI）
    if available_models["claude"]:
        available_models["selected_model"] = "claude-sonnet-4-20250514"  # 默认Claude模型
        available_models["selected_provider"] = "claude"
        print(f"🎯 选择 Claude 模型: {available_models['selected_model']}")
    elif available_models["openai"]:
        available_models["selected_model"] = "o3"  # 默认OpenAI模型
        available_models["selected_provider"] = "openai"
        print(f"🎯 选择 OpenAI 模型: {available_models['selected_model']}")
    else:
        print("❌ 未找到任何可用的API密钥!")
        print("💡 请在项目根目录创建 .env 文件并配置以下任一密钥:")
        print("   ANTHROPIC_API_KEY=your_claude_api_key")
        print("   OPENAI_API_KEY=your_openai_api_key")
    
    return available_models


def load_user_message(file_path: str = "user_message.txt") -> str:
    """
    从文件加载用户消息
    
    Args:
        file_path: 消息文件路径
        
    Returns:
        用户消息内容，如果文件不存在则返回None
    """
    try:
        file_path = Path(file_path)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    print(f"✅ 从 '{file_path}' 加载用户消息成功")
                    print(f"📄 消息预览: {content[:100]}{'...' if len(content) > 100 else ''}")
                    return content
                else:
                    print(f"⚠️  文件 '{file_path}' 为空")
                    return None
        else:
            print(f"📝 未找到消息文件 '{file_path}'，将使用默认测试消息")
            return None
    except Exception as e:
        print(f"❌ 读取消息文件失败: {e}")
        return None


def main(message_file: str = "user_message.txt", model_name: str = None, context_mode: str = "hybrid"):
    """
    主函数
    
    Args:
        message_file: 用户消息文件路径
        model_name: 可选的指定模型名称，如果不提供则自动检测
        context_mode: 上下文模式 (framework_only, memory_only, hybrid)
    """
    print("🚀 启动多模型AI API集成测试")
    print("=" * 60)
    
    try:
        # 检测可用模型
        available_models = detect_available_models()
        
        # 如果没有指定模型，使用自动检测的模型
        if model_name is None:
            model_name = available_models["selected_model"]
        
        if not model_name:
            return {"success": False, "error": "没有可用的API密钥或模型"}
        
        # 加载用户消息
        user_message = load_user_message(message_file)
        
        print(f"\n" + "=" * 60)
        print(f"🤖 开始测试模型: {model_name}")
        print(f"🔧 上下文模式: {context_mode}")
        print("=" * 60)
        
        # 创建模型运行器
        runner = create_model_runner(
            model_name=model_name,
            team_data_root="test_data",
            output_dir="output"
        )
        
        print("✅ 模型运行器创建成功")
        
        # 显示运行器信息
        info = runner.get_runner_info()
        print(f"📋 运行器配置:")
        print(f"   - 模型: {info['model_name']}")
        print(f"   - 提供商: {available_models['selected_provider']}")
        print(f"   - 团队数据: {info['team_data_root']}")
        print(f"   - 输出目录: {info['output_dir']}")
        print(f"   - 可用团队: {len(info['usage_info']['available_teams'])}个")
        
        # 运行综合测试
        print(f"\n🔄 开始运行综合测试...")
        result = runner.run_comprehensive_test(user_message, context_mode)
        
        # 添加模型信息到结果
        result["model_info"] = {
            "selected_model": model_name,
            "selected_provider": available_models["selected_provider"],
            "available_models": available_models,
            "context_mode": context_mode
        }
        
        return result
        
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_all_available_models(context_mode: str = "hybrid"):
    """测试所有可用的模型
    
    Args:
        context_mode: 上下文模式 (framework_only, memory_only, hybrid)
    """
    print("🧪 测试所有可用模型")
    print(f"🔧 使用上下文模式: {context_mode}")
    print("=" * 60)
    
    # 检测可用模型
    available_models = detect_available_models()
    
    all_models = available_models["claude"] + available_models["openai"]
    
    if not all_models:
        print("❌ 没有找到可用的模型")
        return
    
    results = {}
    
    for model_name in all_models:
        print(f"\n" + "=" * 40)
        print(f"🔄 测试模型: {model_name}")
        print("=" * 40)
        
        try:
            result = main("user_message.txt", model_name, context_mode)
            results[model_name] = result
            
            if result.get("success", False):
                print(f"✅ {model_name} 测试成功")
            else:
                print(f"❌ {model_name} 测试失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"❌ {model_name} 测试异常: {e}")
            results[model_name] = {"success": False, "error": str(e)}
    
    # 显示汇总结果
    print(f"\n" + "=" * 60)
    print("📊 所有模型测试结果汇总")
    print("=" * 60)
    
    for model_name, result in results.items():
        status = "✅ 成功" if result.get("success", False) else "❌ 失败"
        print(f"{model_name}: {status}")
    
    return results


def quick_test():
    """快速测试函数"""
    try:
        from src.agent.claude import create_ai_model, create_model_usage_manager, create_model_storage_manager
        
        print("🧪 快速功能测试")
        print("=" * 30)
        
        # 检测可用模型
        available_models = detect_available_models()
        
        if not available_models["selected_model"]:
            print("❌ 没有可用的模型进行测试")
            return False
        
        model_name = available_models["selected_model"]
        
        # 测试模型创建
        model = create_ai_model(model_name)
        print(f"✅ 模型创建成功: {model_name}")
        
        # 测试使用管理器
        usage = create_model_usage_manager(model_name)
        teams = usage.get_available_teams()
        print(f"✅ 使用管理器创建成功，发现{len(teams)}个团队")
        
        # 测试存储管理器
        storage = create_model_storage_manager()
        storage_info = storage.get_storage_info()
        print(f"✅ 存储管理器创建成功")
        
        print("\n📁 存储目录结构:")
        print(f"   - 系统提示词: {storage_info['system_prompts_dir']}")
        print(f"   - AI响应: {storage_info['responses_dir']}")
        print(f"   - 元数据: {storage_info['metadata_dir']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 快速测试失败: {e}")
        return False


def demo_usage():
    """使用演示"""
    print("\n💡 使用演示")
    print("=" * 30)
    
    print("# 基本使用方法:")
    print("""
# 1. 配置 API Keys（在项目根目录创建 .env 文件）
# 对于 Claude (第一优先级):
ANTHROPIC_API_KEY=your_claude_api_key_here

# 对于 OpenAI (第二优先级):
OPENAI_API_KEY=your_openai_api_key_here

# 重要：
# - 如果两个都配置，会优先使用 Claude
# - 只需要配置一个即可正常工作
# - 系统会自动检测并选择最佳模型

# 2. 创建用户消息文件 (user_message.txt)
echo "请帮我设计一个用户认证API" > user_message.txt

# 3. 运行测试（会自动检测并选择合适的模型和混合模式）
python claude_test_runner.py

# 4. 或者指定自定义消息文件和上下文模式
from claude_test_runner import main
main("my_custom_message.txt", None, "hybrid")  # 使用混合模式
main("my_custom_message.txt", None, "framework_only")  # 仅使用框架
main("my_custom_message.txt", None, "memory_only")  # 仅使用记忆

# 5. 指定特定模型和上下文模式
main("user_message.txt", "gpt-4o", "hybrid")  # OpenAI + 混合模式
main("user_message.txt", "claude-sonnet-4-20250514", "hybrid")  # Claude + 混合模式

# 6. 测试所有可用模型（使用混合模式）
from claude_test_runner import test_all_available_models
test_all_available_models("hybrid")
test_all_available_models("framework_only")
""")

    print("# 上下文模式详解:")
    print("""
混合模式 (hybrid) - 推荐模式:
- 结合团队记忆和七阶段框架
- 为每个框架阶段添加相关的历史经验
- 提供最全面的上下文信息
- 适用于复杂项目和需要综合考虑的场景

仅框架模式 (framework_only):
- 只使用七阶段框架模板
- 标准化的结构和流程
- 适用于新项目启动和标准化开发

仅记忆模式 (memory_only):
- 只使用团队历史记忆
- 基于过往经验的建议
- 适用于回顾和经验总结
""")

    print("# 支持的模型:")
    print("""
Claude 模型:
- claude-sonnet-4-20250514
- claude-3-5-sonnet-20241022
- claude-3-5-haiku-20241022
- claude-3-opus-20240229

OpenAI 模型:
- gpt-4o
- gpt-4o-mini
- gpt-4-turbo
- gpt-3.5-turbo
""")

    print("# 分开的模块使用:")
    print("""
# 检测可用模型
from claude_test_runner import detect_available_models
models = detect_available_models()

# 使用特定模型和混合模式
from src.agent.claude import create_ai_model
model = create_ai_model("gpt-4o")  # OpenAI
model = create_ai_model("claude-sonnet-4-20250514")  # Claude

# 创建运行器并使用混合模式
from src.agent.claude import create_model_runner
runner = create_model_runner("gpt-4o")
result = runner.run_with_context(
    user_message="设计一个API",
    team_name="engineering_team", 
    mode="hybrid"  # 使用混合模式
)
""")


def create_sample_message_file():
    """创建示例消息文件"""
    sample_content = """## 背景
我需要为一个电商平台设计用户认证和授权系统。

## 需求
1. 用户注册和登录功能
2. JWT token管理
3. 角色权限控制（普通用户、管理员）
4. 密码重置功能
5. 多端登录支持

## 技术栈
- 后端：Python FastAPI
- 数据库：PostgreSQL
- 缓存：Redis

请帮我设计这个认证系统的完整方案。"""
    
    try:
        with open("user_message.txt", "w", encoding="utf-8") as f:
            f.write(sample_content)
        print("✅ 已创建示例消息文件 'user_message.txt'")
        return True
    except Exception as e:
        print(f"❌ 创建示例文件失败: {e}")
        return False


def create_sample_env_file():
    """创建示例 .env 文件"""
    sample_content = """# AI API Keys Configuration
# 配置你的 AI API 密钥（只需要配置其中一个，或两个都配置）

# Claude (Anthropic) API Key - 优先级更高
# 获取地址: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_claude_api_key_here

# OpenAI API Key - 如果没有 Claude key 会使用这个
# 获取地址: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# 注意:
# 1. 请将 "your_xxx_api_key_here" 替换为你的真实 API key
# 2. 如果两个 key 都配置，会优先使用 Claude
# 3. 至少需要配置一个 key 才能正常工作
"""
    
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(sample_content)
        print("✅ 已创建示例 .env 文件")
        print("⚠️  请编辑 .env 文件，添加你的真实 API keys")
        return True
    except Exception as e:
        print(f"❌ 创建示例 .env 文件失败: {e}")
        return False


def demo_priority_logic():
    """演示API key优先级逻辑"""
    print("🎯 API Key 优先级演示")
    print("=" * 50)
    
    # 模拟不同的环境配置场景
    scenarios = [
        {
            "name": "只有 Claude API Key",
            "anthropic_api_key": "sk-ant-xxx",
            "openai_api_key": None
        },
        {
            "name": "只有 OpenAI API Key", 
            "anthropic_api_key": None,
            "openai_api_key": "sk-xxx"
        },
        {
            "name": "两个 API Key 都存在",
            "anthropic_api_key": "sk-ant-xxx",
            "openai_api_key": "sk-xxx"
        },
        {
            "name": "没有任何 API Key",
            "anthropic_api_key": None,
            "openai_api_key": None
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 场景 {i}: {scenario['name']}")
        print("-" * 30)
        
        # 模拟检测逻辑
        claude_available = bool(scenario["anthropic_api_key"])
        openai_available = bool(scenario["openai_api_key"])
        
        print(f"Claude API Key: {'✅ 可用' if claude_available else '❌ 未配置'}")
        print(f"OpenAI API Key: {'✅ 可用' if openai_available else '❌ 未配置'}")
        
        # 应用优先级逻辑
        if claude_available:
            selected = "Claude (claude-sonnet-4-20250514)"
            priority = "🥇 第一优先级"
        elif openai_available:
            selected = "OpenAI (gpt-4o)"
            priority = "🥈 第二优先级"
        else:
            selected = "无可用模型"
            priority = "❌ 需要配置API key"
        
        print(f"选择结果: {selected}")
        print(f"选择原因: {priority}")


def run_non_interactive():
    """非交互式运行模式"""
    print("🤖 非交互式测试模式")
    print("=" * 50)
    
    # 直接运行完整测试
    result = main("user_message.txt")
    
    if result and result.get("overall_success"):
        print("\n🎉 非交互式测试完成且成功！")
    elif result and result.get("success_count", 0) > 0:
        print(f"\n✅ 非交互式测试部分成功！通过 {result.get('success_count', 0)}/{result.get('total_tests', 3)} 个测试")
    else:
        print(f"\n❌ 非交互式测试失败: {result.get('error', '未知错误') if result else '无结果'}")
    
    return result


if __name__ == "__main__":
    import os
    
    # 检查是否有非交互式环境变量
    if os.getenv("NON_INTERACTIVE") or "--non-interactive" in sys.argv:
        run_non_interactive()
    else:
        # 原有的交互式逻辑
        # 运行快速测试
        if quick_test():
            print("\n" + "=" * 60)
            
            # 检查是否存在消息文件
            message_file = Path("user_message.txt")
            if not message_file.exists():
                print(f"📝 未找到消息文件 '{message_file}'")
                try:
                    create_file = input("是否创建示例消息文件？(y/n): ").lower()
                    if create_file.startswith('y'):
                        create_sample_message_file()
                except KeyboardInterrupt:
                    print("\n\n👋 已取消")
            
            # 检查是否存在 .env 文件
            env_file = Path(".env")
            if not env_file.exists():
                print(f"📝 未找到 .env 配置文件")
                try:
                    create_env = input("是否创建示例 .env 文件？(y/n): ").lower()
                    if create_env.startswith('y'):
                        create_sample_env_file()
                except KeyboardInterrupt:
                    print("\n\n👋 已取消")
            
            # 询问是否运行完整测试
            try:
                response = input("\n选择测试模式:\n1. 自动检测并测试单个模型 (y)\n2. 测试所有可用模型 (a)\n3. 演示API key优先级逻辑 (p)\n4. 跳过测试 (n)\n请选择 (y/a/p/n): ").lower()
                
                # 询问上下文模式
                context_mode = "hybrid"  # 默认值
                if response.startswith('y') or response.startswith('a'):
                    context_input = input("\n选择上下文模式:\n1. 混合模式 - 记忆+框架 (hybrid, 推荐)\n2. 仅框架模式 (framework)\n3. 仅记忆模式 (memory)\n请选择 (hybrid/framework/memory, 默认 hybrid): ").lower().strip()
                    
                    if context_input in ['framework', 'framework_only', 'f']:
                        context_mode = "framework_only"
                    elif context_input in ['memory', 'memory_only', 'm']:
                        context_mode = "memory_only"
                    else:
                        context_mode = "hybrid"  # 默认使用混合模式
                    
                    print(f"✅ 已选择上下文模式: {context_mode}")
                
                if response.startswith('a'):
                    test_all_available_models(context_mode)
                elif response.startswith('p'):
                    demo_priority_logic()
                elif response.startswith('y'):
                    # 询问消息文件路径
                    try:
                        file_input = input("消息文件路径 (回车使用 'user_message.txt'): ").strip()
                        message_file_path = file_input if file_input else "user_message.txt"
                        main(message_file_path, None, context_mode)
                    except KeyboardInterrupt:
                        print("\n\n👋 测试已取消")
                else:
                    print("✅ 快速测试完成")
                    demo_usage()
            except KeyboardInterrupt:
                print("\n\n👋 测试已取消")
        else:
            print("❌ 快速测试失败，请检查配置")
            print("\n💡 可能的解决方案:")
            print("1. 确保已安装所有依赖: pip install -r requirements.txt")
            print("2. 配置 API keys 在 .env 文件中")
            print("3. 检查网络连接") 