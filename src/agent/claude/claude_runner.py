#!/usr/bin/env python3
"""
Claude API集成运行器

整合模型创建、使用和存储功能的主调用文件
"""

import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .claude_model import create_claude_model
from .claude_usage import create_claude_usage
from .claude_storage import create_claude_storage


class ClaudeRunner:
    """Claude运行器主类"""
    
    def __init__(self, model_name="claude-sonnet-4-20250514", 
                 team_data_root="test_data", output_dir="output"):
        """
        初始化Claude运行器
        
        Args:
            model_name: Claude模型名称
            team_data_root: 团队数据根目录
            output_dir: 输出目录
        """
        self.model_name = model_name
        self.team_data_root = team_data_root
        self.output_dir = output_dir
        
        # 初始化组件
        self.claude_model = create_claude_model(model_name)
        self.claude_usage = create_claude_usage(model_name, team_data_root)
        self.claude_storage = create_claude_storage(output_dir)
    
    def test_connection(self) -> Dict[str, Any]:
        """测试Claude API连接"""
        print("🧪 测试Claude API基本连接")
        print("=" * 40)
        
        result = self.claude_model.test_connection()
        return result
    
    def test_team_context_generation(self) -> Dict[str, Any]:
        """测试团队上下文生成"""
        print("\n🧪 测试团队上下文生成")
        print("=" * 40)
        
        result = self.claude_usage.test_team_context_generation()
        return result
    
    def run_claude_with_context(self, user_message: str, team_name: str, 
                               mode: str = "framework_only", max_tokens: int = 20000,
                               temperature: float = 0.7, save_results: bool = True) -> Dict[str, Any]:
        """
        使用团队上下文运行Claude
        
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
        print(f"\n🧪 测试Claude + 团队上下文集成")
        print("=" * 40)
        print(f"🔄 使用团队 '{team_name}' 测试集成...")
        
        # 调用Claude API
        result = self.claude_usage.chat_with_context(
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
        print(f"\n📄 Claude响应预览:")
        print("-" * 50)
        response_preview = result["response_content"][:800] + "..." if len(result["response_content"]) > 800 else result["response_content"]
        print(response_preview)
        print("-" * 50)
        
        # 保存结果（分开存放）
        if save_results:
            saved_paths = self.claude_storage.save_complete_result(result)
            print(f"\n💾 结果已分开保存:")
            for file_type, path in saved_paths.items():
                print(f"   - {file_type}: {path}")
            
            result["saved_paths"] = saved_paths
        
        return result
    
    def run_comprehensive_test(self, user_message: str = None) -> Dict[str, Any]:
        """
        运行综合测试
        
        Args:
            user_message: 可选的自定义用户消息，如果未提供则使用默认测试消息
        """
        print("🤖 Claude API综合测试")
        print("=" * 60)
        
        tests = []
        results = {}
        
        # 1. 基本连接测试
        try:
            connection_result = self.test_connection()
            tests.append(("基本连接测试", connection_result["success"]))
            results["connection_test"] = connection_result
        except Exception as e:
            tests.append(("基本连接测试", False))
            results["connection_test"] = {"success": False, "error": str(e)}
        
        # 2. 团队上下文生成测试
        try:
            context_result = self.test_team_context_generation()
            tests.append(("团队上下文生成测试", context_result["success"]))
            results["context_test"] = context_result
        except Exception as e:
            tests.append(("团队上下文生成测试", False))
            results["context_test"] = {"success": False, "error": str(e)}
        
        # 3. Claude + 上下文集成测试
        try:
            # 如果没有传入自定义消息，使用默认的业务需求进行测试
            if user_message is None:
                user_message = """## 背景
AIFSD Agent平台需要支持创建"Agents"来管理和调用来自不同来源的智能服务（如大语言模型、语音模型、图像模型等）。后端需要提供API接收前端的字段信息，验证并存储数据，返回创建结果。

## 业务价值
1. **快速部署**: 产品团队和业务线可以通过统一界面快速创建和管理各种类型的agents
2. **访问控制**: 通过"可见范围"字段确保agent使用范围可控
3. **统一管理**: 集中存储agent元数据用于后续统计、审计和维护

请帮我设计这个API的实现方案。"""
            
            teams = self.claude_usage.get_available_teams()
            if teams:
                test_team = teams[0]
                integration_result = self.run_claude_with_context(
                    user_message=user_message,
                    team_name=test_team,
                    mode="framework_only",
                    save_results=True
                )
                tests.append(("Claude + 上下文集成测试", integration_result["success"]))
                results["integration_test"] = integration_result
            else:
                tests.append(("Claude + 上下文集成测试", False))
                results["integration_test"] = {"success": False, "error": "未找到可用团队"}
                
        except Exception as e:
            tests.append(("Claude + 上下文集成测试", False))
            results["integration_test"] = {"success": False, "error": str(e)}
        
        # 显示测试摘要
        print("\n📊 测试结果摘要")
        print("=" * 40)
        passed = 0
        for test_name, success in tests:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{test_name}: {status}")
            if success:
                passed += 1
        
        print(f"\n总计: {passed}/{len(tests)} 个测试通过")
        
        # 显示存储信息
        storage_info = self.claude_storage.get_storage_info()
        print(f"\n📁 存储信息:")
        print(f"   - 系统提示词: {storage_info['system_prompts_count']}个文件")
        print(f"   - Claude响应: {storage_info['responses_count']}个文件")
        print(f"   - 元数据: {storage_info['metadata_count']}个文件")
        
        if passed == len(tests):
            print("\n🎉 所有测试通过！Claude API集成工作正常。")
            print("\n📝 下一步:")
            print(f"- 检查 '{self.output_dir}/' 目录查看分类保存的结果")
            print("- 可以开始使用Claude API进行实际开发")
        else:
            print("\n⚠️  部分测试失败，请检查配置和网络连接。")
        
        return {
            "success": passed == len(tests),
            "passed": passed,
            "total": len(tests),
            "results": results,
            "storage_info": storage_info
        }
    
    def get_runner_info(self) -> Dict[str, Any]:
        """获取运行器信息"""
        return {
            "model_name": self.model_name,
            "team_data_root": self.team_data_root,
            "output_dir": self.output_dir,
            "claude_model": self.claude_model.get_client_info(),
            "usage_info": self.claude_usage.get_usage_info(),
            "storage_info": self.claude_storage.get_storage_info()
        }


def create_claude_runner(model_name="claude-sonnet-4-20250514", 
                        team_data_root="test_data", output_dir="output") -> ClaudeRunner:
    """
    便捷函数：创建Claude运行器
    
    Args:
        model_name: Claude模型名称
        team_data_root: 团队数据根目录
        output_dir: 输出目录
    
    Returns:
        ClaudeRunner实例
    """
    return ClaudeRunner(model_name=model_name, team_data_root=team_data_root, output_dir=output_dir)


def main(user_message: str = None):
    """
    主函数
    
    Args:
        user_message: 可选的自定义用户消息
    """
    try:
        # 创建运行器
        runner = create_claude_runner()
        
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