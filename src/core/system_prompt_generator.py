#!/usr/bin/env python3
"""
System Prompt生成器

专门用于根据user_message找到合适的记忆，然后结合七步框架生成system_prompt
与claude_test_runner.py全面测试过程中的system_prompt生成过程完全保持一致

功能特性：
1. 🔍 智能记忆选择：根据用户消息内容智能匹配相关记忆
2. 📋 七步框架集成：结合完整的七阶段框架模板
3. 🎯 混合模式：记忆+框架的最优组合
4. 🧠 增强评分：使用增强评分算法进行智能记忆选择
5. 🎓 自我学习：可选的学习机制，基于System Prompt使用效果
6. ⚙️  参数化配置：支持灵活的生成参数配置
7. 💾 结果输出：可选择保存或直接返回生成的system_prompt

使用方法：
1. 创建生成器实例
2. 调用generate_system_prompt方法
3. 获取结果system_prompt
4. 可选：提供使用反馈以触发学习
"""

import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.commands.team_context_command import TeamContextCommand


class SystemPromptGenerator:
    """System Prompt生成器类"""
    
    def __init__(self, team_data_root: str = "test_data"):
        """
        初始化System Prompt生成器
        
        Args:
            team_data_root: 团队数据根目录
        """
        self.team_data_root = team_data_root
        self.context_command = TeamContextCommand(root_path=team_data_root)
        
        # 确保输出目录存在
        self.output_dir = project_root / "output" / "system_prompts"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 学习相关状态
        self._learning_enabled = False
        self._scoring_engine_cache = {}  # 缓存评分引擎
        self._generation_sessions = []   # 记录生成会话
    
    def enable_learning(self, enabled: bool = True):
        """
        启用或禁用自我学习机制
        
        Args:
            enabled: 是否启用学习
        """
        self._learning_enabled = enabled
        if enabled:
            print("🎓 自我学习机制已启用")
        else:
            print("🔒 自我学习机制已禁用")
    
    def _get_scoring_engine(self, team_name: str):
        """获取或创建团队的评分引擎"""
        if not self._learning_enabled:
            return None
            
        if team_name not in self._scoring_engine_cache:
            try:
                from src.scoring_self_evolution import SelfLearningMemoryScoringEngine
                from src.core.directory_manager import DirectoryManager
                
                # 获取团队的矩阵文件路径
                dir_manager = DirectoryManager(self.team_data_root)
                team_path = dir_manager.get_team_path(team_name)
                matrix_file = team_path / "memory" / "keyword_matrix.json"
                
                # 创建或加载评分引擎
                if matrix_file.exists():
                    engine = SelfLearningMemoryScoringEngine(str(matrix_file))
                else:
                    engine = SelfLearningMemoryScoringEngine()
                    # 确保目录存在
                    matrix_file.parent.mkdir(parents=True, exist_ok=True)
                
                self._scoring_engine_cache[team_name] = {
                    'engine': engine,
                    'matrix_file': matrix_file
                }
                
            except ImportError:
                print("⚠️ 自学习评分引擎不可用")
                return None
                
        return self._scoring_engine_cache[team_name]
    
    def _record_generation_session(self, team_name: str, user_message: str, 
                                  generation_result: Dict[str, Any], 
                                  matched_memories: list = None):
        """记录生成会话信息，用于潜在的学习"""
        if not self._learning_enabled:
            return
            
        session = {
            'session_id': f"prompt_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'team_name': team_name,
            'user_message': user_message,
            'user_message_length': len(user_message),
            'system_prompt_length': generation_result.get('system_prompt_length', 0),
            'matched_memories': matched_memories or [],
            'mode': generation_result.get('mode', 'unknown'),
            'success': generation_result.get('success', False)
        }
        
        self._generation_sessions.append(session)
        
        # 保持最多100个会话记录
        if len(self._generation_sessions) > 100:
            self._generation_sessions = self._generation_sessions[-100:]
    
    def _save_system_prompt(self, system_prompt: str, team_name: str, mode: str, user_message: str = "") -> str:
        """
        保存system prompt到output/system_prompts目录
        
        Args:
            system_prompt: 要保存的system prompt内容
            team_name: 团队名称
            mode: 生成模式
            user_message: 用户消息（用于生成描述）
        
        Returns:
            保存的文件路径
        """
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成文件名
        filename = f"{timestamp}_{team_name}_{mode}_system_prompt.txt"
        file_path = self.output_dir / filename
        
        # 准备文件内容
        content_lines = [
            "=" * 80,
            f"System Prompt Generated - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            f"Team: {team_name}",
            f"Mode: {mode}",
            f"Generated by: SystemPromptGenerator",
            ""
        ]
        
        # 如果有用户消息，添加到文件头
        if user_message.strip():
            content_lines.extend([
                "User Message Context:",
                "-" * 40,
                user_message,
                "",
                "Generated System Prompt:",
                "-" * 40,
                ""
            ])
        else:
            content_lines.extend([
                "Generated System Prompt:",
                "-" * 40,
                ""
            ])
        
        # 写入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content_lines))
                f.write(system_prompt)
                f.write('\n')
            
            return str(file_path)
        except Exception as e:
            raise Exception(f"保存system prompt失败: {e}")
    
    def get_available_teams(self) -> list:
        """获取可用的团队列表"""
        teams_path = Path(self.team_data_root) / "teams"
        if not teams_path.exists():
            return []
        
        return [d.name for d in teams_path.iterdir() if d.is_dir()]
    
    def generate_system_prompt(self, 
                             user_message: str,
                             team_name: str,
                             mode: str = "hybrid",
                             stages: Optional[str] = None,
                             memory_types: str = "all",
                             project_scope: Optional[str] = None,
                             memory_importance: int = 2,
                             max_memory_items: int = 50,
                             tags_filter: Optional[str] = None,
                             save_results: bool = False,
                             verbose: bool = True,
                             enable_learning: Optional[bool] = None) -> Dict[str, Any]:
        """
        生成系统提示词
        
        Args:
            user_message: 用户消息，用于智能选择相关记忆
            team_name: 团队名称
            mode: 上下文模式 (framework_only, memory_only, hybrid)
            stages: 框架阶段 (逗号分隔或'all')
            memory_types: 记忆类型 ('declarative', 'procedural', 'episodic', 'all')
            project_scope: 项目范围过滤器
            memory_importance: 记忆重要性阈值 (1-5)
            max_memory_items: 最大记忆条目数
            tags_filter: 标签过滤器 (逗号分隔)
            save_results: 是否保存结果到文件
            verbose: 是否显示详细信息
            enable_learning: 为本次生成临时启用/禁用学习（覆盖全局设置）
            
        Returns:
            包含system_prompt和元数据的结果字典
        """
        try:
            # 临时学习设置
            original_learning_enabled = self._learning_enabled
            if enable_learning is not None:
                self._learning_enabled = enable_learning
            
            if verbose:
                print(f"🤖 开始生成System Prompt")
                if self._learning_enabled:
                    print(f"🎓 学习模式: 启用")
                print(f"📋 配置参数:")
                print(f"   - 团队: {team_name}")
                print(f"   - 模式: {mode}")
                print(f"   - 用户消息: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
                print(f"   - 记忆重要性: {memory_importance}")
                print(f"   - 最大记忆数: {max_memory_items}")
            
            # 验证团队存在
            available_teams = self.get_available_teams()
            if team_name not in available_teams:
                return {
                    "success": False,
                    "error": f"团队 '{team_name}' 不存在。可用团队: {available_teams}",
                    "available_teams": available_teams
                }
            
            # 使用团队上下文命令生成上下文 - 完全复制claude_test_runner.py的逻辑
            if verbose:
                print(f"🔄 调用团队上下文生成...")
            
            result = self.context_command.execute(
                team_name=team_name,
                action="generate",
                mode=mode,
                stages=stages or "all",
                memory_types=memory_types,
                output_format="json",  # 使用json格式以获取content
                save_results=save_results,
                project_scope=project_scope,
                memory_importance=memory_importance,
                max_memory_items=max_memory_items,
                tags_filter=tags_filter,
                user_message=user_message  # 传递用户消息用于智能记忆选择
            )
            
            if not result.success:
                return {
                    "success": False,
                    "error": f"上下文生成失败: {result.error or result.message}",
                    "team_name": team_name,
                    "mode": mode
                }
            
            # 从结果中提取system_prompt内容
            system_prompt = ""
            if hasattr(result, 'data') and result.data and 'content' in result.data:
                system_prompt = result.data['content']
            elif hasattr(result, 'content'):
                system_prompt = result.content
            else:
                system_prompt = result.message
            
            # 如果没有生成有效内容，使用默认提示词
            if not system_prompt or system_prompt.strip() == "":
                system_prompt = f"你是一个为{team_name}团队工作的AI助手。请根据团队经验和最佳实践提供有用、准确的响应。"
            
            # 获取匹配的记忆信息
            matched_memories = []
            if result.data and 'source_memories' in result.data:
                matched_memories = result.data['source_memories']
            
            # 显示生成结果统计
            if verbose:
                print(f"✅ System Prompt生成成功!")
                print(f"📊 生成统计:")
                print(f"   - 内容长度: {len(system_prompt)}字符")
                print(f"   - 生成模式: {mode}")
                
                # 显示生成的记忆信息（如果有）
                if result.data and 'source_memories' in result.data:
                    memory_count = len(result.data['source_memories'])
                    print(f"   - 使用记忆: {memory_count}个")
                    if memory_count > 0:
                        print(f"   - 记忆来源: {', '.join(result.data['source_memories'][:5])}{'...' if memory_count > 5 else ''}")
                
                # 显示框架阶段信息（如果有）
                if result.data and 'framework_stages' in result.data:
                    stage_count = len(result.data['framework_stages'])
                    print(f"   - 框架阶段: {stage_count}个")
                    if stage_count > 0:
                        print(f"   - 包含阶段: {', '.join(result.data['framework_stages'])}")
                
                # 显示内容预览
                print(f"\n📄 System Prompt预览:")
                print("-" * 50)
                preview = system_prompt[:300] if system_prompt else ""
                print(f"{preview}{'...' if len(system_prompt) > 300 else ''}")
                print("-" * 50)
            
            # 保存system prompt到output/system_prompts目录
            try:
                saved_file_path = self._save_system_prompt(
                    system_prompt=system_prompt,
                    team_name=team_name,
                    mode=mode,
                    user_message=user_message
                )
                if verbose:
                    print(f"💾 System Prompt已保存到: {saved_file_path}")
            except Exception as save_error:
                if verbose:
                    print(f"⚠️  保存失败: {save_error}")
                saved_file_path = None
            
            # 构建返回结果
            generation_result = {
                "success": True,
                "system_prompt": system_prompt,
                "system_prompt_length": len(system_prompt),
                "team_name": team_name,
                "mode": mode,
                "user_message": user_message,
                "user_message_length": len(user_message),
                "generation_metadata": {
                    "stages": stages or "all",
                    "memory_types": memory_types,
                    "project_scope": project_scope,
                    "memory_importance": memory_importance,
                    "max_memory_items": max_memory_items,
                    "tags_filter": tags_filter,
                    "learning_enabled": self._learning_enabled
                },
                "saved_to": saved_file_path  # 添加保存路径信息
            }
            
            # 添加详细的生成数据（如果有）
            if result.data:
                generation_result["context_data"] = result.data
            
            # 保留原有的保存结果信息（如果有）
            if save_results and result.data and 'saved_to' in result.data:
                generation_result["context_saved_to"] = result.data['saved_to']
                if verbose:
                    print(f"💾 上下文结果已保存到: {result.data['saved_to']}")
            
            # 🎓 记录生成会话（用于学习）
            self._record_generation_session(team_name, user_message, generation_result, matched_memories)
            
            # 🧠 轻量级学习触发（如果启用）
            if self._learning_enabled and matched_memories:
                self._perform_lightweight_learning(team_name, user_message, matched_memories, verbose)
            
            # 恢复原始学习设置
            self._learning_enabled = original_learning_enabled
            
            return generation_result
            
        except Exception as e:
            # 恢复原始学习设置
            if enable_learning is not None:
                self._learning_enabled = original_learning_enabled
                
            if verbose:
                print(f"❌ System Prompt生成失败: {e}")
                import traceback
                traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "team_name": team_name,
                "mode": mode,
                "user_message": user_message
            }
    
    def _perform_lightweight_learning(self, team_name: str, user_message: str, 
                                     matched_memories: list, verbose: bool = False):
        """
        执行轻量级学习（不立即更新权重，仅记录统计）
        
        Args:
            team_name: 团队名称
            user_message: 用户消息
            matched_memories: 匹配的记忆ID列表
            verbose: 是否显示详细信息
        """
        try:
            scoring_engine_info = self._get_scoring_engine(team_name)
            if not scoring_engine_info:
                return
            
            scoring_engine = scoring_engine_info['engine']
            
            # 模拟记忆项目（用于统计更新）
            from src.scoring_self_evolution import MemoryItem
            
            # 创建虚拟记忆项目用于统计更新
            mock_memories = []
            for i, memory_id in enumerate(matched_memories[:5]):  # 限制最多5个
                mock_memory = MemoryItem(
                    id=memory_id,
                    title=f"System Prompt Matched Memory {i+1}",
                    content=f"Memory matched for: {user_message[:100]}",
                    tags=["system_prompt", "matched"],
                    project="system_prompt_generation",
                    importance=3
                )
                mock_memories.append(mock_memory)
            
            if mock_memories:
                # 执行轻量级评分（主要为了统计更新）
                results = scoring_engine.score_memory_items(user_message, mock_memories)
                
                # 保存更新后的矩阵（包含统计信息）
                matrix_file = scoring_engine_info['matrix_file']
                scoring_engine.save_matrix(str(matrix_file))
                
                if verbose:
                    print(f"🎓 轻量级学习完成 - 更新了{len(matched_memories)}个记忆的统计信息")
                    
        except Exception as e:
            if verbose:
                print(f"⚠️ 轻量级学习失败: {e}")
    
    def provide_usage_feedback(self, team_name: str, user_message: str, 
                              system_prompt_effectiveness: int,
                              matched_memories: list = None,
                              comment: str = "") -> Dict[str, Any]:
        """
        提供System Prompt使用效果反馈，触发深度学习
        
        Args:
            team_name: 团队名称
            user_message: 原始用户消息
            system_prompt_effectiveness: 效果评分 (1-5)
            matched_memories: 匹配的记忆ID列表
            comment: 反馈评论
            
        Returns:
            反馈处理结果
        """
        if not self._learning_enabled:
            return {
                "success": False,
                "message": "学习机制未启用"
            }
            
        try:
            scoring_engine_info = self._get_scoring_engine(team_name)
            if not scoring_engine_info:
                return {
                    "success": False,
                    "message": "评分引擎不可用"
                }
            
            scoring_engine = scoring_engine_info['engine']
            
            # 为每个匹配的记忆添加反馈
            feedback_count = 0
            if matched_memories:
                for memory_id in matched_memories:
                    scoring_engine.add_user_feedback(
                        memory_id=memory_id,
                        query=user_message,
                        rating=system_prompt_effectiveness,
                        matched_keywords=[],  # 这里可以从之前的评分结果中获取
                        comment=f"System Prompt feedback: {comment}"
                    )
                    feedback_count += 1
            
            # 保存学习结果
            matrix_file = scoring_engine_info['matrix_file']
            scoring_engine.save_matrix(str(matrix_file))
            
            return {
                "success": True,
                "message": f"反馈已记录，更新了{feedback_count}个记忆的学习数据",
                "feedback_count": feedback_count,
                "effectiveness_rating": system_prompt_effectiveness
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"反馈处理失败: {e}"
            }
    
    def get_learning_statistics(self, team_name: str) -> Dict[str, Any]:
        """获取团队的学习统计信息"""
        if not self._learning_enabled:
            return {"learning_enabled": False}
            
        try:
            scoring_engine_info = self._get_scoring_engine(team_name)
            if not scoring_engine_info:
                return {"error": "评分引擎不可用"}
            
            scoring_engine = scoring_engine_info['engine']
            stats = scoring_engine.get_learning_statistics()
            
            # 添加生成会话统计
            team_sessions = [s for s in self._generation_sessions if s['team_name'] == team_name]
            stats['generation_sessions'] = {
                'total_sessions': len(team_sessions),
                'successful_sessions': sum(1 for s in team_sessions if s['success']),
                'avg_prompt_length': sum(s['system_prompt_length'] for s in team_sessions) / len(team_sessions) if team_sessions else 0,
                'recent_sessions': len([s for s in team_sessions if (datetime.now() - datetime.fromisoformat(s['timestamp'])).days <= 7])
            }
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_generator_info(self) -> Dict[str, Any]:
        """获取生成器信息"""
        available_teams = self.get_available_teams()
        
        return {
            "team_data_root": self.team_data_root,
            "available_teams": available_teams,
            "team_count": len(available_teams),
            "supported_modes": ["hybrid", "framework_only", "memory_only"],
            "supported_memory_types": ["declarative", "procedural", "episodic", "all"],
            "default_config": {
                "mode": "hybrid",
                "memory_importance": 2,
                "max_memory_items": 50,
                "memory_types": "all",
                "stages": "all"
            }
        }


def create_system_prompt_generator(team_data_root: str = "test_data") -> SystemPromptGenerator:
    """
    创建System Prompt生成器实例
    
    Args:
        team_data_root: 团队数据根目录
    
    Returns:
        SystemPromptGenerator实例
    """
    return SystemPromptGenerator(team_data_root) 