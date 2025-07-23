"""
ContextX七阶段框架集成引擎

基于pdd-prompt/core的七阶段框架，结合团队记忆系统，实现：
- 需求分析、业务模型、解决方案、架构设计、任务编排、通用任务、约束条件的完整生成
- 阶段间的依赖关系和数据传递
- 记忆系统的深度集成
- 自适应的上下文生成
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .context_processor import ContextProcessor, ContextGenerationConfig, GeneratedContext, MemoryType
from .markdown_engine import MarkdownEngine, MemoryEntry


class StageStatus(Enum):
    """阶段状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """阶段执行结果"""
    stage: ContextType
    status: StageStatus
    content: str
    dependencies_met: bool = True
    processing_time: float = 0.0
    memory_sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'stage': self.stage.value,
            'status': self.status.value,
            'content': self.content,
            'dependencies_met': self.dependencies_met,
            'processing_time': self.processing_time,
            'memory_sources': self.memory_sources,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


@dataclass
class SevenStageConfig:
    """七阶段执行配置"""
    team_name: str
    target_stages: List[ContextType] = field(default_factory=list)
    execute_all_stages: bool = False
    memory_integration: bool = True
    stage_dependencies: bool = True
    output_format: str = "markdown"  # markdown, json, combined
    save_intermediate: bool = True
    memory_filters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.execute_all_stages:
            self.target_stages = list(ContextType)


class SevenStageEngine:
    """七阶段框架集成引擎"""
    
    # 阶段依赖关系图
    STAGE_DEPENDENCIES = {
        ContextType.REQUIREMENTS: [],
        ContextType.BUSINESS_MODEL: [ContextType.REQUIREMENTS],
        ContextType.SOLUTION: [ContextType.REQUIREMENTS, ContextType.BUSINESS_MODEL],
        ContextType.STRUCTURE: [ContextType.SOLUTION],
        ContextType.TASKS: [ContextType.STRUCTURE],
        ContextType.COMMON_TASKS: [ContextType.TASKS],
        ContextType.CONSTRAINTS: [],  # 约束可以独立存在，但会影响其他阶段
    }
    
    # 阶段执行顺序
    EXECUTION_ORDER = [
        ContextType.REQUIREMENTS,
        ContextType.CONSTRAINTS,
        ContextType.BUSINESS_MODEL,
        ContextType.SOLUTION,
        ContextType.STRUCTURE,
        ContextType.TASKS,
        ContextType.COMMON_TASKS,
    ]
    
    def __init__(self, base_path: Path):
        """
        初始化七阶段引擎
        
        Args:
            base_path: 团队数据根目录
        """
        self.base_path = Path(base_path)
        self.context_processor = ContextProcessor(base_path)
        self.markdown_engine = MarkdownEngine()
        
        # 执行状态追踪
        self.stage_results: Dict[ContextType, StageResult] = {}
        self.execution_context: Dict[str, Any] = {}
    
    def execute_seven_stages(self, config: SevenStageConfig) -> Dict[str, Any]:
        """
        执行七阶段框架
        
        Args:
            config: 七阶段执行配置
        
        Returns:
            执行结果字典
        """
        start_time = datetime.now()
        
        try:
            # 初始化执行上下文
            self._initialize_execution_context(config)
            
            # 验证团队存在
            if not self.context_processor.directory_manager.team_exists(config.team_name):
                raise ValueError(f"Team '{config.team_name}' does not exist")
            
            # 执行阶段
            if config.stage_dependencies:
                results = self._execute_with_dependencies(config)
            else:
                results = self._execute_parallel(config)
            
            # 生成综合报告
            execution_summary = self._generate_execution_summary(config, results, start_time)
            
            # 保存结果
            if config.save_intermediate:
                self._save_execution_results(config, results, execution_summary)
            
            return {
                'success': True,
                'execution_summary': execution_summary,
                'stage_results': {stage.value: result.to_dict() for stage, result in results.items()},
                'config': config.__dict__
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'partial_results': {stage.value: result.to_dict() for stage, result in self.stage_results.items()},
                'config': config.__dict__
            }
    
    def _initialize_execution_context(self, config: SevenStageConfig):
        """初始化执行上下文"""
        self.execution_context = {
            'team_name': config.team_name,
            'start_time': datetime.now().isoformat(),
            'memory_integration': config.memory_integration,
            'stage_dependencies': config.stage_dependencies,
            'accumulated_context': {},
            'cross_stage_insights': []
        }
        self.stage_results.clear()
    
    def _execute_with_dependencies(self, config: SevenStageConfig) -> Dict[ContextType, StageResult]:
        """按依赖关系顺序执行阶段"""
        results = {}
        
        # 按执行顺序处理阶段
        for stage in self.EXECUTION_ORDER:
            if stage not in config.target_stages:
                continue
            
            start_time = datetime.now()
            
            try:
                # 检查依赖关系
                dependencies_met = self._check_dependencies(stage, results)
                
                if not dependencies_met and config.stage_dependencies:
                    result = StageResult(
                        stage=stage,
                        status=StageStatus.SKIPPED,
                        content=f"Dependencies not met for {stage.value}",
                        dependencies_met=False
                    )
                else:
                    # 执行阶段
                    result = self._execute_single_stage(stage, config, results)
                
                # 记录处理时间
                result.processing_time = (datetime.now() - start_time).total_seconds()
                
                results[stage] = result
                self.stage_results[stage] = result
                
                # 更新执行上下文
                self._update_execution_context(stage, result)
                
            except Exception as e:
                result = StageResult(
                    stage=stage,
                    status=StageStatus.FAILED,
                    content=f"Failed to execute stage {stage.value}: {str(e)}",
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
                results[stage] = result
                self.stage_results[stage] = result
        
        return results
    
    def _execute_parallel(self, config: SevenStageConfig) -> Dict[ContextType, StageResult]:
        """并行执行所有阶段（忽略依赖关系）"""
        results = {}
        
        for stage in config.target_stages:
            start_time = datetime.now()
            
            try:
                result = self._execute_single_stage(stage, config, {})
                result.processing_time = (datetime.now() - start_time).total_seconds()
                results[stage] = result
                self.stage_results[stage] = result
                
            except Exception as e:
                result = StageResult(
                    stage=stage,
                    status=StageStatus.FAILED,
                    content=f"Failed to execute stage {stage.value}: {str(e)}",
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
                results[stage] = result
                self.stage_results[stage] = result
        
        return results
    
    def _execute_single_stage(self, stage: ContextType, config: SevenStageConfig, 
                             previous_results: Dict[ContextType, StageResult]) -> StageResult:
        """执行单个阶段"""
        # 创建上下文生成配置
        context_config = ContextGenerationConfig(
            team_name=config.team_name,
            project_name=getattr(config, 'project_name', None),
            include_memory_types=[MemoryType.ALL],
            include_team_memories=config.memory_integration,
            memory_filters=getattr(config, 'memory_filters', {})
        )
        
        # 生成上下文
        generated_contexts = self.context_processor.generate_context(context_config)
        
        if not generated_contexts:
            return StageResult(
                stage=stage,
                status=StageStatus.FAILED,
                content=f"No context generated for {stage.value}"
            )
        
        generated_context = generated_contexts[0]
        
        # 应用七阶段特定的增强
        enhanced_content = self._apply_seven_stage_enhancement(
            stage, generated_context, previous_results, config
        )
        
        return StageResult(
            stage=stage,
            status=StageStatus.COMPLETED,
            content=enhanced_content,
            dependencies_met=True,
            memory_sources=generated_context.source_memories,
            metadata=generated_context.metadata
        )
    
    def _apply_seven_stage_enhancement(self, stage: ContextType, context: GeneratedContext,
                                     previous_results: Dict[ContextType, StageResult],
                                     config: SevenStageConfig) -> str:
        """应用七阶段特定的内容增强"""
        
        enhanced_sections = [
            f"# {stage.value.replace('-', ' ').title()} - Seven Stage Framework",
            "",
            f"**Team:** {context.team_name}",
            f"**Stage:** {stage.value}",
            f"**Generated:** {context.generation_time}",
            ""
        ]
        
        # 添加依赖关系信息
        if config.stage_dependencies and stage in self.STAGE_DEPENDENCIES:
            dependencies = self.STAGE_DEPENDENCIES[stage]
            if dependencies:
                enhanced_sections.extend([
                    "## Dependencies",
                    "",
                    *[f"- {dep.value}" for dep in dependencies],
                    ""
                ])
                
                # 添加依赖阶段的关键输出
                for dep in dependencies:
                    if dep in previous_results:
                        enhanced_sections.extend([
                            f"### Input from {dep.value.title()}",
                            "",
                            self._extract_key_insights(previous_results[dep]),
                            ""
                        ])
        
        # 添加阶段特定的框架指导
        framework_guidance = self._get_stage_framework_guidance(stage)
        if framework_guidance:
            enhanced_sections.extend([
                "## Framework Guidance",
                "",
                framework_guidance,
                ""
            ])
        
        # 添加原始上下文内容
        enhanced_sections.extend([
            "## Generated Context",
            "",
            context.content
        ])
        
        # 添加记忆来源信息
        if context.source_memories:
            enhanced_sections.extend([
                "",
                "## Memory Sources",
                "",
                *[f"- {memory_id}" for memory_id in context.source_memories]
            ])
        
        # 添加跨阶段洞察
        cross_insights = self._generate_cross_stage_insights(stage, previous_results)
        if cross_insights:
            enhanced_sections.extend([
                "",
                "## Cross-Stage Insights",
                "",
                cross_insights
            ])
        
        return "\n".join(enhanced_sections)
    
    def _check_dependencies(self, stage: ContextType, results: Dict[ContextType, StageResult]) -> bool:
        """检查阶段依赖关系是否满足"""
        dependencies = self.STAGE_DEPENDENCIES.get(stage, [])
        
        for dep in dependencies:
            if dep not in results or results[dep].status != StageStatus.COMPLETED:
                return False
        
        return True
    
    def _extract_key_insights(self, stage_result: StageResult) -> str:
        """从阶段结果中提取关键洞察"""
        content = stage_result.content
        
        # 简单的关键信息提取逻辑
        lines = content.split('\n')
        key_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('##') or line.startswith('**') or line.startswith('-'):
                key_lines.append(line)
                if len(key_lines) >= 5:  # 限制关键信息数量
                    break
        
        return '\n'.join(key_lines) if key_lines else "No key insights extracted."
    
    def _get_stage_framework_guidance(self, stage: ContextType) -> str:
        """获取阶段特定的框架指导"""
        guidance = {
            ContextType.REQUIREMENTS: """
### Requirements Analysis Framework
1. **Functional Requirements**: What the system must do
2. **Non-functional Requirements**: Quality attributes and constraints
3. **User Stories**: From user perspective
4. **Acceptance Criteria**: Definition of done
5. **Priority Assessment**: MoSCoW or similar method
            """,
            
            ContextType.BUSINESS_MODEL: """
### Business Model Canvas Framework
1. **Value Propositions**: What value we deliver
2. **Customer Segments**: Who we serve
3. **Revenue Streams**: How we make money
4. **Cost Structure**: What it costs to operate
5. **Key Partnerships**: Who helps us succeed
            """,
            
            ContextType.SOLUTION: """
### Solution Design Framework
1. **Problem-Solution Fit**: How solution addresses requirements
2. **Alternative Analysis**: Other approaches considered
3. **Technology Stack**: Tools and technologies chosen
4. **Integration Points**: How components connect
5. **Risk Assessment**: Potential issues and mitigation
            """,
            
            ContextType.STRUCTURE: """
### Architecture Design Framework
1. **System Architecture**: High-level structure
2. **Component Design**: Individual component details
3. **Data Architecture**: Data flow and storage
4. **Security Architecture**: Security considerations
5. **Scalability Design**: Growth and performance planning
            """,
            
            ContextType.TASKS: """
### Task Planning Framework
1. **Work Breakdown**: Decomposition of work
2. **Dependencies**: Task interdependencies
3. **Resource Allocation**: Who does what
4. **Timeline**: When tasks will be completed
5. **Risk Management**: Task-level risks and mitigation
            """,
            
            ContextType.COMMON_TASKS: """
### Common Tasks Framework
1. **Reusable Patterns**: Tasks that repeat across projects
2. **Standard Procedures**: Established workflows
3. **Best Practices**: Proven approaches
4. **Template Tasks**: Generic task templates
5. **Automation Opportunities**: Tasks that can be automated
            """,
            
            ContextType.CONSTRAINTS: """
### Constraints Framework
1. **Technical Constraints**: Technology limitations
2. **Business Constraints**: Business rules and policies
3. **Resource Constraints**: Time, budget, people limitations
4. **Regulatory Constraints**: Compliance requirements
5. **Integration Constraints**: External system limitations
            """
        }
        
        return guidance.get(stage, "").strip()
    
    def _generate_cross_stage_insights(self, current_stage: ContextType, 
                                     previous_results: Dict[ContextType, StageResult]) -> str:
        """生成跨阶段洞察"""
        if not previous_results:
            return ""
        
        insights = []
        
        # 分析与其他阶段的关联
        for stage, result in previous_results.items():
            if result.status == StageStatus.COMPLETED:
                # 简单的关联分析
                if current_stage == ContextType.SOLUTION and stage == ContextType.REQUIREMENTS:
                    insights.append("- Solution should directly address identified requirements")
                elif current_stage == ContextType.STRUCTURE and stage == ContextType.SOLUTION:
                    insights.append("- Architecture should support the chosen solution approach")
                elif current_stage == ContextType.TASKS and stage == ContextType.STRUCTURE:
                    insights.append("- Tasks should implement the designed architecture components")
        
        return '\n'.join(insights) if insights else ""
    
    def _update_execution_context(self, stage: ContextType, result: StageResult):
        """更新执行上下文"""
        self.execution_context['accumulated_context'][stage.value] = {
            'status': result.status.value,
            'memory_sources': result.memory_sources,
            'processing_time': result.processing_time
        }
        
        # 记录跨阶段洞察
        if result.status == StageStatus.COMPLETED:
            self.execution_context['cross_stage_insights'].append({
                'stage': stage.value,
                'timestamp': result.timestamp,
                'memory_count': len(result.memory_sources)
            })
    
    def _generate_execution_summary(self, config: SevenStageConfig, 
                                  results: Dict[ContextType, StageResult],
                                  start_time: datetime) -> Dict[str, Any]:
        """生成执行总结"""
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        completed_stages = [stage for stage, result in results.items() if result.status == StageStatus.COMPLETED]
        failed_stages = [stage for stage, result in results.items() if result.status == StageStatus.FAILED]
        skipped_stages = [stage for stage, result in results.items() if result.status == StageStatus.SKIPPED]
        
        return {
            'execution_time': total_time,
            'total_stages': len(results),
            'completed_stages': len(completed_stages),
            'failed_stages': len(failed_stages),
            'skipped_stages': len(skipped_stages),
            'success_rate': len(completed_stages) / len(results) if results else 0,
            'completed_stage_names': [stage.value for stage in completed_stages],
            'failed_stage_names': [stage.value for stage in failed_stages],
            'skipped_stage_names': [stage.value for stage in skipped_stages],
            'total_memory_sources': sum(len(result.memory_sources) for result in results.values()),
            'average_processing_time': sum(result.processing_time for result in results.values()) / len(results) if results else 0
        }
    
    def _save_execution_results(self, config: SevenStageConfig, 
                              results: Dict[ContextType, StageResult],
                              summary: Dict[str, Any]):
        """保存执行结果"""
        team_path = self.context_processor.directory_manager.get_team_path(config.team_name)
        output_dir = team_path / "seven_stage_outputs"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存各阶段结果
        for stage, result in results.items():
            if result.status == StageStatus.COMPLETED:
                stage_file = output_dir / f"{timestamp}_{stage.value}.md"
                stage_file.write_text(result.content, encoding='utf-8')
        
        # 保存执行总结
        summary_file = output_dir / f"{timestamp}_execution_summary.json"
        # 转换config为可序列化的格式
        config_dict = config.__dict__.copy()
        config_dict['target_stages'] = [stage.value for stage in config.target_stages]
        
        summary_data = {
            'config': config_dict,
            'summary': summary,
            'results': {stage.value: result.to_dict() for stage, result in results.items()}
        }
        summary_file.write_text(json.dumps(summary_data, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # 保存综合报告
        if config.output_format in ['markdown', 'combined']:
            self._save_comprehensive_report(config, results, summary, output_dir, timestamp)
    
    def _save_comprehensive_report(self, config: SevenStageConfig,
                                 results: Dict[ContextType, StageResult],
                                 summary: Dict[str, Any],
                                 output_dir: Path, timestamp: str):
        """保存综合报告"""
        report_sections = [
            f"# Seven Stage Framework - Comprehensive Report",
            f"",
            f"**Team:** {config.team_name}",
            f"**Generated:** {timestamp}",
            f"**Total Execution Time:** {summary['execution_time']:.2f} seconds",
            f"**Success Rate:** {summary['success_rate']:.1%}",
            "",
            "## Executive Summary",
            "",
            f"- **Completed Stages:** {summary['completed_stages']}/{summary['total_stages']}",
            f"- **Total Memory Sources:** {summary['total_memory_sources']}",
            f"- **Average Processing Time:** {summary['average_processing_time']:.2f} seconds",
            ""
        ]
        
        # 添加各阶段内容
        for stage in self.EXECUTION_ORDER:
            if stage in results:
                result = results[stage]
                report_sections.extend([
                    f"## {stage.value.replace('-', ' ').title()} ({result.status.value})",
                    "",
                    result.content,
                    "",
                    "---",
                    ""
                ])
        
        # 添加元数据
        report_sections.extend([
            "## Execution Metadata",
            "",
            f"```json",
            json.dumps(summary, indent=2, ensure_ascii=False),
            "```"
        ])
        
        report_file = output_dir / f"{timestamp}_comprehensive_report.md"
        report_file.write_text('\n'.join(report_sections), encoding='utf-8') 