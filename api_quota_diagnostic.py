#!/usr/bin/env python3
"""
OpenAI API 配额诊断工具

帮助诊断429错误的具体原因和解决方案
"""

import time
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.env_config import get_env_config

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("❌ 需要安装 openai 库: pip install openai")
    sys.exit(1)


def test_minimal_api_call():
    """测试最小的API调用"""
    print("🧪 测试最小API调用...")
    
    env_config = get_env_config()
    if not env_config.openai_api_key:
        print("❌ 未找到 OPENAI_API_KEY")
        return False
    
    client = openai.OpenAI(api_key=env_config.openai_api_key)
    
    try:
        # 使用最小参数
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 使用最便宜的模型
            max_tokens=10,  # 最小token数
            temperature=0,
            messages=[
                {"role": "user", "content": "Hi"}
            ]
        )
        
        print(f"✅ 最小API调用成功!")
        print(f"📊 使用tokens: {response.usage.total_tokens}")
        print(f"📝 响应: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ 最小API调用失败: {e}")
        return False


def test_model_availability():
    """测试不同模型的可用性"""
    print("\n🧪 测试不同模型可用性...")
    
    env_config = get_env_config()
    client = openai.OpenAI(api_key=env_config.openai_api_key)
    
    models_to_test = [
        "gpt-3.5-turbo",
        "gpt-4o-mini", 
        "gpt-4o",
        "gpt-4-turbo"
    ]
    
    results = {}
    
    for model in models_to_test:
        print(f"  🔄 测试 {model}...")
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=5,
                temperature=0,
                messages=[{"role": "user", "content": "Hi"}]
            )
            results[model] = {
                "status": "✅ 成功",
                "tokens": response.usage.total_tokens
            }
            print(f"    ✅ {model}: {response.usage.total_tokens} tokens")
            
            # 添加延迟避免频率限制
            time.sleep(1)
            
        except Exception as e:
            results[model] = {
                "status": "❌ 失败", 
                "error": str(e)
            }
            print(f"    ❌ {model}: {e}")
            
            # 如果是429错误，停止测试其他模型
            if "429" in str(e):
                print("    ⚠️  检测到429错误，停止测试其他模型")
                break
    
    return results


def test_with_delays():
    """测试带延迟的多次调用"""
    print("\n🧪 测试带延迟的多次调用...")
    
    env_config = get_env_config()
    client = openai.OpenAI(api_key=env_config.openai_api_key)
    
    success_count = 0
    total_attempts = 3
    
    for i in range(total_attempts):
        print(f"  🔄 第 {i+1} 次调用...")
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=5,
                temperature=0,
                messages=[{"role": "user", "content": f"Test {i+1}"}]
            )
            success_count += 1
            print(f"    ✅ 成功: {response.usage.total_tokens} tokens")
            
        except Exception as e:
            print(f"    ❌ 失败: {e}")
            if "429" in str(e):
                print("    ⏰ 等待60秒后重试...")
                time.sleep(60)
        
        # 每次调用间隔
        if i < total_attempts - 1:
            print("    ⏰ 等待5秒...")
            time.sleep(5)
    
    print(f"\n📊 成功率: {success_count}/{total_attempts}")
    return success_count > 0


def get_api_key_info():
    """获取API密钥信息"""
    print("🔑 API密钥信息:")
    
    env_config = get_env_config()
    if env_config.openai_api_key:
        key = env_config.openai_api_key
        print(f"  - 密钥长度: {len(key)}")
        print(f"  - 前缀: {key[:7]}...")
        print(f"  - 后缀: ...{key[-4:]}")
        
        # 检查密钥格式
        if key.startswith("sk-"):
            print("  - 格式: ✅ 标准格式")
        else:
            print("  - 格式: ⚠️  非标准格式")
    else:
        print("  - ❌ 未找到API密钥")


def diagnose_429_error():
    """综合诊断429错误"""
    print("🔍 OpenAI API 配额诊断")
    print("=" * 50)
    
    # 1. 检查API密钥
    get_api_key_info()
    
    # 2. 测试最小调用
    if not test_minimal_api_call():
        print("\n💡 建议:")
        print("1. 检查API密钥是否正确")
        print("2. 检查网络连接")
        print("3. 等待一段时间后重试")
        return
    
    # 3. 测试不同模型
    model_results = test_model_availability()
    
    # 4. 测试延迟调用
    delay_success = test_with_delays()
    
    # 5. 生成建议
    print("\n💡 诊断结果和建议:")
    print("=" * 30)
    
    success_models = [m for m, r in model_results.items() if "成功" in r["status"]]
    failed_models = [m for m, r in model_results.items() if "失败" in r["status"]]
    
    if success_models:
        print(f"✅ 可用模型: {', '.join(success_models)}")
    
    if failed_models:
        print(f"❌ 不可用模型: {', '.join(failed_models)}")
    
    if delay_success:
        print("✅ 延迟调用有效，建议添加重试机制")
    else:
        print("❌ 延迟调用仍失败，可能需要等待更长时间")
    
    # 具体建议
    print("\n🛠️  解决方案:")
    if success_models:
        print(f"1. 使用可用模型: {success_models[0]}")
        print("2. 减少max_tokens参数")
        print("3. 添加请求间隔和重试机制")
    
    print("4. 检查OpenAI账户计费状态")
    print("5. 等待配额重置（通常1分钟或1小时）")


if __name__ == "__main__":
    diagnose_429_error() 