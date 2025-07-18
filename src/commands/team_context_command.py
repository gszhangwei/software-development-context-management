"""
PromptX团队上下文生成命令

负责触发和管理团队上下文的生成，支持：
- 七阶段框架的完整执行
- 单阶段或多阶段的选择性生成
- 不同输出格式和配置选项
- 记忆系统的深度集成
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .base_command import BaseCommand, CommandResult, TeamCommandMixin
from ..core.context_processor import ContextProcessor, ContextType, ContextGenerationConfig
from ..core.seven_stage_engine import SevenStageEngine, SevenStageConfig


class TeamContextCommand(BaseCommand, TeamCommandMixin):
    """团队上下文生成命令"""
    
    @property
    def name(self) -> str:
        return "team_context"
    
    @property
    def description(self) -> str:
        return "生成基于七阶段框架的结构化团队上下文"
    
    def execute(self, team_name: str, action: str = "generate", 
                stages: str = None, output_format: str = "markdown",
                memory_integration: bool = True, stage_dependencies: bool = True,
                save_results: bool = True, project_scope: str = None,
                memory_importance: int = 2, **kwargs) -> CommandResult:
        """
        执行团队上下文生成命令
        
        Args:
            team_name: 团队名称
            action: 操作类型 ('generate', 'list_stages', 'show_dependencies', 'export')
            stages: 要生成的阶段列表，逗号分隔，如'requirements,solution'，或'all'
            output_format: 输出格式 ('markdown', 'json', 'combined')
            memory_integration: 是否集成记忆系统
            stage_dependencies: 是否考虑阶段依赖关系
            save_results: 是否保存生成结果
            project_scope: 项目范围过滤器
            memory_importance: 记忆重要性阈值
            **kwargs: 其他参数
        
        Returns:
            命令执行结果
        """
        try:
            # 验证团队存在
            if not self.validate_team_exists(team_name):
                return CommandResult(
                    success=False,
                    message=f"Team '{team_name}' does not exist",
                    error="TEAM_NOT_FOUND"
                )
            
            # 根据action分发处理
            if action == "generate":
                return self._generate_context(
                    team_name, stages, output_format, memory_integration,
                    stage_dependencies, save_results, project_scope, memory_importance, **kwargs
                )
            elif action == "list_stages":
                return self._list_available_stages()
            elif action == "show_dependencies":
                return self._show_stage_dependencies()
            elif action == "export":
                return self._export_existing_results(team_name, **kwargs)
            else:
                return CommandResult(
                    success=False,
                    message=f"Unknown action: {action}",
                    error="INVALID_ACTION"
                )
                
        except Exception as e:
            self.logger.error(f"Error in team_context command: {str(e)}")
            return CommandResult(
                success=False,
                message=f"Command execution failed: {str(e)}",
                error=str(e)
            )
    
    def _generate_context(self, team_name: str, stages: str, output_format: str,
                         memory_integration: bool, stage_dependencies: bool,
                         save_results: bool, project_scope: str, memory_importance: int,
                         **kwargs) -> CommandResult:
        """生成团队上下文"""
        # 解析要生成的阶段
        target_stages = self._parse_stages(stages)
        
        if not target_stages:
            return CommandResult(
                success=False,
                message="No valid stages specified",
                error="INVALID_STAGES"
            )
        
        # 创建配置
        config = SevenStageConfig(
            team_name=team_name,
            target_stages=target_stages,
            execute_all_stages=(stages == "all"),
            memory_integration=memory_integration,
            stage_dependencies=stage_dependencies,
            output_format=output_format,
            save_intermediate=save_results,
            memory_filters={
                'importance_threshold': memory_importance,
                'project_scope': project_scope
            } if project_scope else {}
        )
        
        # 执行七阶段生成
        engine = SevenStageEngine(self.base_path)
        result = engine.execute_seven_stages(config)
        
        if result['success']:
            return CommandResult(
                success=True,
                message=f"Successfully generated context for {len(target_stages)} stages",
                data={
                    'execution_summary': result['execution_summary'],
                    'completed_stages': result['execution_summary']['completed_stage_names'],
                    'failed_stages': result['execution_summary']['failed_stage_names'],
                    'total_time': result['execution_summary']['execution_time'],
                    'success_rate': result['execution_summary']['success_rate'],
                    'memory_sources': result['execution_summary']['total_memory_sources']
                }
            )
        else:
            return CommandResult(
                success=False,
                message=f"Context generation failed: {result.get('error', 'Unknown error')}",
                error=result.get('error'),
                data=result.get('partial_results')
            )
    
    def _parse_stages(self, stages: str) -> List[ContextType]:
        """解析阶段参数"""
        if not stages or stages.lower() == "all":
            return list(ContextType)
        
        stage_names = [name.strip().lower() for name in stages.split(',')]
        target_stages = []
        
        # 阶段名称映射
        stage_mapping = {
            'requirements': ContextType.REQUIREMENTS,
            'req': ContextType.REQUIREMENTS,
            'business': ContextType.BUSINESS_MODEL,
            'business-model': ContextType.BUSINESS_MODEL,
            'biz': ContextType.BUSINESS_MODEL,
            'solution': ContextType.SOLUTION,
            'sol': ContextType.SOLUTION,
            'structure': ContextType.STRUCTURE,
            'arch': ContextType.STRUCTURE,
            'architecture': ContextType.STRUCTURE,
            'tasks': ContextType.TASKS,
            'task': ContextType.TASKS,
            'common-tasks': ContextType.COMMON_TASKS,
            'common': ContextType.COMMON_TASKS,
            'constraints': ContextType.CONSTRAINTS,
            'constraint': ContextType.CONSTRAINTS,
            'limit': ContextType.CONSTRAINTS
        }
        
        for stage_name in stage_names:
            if stage_name in stage_mapping:
                target_stages.append(stage_mapping[stage_name])
            else:
                # 尝试直接匹配枚举值
                try:
                    stage_type = ContextType(stage_name.replace('_', '-'))
                    target_stages.append(stage_type)
                except ValueError:
                    self.logger.warning(f"Unknown stage name: {stage_name}")
        
        return list(set(target_stages))  # 去重
    
    def _list_available_stages(self) -> CommandResult:
        """列出可用的阶段"""
        stages_info = []
        
        for stage in ContextType:
            stage_info = {
                'name': stage.value,
                'display_name': stage.value.replace('-', ' ').title(),
                'aliases': self._get_stage_aliases(stage),
                'description': self._get_stage_description(stage)
            }
            stages_info.append(stage_info)
        
        return CommandResult(
            success=True,
            message=f"Available stages: {len(stages_info)}",
            data={
                'stages': stages_info,
                'total_count': len(stages_info),
                'usage_examples': [
                    "team_context generate frontend-team --stages=requirements,solution",
                    "team_context generate backend-team --stages=all",
                    "team_context generate data-team --stages=req,biz,arch"
                ]
            }
        )
    
    def _get_stage_aliases(self, stage: ContextType) -> List[str]:
        """获取阶段的别名"""
        aliases_map = {
            ContextType.REQUIREMENTS: ['req', 'requirements'],
            ContextType.BUSINESS_MODEL: ['business', 'biz', 'business-model'],
            ContextType.SOLUTION: ['solution', 'sol'],
            ContextType.STRUCTURE: ['structure', 'arch', 'architecture'],
            ContextType.TASKS: ['tasks', 'task'],
            ContextType.COMMON_TASKS: ['common-tasks', 'common'],
            ContextType.CONSTRAINTS: ['constraints', 'constraint', 'limit']
        }
        return aliases_map.get(stage, [stage.value])
    
    def _get_stage_description(self, stage: ContextType) -> str:
        """获取阶段描述"""
        descriptions = {
            ContextType.REQUIREMENTS: "需求分析和功能规格定义",
            ContextType.BUSINESS_MODEL: "商业模式和价值主张设计",
            ContextType.SOLUTION: "解决方案设计和技术选型",
            ContextType.STRUCTURE: "系统架构和组件设计",
            ContextType.TASKS: "任务分解和执行计划",
            ContextType.COMMON_TASKS: "通用任务模式和最佳实践",
            ContextType.CONSTRAINTS: "约束条件和限制因素"
        }
        return descriptions.get(stage, "No description available")
    
    def _show_stage_dependencies(self) -> CommandResult:
        """显示阶段依赖关系"""
        dependencies_info = []
        
        # 从七阶段引擎获取依赖关系
        engine = SevenStageEngine(self.base_path)
        
        for stage in engine.EXECUTION_ORDER:
            dependencies = engine.STAGE_DEPENDENCIES.get(stage, [])
            dependency_info = {
                'stage': stage.value,
                'display_name': stage.value.replace('-', ' ').title(),
                'dependencies': [dep.value for dep in dependencies],
                'dependency_count': len(dependencies),
                'execution_order': engine.EXECUTION_ORDER.index(stage) + 1
            }
            dependencies_info.append(dependency_info)
        
        return CommandResult(
            success=True,
            message="Stage dependencies information",
            data={
                'dependencies': dependencies_info,
                'execution_order': [stage.value for stage in engine.EXECUTION_ORDER],
                'notes': [
                    "Dependencies are checked when stage_dependencies=true",
                    "Stages with unmet dependencies will be skipped",
                    "Constraints stage is independent and can run anytime"
                ]
            }
        )
    
    def _export_existing_results(self, team_name: str, **kwargs) -> CommandResult:
        """导出现有的生成结果"""
        team_path = self.get_team_path(team_name)
        output_dir = team_path / "seven_stage_outputs"
        
        if not output_dir.exists():
            return CommandResult(
                success=False,
                message="No existing results found for this team",
                error="NO_RESULTS"
            )
        
        # 扫描现有结果文件
        result_files = []
        
        # 扫描Markdown文件
        for md_file in output_dir.glob("*.md"):
            if md_file.name.endswith("_comprehensive_report.md"):
                continue  # 跳过综合报告，单独处理
            
            file_info = {
                'filename': md_file.name,
                'path': str(md_file),
                'size': md_file.stat().st_size,
                'modified': datetime.fromtimestamp(md_file.stat().st_mtime).isoformat(),
                'type': 'stage_result'
            }
            result_files.append(file_info)
        
        # 扫描JSON摘要文件
        for json_file in output_dir.glob("*_execution_summary.json"):
            file_info = {
                'filename': json_file.name,
                'path': str(json_file),
                'size': json_file.stat().st_size,
                'modified': datetime.fromtimestamp(json_file.stat().st_mtime).isoformat(),
                'type': 'execution_summary'
            }
            result_files.append(file_info)
        
        # 扫描综合报告
        for report_file in output_dir.glob("*_comprehensive_report.md"):
            file_info = {
                'filename': report_file.name,
                'path': str(report_file),
                'size': report_file.stat().st_size,
                'modified': datetime.fromtimestamp(report_file.stat().st_mtime).isoformat(),
                'type': 'comprehensive_report'
            }
            result_files.append(file_info)
        
        # 按修改时间排序
        result_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return CommandResult(
            success=True,
            message=f"Found {len(result_files)} existing result files",
            data={
                'output_directory': str(output_dir),
                'files': result_files,
                'file_types': {
                    'stage_results': len([f for f in result_files if f['type'] == 'stage_result']),
                    'execution_summaries': len([f for f in result_files if f['type'] == 'execution_summary']),
                    'comprehensive_reports': len([f for f in result_files if f['type'] == 'comprehensive_report'])
                },
                'latest_execution': result_files[0]['modified'] if result_files else None
            }
        )
    
    def get_help_text(self) -> str:
        """获取帮助文本"""
        return """
团队上下文生成命令 (team_context)

用法:
  team_context <action> <team_name> [options]

操作 (actions):
  generate          生成团队上下文
  list_stages       列出可用的阶段
  show_dependencies 显示阶段依赖关系
  export           导出现有结果

generate 选项:
  --stages=<stages>           要生成的阶段，逗号分隔或'all'
  --output-format=<format>    输出格式 (markdown/json/combined)
  --memory-integration=<bool> 是否集成记忆系统 (default: true)
  --stage-dependencies=<bool> 是否考虑依赖关系 (default: true)
  --save-results=<bool>       是否保存结果 (default: true)
  --project-scope=<project>   项目范围过滤器
  --memory-importance=<int>   记忆重要性阈值 (1-5, default: 2)

示例:
  team_context generate frontend-team --stages=all
  team_context generate backend-team --stages=requirements,solution
  team_context list_stages
  team_context show_dependencies
  team_context export data-team

阶段类型:
  requirements     需求分析 (aliases: req)
  business-model   商业模式 (aliases: business, biz)
  solution         解决方案 (aliases: sol)
  structure        系统架构 (aliases: arch, architecture)
  tasks            任务编排 (aliases: task)
  common-tasks     通用任务 (aliases: common)
  constraints      约束条件 (aliases: constraint, limit)
        """.strip() 