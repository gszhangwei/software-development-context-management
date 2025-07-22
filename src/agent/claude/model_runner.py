#!/usr/bin/env python3
"""
AI模型集成运行器

整合多AI模型创建、使用和存储功能的主调用文件
支持Claude、OpenAI等多种AI模型提供商
"""

import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .ai_model_factory import create_ai_model
from .model_usage_manager import create_model_usage_manager
from .model_storage_manager import create_claude_storage


class ModelRunner:
    """AI模型运行器主类"""
    
    def __init__(self, model_name="claude-sonnet-4-20250514", 
                 team_data_root="test_data", output_dir="output"):
        """
        初始化AI模型运行器
        
        Args:
            model_name: AI模型名称（支持Claude和OpenAI模型）
            team_data_root: 团队数据根目录
            output_dir: 输出目录
        """
        self.model_name = model_name
        self.team_data_root = team_data_root
        self.output_dir = output_dir
        
        # 初始化组件
        self.ai_model = create_ai_model(model_name)
        self.model_usage = create_model_usage_manager(model_name, team_data_root)
        self.model_storage = create_claude_storage(output_dir)
    
    def test_connection(self) -> Dict[str, Any]:
        """测试AI模型API连接"""
        print("🧪 测试AI模型API基本连接")
        print("=" * 40)
        
        result = self.ai_model.test_connection()
        return result
    
    def test_team_context_generation(self) -> Dict[str, Any]:
        """测试团队上下文生成"""
        print("\n🧪 测试团队上下文生成")
        print("=" * 40)
        
        result = self.model_usage.test_team_context_generation()
        return result
    
    def run_with_context(self, user_message: str, team_name: str, 
                        mode: str = "framework_only", max_tokens: int = None,
                        temperature: float = 0.5, save_results: bool = True) -> Dict[str, Any]:
        """
        使用团队上下文运行AI模型
        
        Args:
            user_message: 用户消息
            team_name: 团队名称
            mode: 上下文模式
            max_tokens: 最大令牌数
            temperature: 温度参数
            save_results: 是否保存结果
        
        Returns:
            运行结果
        """
        print(f"\n🧪 测试AI模型 + 团队上下文集成")
        print("=" * 40)
        print(f"🔄 使用团队 '{team_name}' 测试集成...")
        
        # 根据模型类型自动设置合适的max_tokens
        if max_tokens is None:
            from .ai_model_factory import MODEL_CONFIGS
            model_config = MODEL_CONFIGS.get(self.model_name, {})
            provider = model_config.get("provider", "unknown")
            
            if provider == "openai":
                # OpenAI模型通常支持较少的输出token
                max_tokens = 16000  # 为OpenAI模型设置较小的值
            else:
                # Claude等其他模型可以使用更大的值
                max_tokens = 20000
        
        print(f"📊 使用参数: max_tokens={max_tokens}, temperature={temperature}")
        
        # 调用AI模型API
        result = self.model_usage.chat_with_context(
            user_message=user_message,
            team_name=team_name,
            mode=mode,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if not result["success"]:
            print(f"❌ 集成测试失败: {result['error']}")
            return result
        
        # 显示结果统计
        print(f"✅ 集成测试成功!")
        print(f"📊 结果统计:")
        print(f"   - 系统提示词长度: {result['system_prompt_length']}字符")
        print(f"   - 用户消息长度: {result['user_message_length']}字符")
        print(f"   - 响应时间: {result['response_time']:.2f}秒")
        print(f"   - 输入令牌: {result['input_tokens']}")
        print(f"   - 输出令牌: {result['output_tokens']}")
        print(f"   - 总令牌: {result['total_tokens']}")
        print(f"   - 响应长度: {result['response_length']}字符")
        
        # 显示响应预览
        print(f"\n📄 AI响应预览:")
        print("-" * 50)
        response_preview = result["response"][:300] if result["response"] else ""
        print(f"{response_preview}{'...' if len(result['response']) > 300 else ''}")
        print("-" * 50)
        
        # 保存结果（如果需要）
        if save_results:
            try:
                saved_paths = self.model_storage.save_complete_result(result)
                print(f"\n💾 结果已保存:")
                print(f"   - 系统提示词: {saved_paths['system_prompt']}")
                print(f"   - AI响应: {saved_paths['response']}")
                print(f"   - 元数据: {saved_paths['metadata']}")
                
                result["saved_paths"] = saved_paths
                
            except Exception as e:
                print(f"⚠️  保存结果时出错: {e}")
                result["save_error"] = str(e)
        
        return result
    
    def run_comprehensive_test(self, user_message: str = None, context_mode: str = "framework_only") -> Dict[str, Any]:
        """
        运行综合测试
        
        Args:
            user_message: 可选的用户消息
            context_mode: 上下文模式 (framework_only, memory_only, hybrid)
        
        Returns:
            综合测试结果
        """
        print(f"🤖 AI模型综合测试")
        print("=" * 60)
        
        results = {
            "connection_test": None,
            "context_test": None,
            "integration_test": None,
            "success_count": 0,
            "total_tests": 3,
            "context_mode": context_mode
        }
        
        # 1. 连接测试
        connection_result = self.test_connection()
        results["connection_test"] = connection_result
        if connection_result.get("success", False):
            results["success_count"] += 1
        
        # 2. 上下文生成测试
        context_result = self.test_team_context_generation()
        results["context_test"] = context_result
        if context_result.get("success", False):
            results["success_count"] += 1
        
        # 3. 集成测试（如果前面测试成功）
        if results["success_count"] >= 1:  # 至少上下文测试成功
            if user_message is None:
                user_message = "请帮我设计一个高可用性的微服务架构，包括API网关、服务发现、负载均衡和监控组件。"
            
            available_teams = context_result.get("available_teams", [])
            if available_teams:
                test_team = available_teams[0]  # 使用第一个可用团队
                integration_result = self.run_with_context(
                    user_message=user_message,
                    team_name=test_team,
                    mode=context_mode  # 使用传入的上下文模式
                )
                results["integration_test"] = integration_result
                if integration_result.get("success", False):
                    results["success_count"] += 1
        
        # 显示综合结果
        print(f"\n📊 测试结果摘要")
        print("=" * 40)
        print(f"基本连接测试: {'✅ 通过' if results['connection_test'].get('success') else '❌ 失败'}")
        print(f"团队上下文生成测试: {'✅ 通过' if results['context_test'].get('success') else '❌ 失败'}")
        print(f"AI模型 + 上下文集成测试: {'✅ 通过' if results['integration_test'] and results['integration_test'].get('success') else '❌ 失败'}")
        
        print(f"\n总计: {results['success_count']}/{results['total_tests']} 个测试通过")
        
        # 显示存储信息
        storage_info = self.model_storage.get_storage_info()
        print(f"\n📁 存储信息:")
        print(f"   - 系统提示词: {storage_info['system_prompts_count']}个文件")
        print(f"   - AI响应: {storage_info['responses_count']}个文件")
        print(f"   - 元数据: {storage_info['metadata_count']}个文件")
        
        # 最终状态
        if results["success_count"] == results["total_tests"]:
            print(f"\n🎉 所有测试通过！AI模型集成正常工作。")
        elif results["success_count"] > 0:
            print(f"\n⚠️  部分测试失败，请检查配置和网络连接。")
        else:
            print(f"\n❌ 所有测试失败，请检查配置、API密钥和网络连接。")
        
        results["overall_success"] = results["success_count"] == results["total_tests"]
        return results
    
    def get_runner_info(self) -> Dict[str, Any]:
        """获取运行器信息"""
        return {
            "model_name": self.model_name,
            "team_data_root": self.team_data_root,
            "output_dir": self.output_dir,
            "model_info": self.ai_model.get_client_info(),
            "usage_info": {
                "available_teams": self.model_usage.get_available_teams()
            },
            "storage_info": self.model_storage.get_storage_info()
        }


def create_model_runner(model_name="claude-sonnet-4-20250514", 
                       team_data_root="test_data", output_dir="output") -> ModelRunner:
    """
    便捷函数：创建AI模型运行器
    
    Args:
        model_name: AI模型名称
        team_data_root: 团队数据根目录
        output_dir: 输出目录
    
    Returns:
        ModelRunner实例
    """
    return ModelRunner(model_name=model_name, team_data_root=team_data_root, output_dir=output_dir)


# 向后兼容的别名
def create_claude_runner(model_name="claude-sonnet-4-20250514", 
                        team_data_root="test_data", output_dir="output") -> ModelRunner:
    """向后兼容：创建Claude运行器"""
    return create_model_runner(model_name=model_name, team_data_root=team_data_root, output_dir=output_dir)


# 保持向后兼容的类别名
ClaudeRunner = ModelRunner


def main(user_message: str = None):
    """
    主函数
    
    Args:
        user_message: 可选的自定义用户消息
    """
    try:
        # 创建运行器
        runner = create_model_runner()
        
        # 运行综合测试
        result = runner.run_comprehensive_test(user_message)
        
        return result
        
    except Exception as e:
        print(f"❌ 运行器执行失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    main() 