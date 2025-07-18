"""
ContextX高级报告引擎

提供数据分析和可视化功能，包括：
- 团队绩效分析
- 记忆使用统计
- 协作效率报告
- 趋势分析和预测
- 多种图表和可视化
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import statistics

from .directory_manager import DirectoryManager
from .markdown_engine import MarkdownEngine, MemoryEntry
from .advanced_search import AdvancedSearchEngine
from .collaboration_manager import CollaborationManager


@dataclass
class ReportConfig:
    """报告配置"""
    report_type: str = "summary"  # summary, detailed, analytics, visualization
    date_range: Optional[Tuple[str, str]] = None
    teams: Optional[List[str]] = None
    include_charts: bool = True
    include_statistics: bool = True
    include_recommendations: bool = True
    output_format: str = "html"  # html, markdown, json, pdf


@dataclass
class AnalyticsData:
    """分析数据"""
    metric_name: str
    value: Union[int, float, str]
    description: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'metric_name': self.metric_name,
            'value': self.value,
            'description': self.description,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class ReportingEngine:
    """高级报告引擎"""
    
    def __init__(self, base_path: Path):
        """
        初始化报告引擎
        
        Args:
            base_path: 基础路径
        """
        self.base_path = Path(base_path)
        self.directory_manager = DirectoryManager(base_path)
        self.markdown_engine = MarkdownEngine()
        self.search_engine = AdvancedSearchEngine(base_path)
        self.collaboration_manager = CollaborationManager(base_path)
        
        # 报告目录
        self.reports_dir = self.base_path / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # 图表模板
        self.chart_templates = self._load_chart_templates()
    
    def generate_team_performance_report(self, team_name: str, 
                                       config: ReportConfig) -> Dict[str, Any]:
        """
        生成团队绩效报告
        
        Args:
            team_name: 团队名称
            config: 报告配置
            
        Returns:
            报告数据
        """
        if not self.directory_manager.team_exists(team_name):
            raise ValueError(f"Team '{team_name}' does not exist")
        
        # 收集基础数据
        team_data = self._collect_team_data(team_name, config.date_range)
        
        # 计算性能指标
        performance_metrics = self._calculate_performance_metrics(team_data)
        
        # 生成分析
        analysis = self._analyze_team_performance(performance_metrics)
        
        # 生成建议
        recommendations = self._generate_performance_recommendations(analysis) if config.include_recommendations else []
        
        # 创建图表
        charts = self._create_performance_charts(performance_metrics) if config.include_charts else []
        
        report = {
            'report_type': 'team_performance',
            'team_name': team_name,
            'generated_at': datetime.now().isoformat(),
            'date_range': config.date_range,
            'metrics': performance_metrics,
            'analysis': analysis,
            'recommendations': recommendations,
            'charts': charts,
            'summary': f"Performance report for {team_name} with {len(performance_metrics)} metrics"
        }
        
        # 保存报告
        if config.output_format in ['html', 'markdown']:
            self._save_report(report, team_name, config)
        
        return report
    
    def generate_memory_analytics_report(self, team_name: str,
                                       config: ReportConfig) -> Dict[str, Any]:
        """
        生成记忆分析报告
        
        Args:
            team_name: 团队名称
            config: 报告配置
            
        Returns:
            报告数据
        """
        # 收集记忆数据
        memories = self._load_team_memories(team_name)
        
        # 应用日期过滤
        if config.date_range:
            memories = self._filter_memories_by_date(memories, config.date_range)
        
        # 计算记忆统计
        memory_stats = self._calculate_memory_statistics(memories)
        
        # 分析记忆模式
        patterns = self._analyze_memory_patterns(memories)
        
        # 创建图表
        charts = self._create_memory_charts(memory_stats, patterns) if config.include_charts else []
        
        # 生成洞察
        insights = self._generate_memory_insights(memory_stats, patterns)
        
        report = {
            'report_type': 'memory_analytics',
            'team_name': team_name,
            'generated_at': datetime.now().isoformat(),
            'date_range': config.date_range,
            'statistics': memory_stats,
            'patterns': patterns,
            'insights': insights,
            'charts': charts,
            'total_memories': len(memories)
        }
        
        return report
    
    def generate_collaboration_report(self, config: ReportConfig) -> Dict[str, Any]:
        """
        生成协作分析报告
        
        Args:
            config: 报告配置
            
        Returns:
            报告数据
        """
        # 获取协作分析数据
        collaboration_analytics = self.collaboration_manager.get_collaboration_analytics()
        
        # 收集所有团队的协作数据
        team_collaboration_data = {}
        
        teams_dir = self.base_path / "teams"
        if teams_dir.exists():
            for team_dir in teams_dir.iterdir():
                if team_dir.is_dir():
                    team_name = team_dir.name
                    if config.teams is None or team_name in config.teams:
                        team_data = self.collaboration_manager.get_collaboration_analytics(team_name)
                        team_collaboration_data[team_name] = team_data
        
        # 分析协作效率
        collaboration_efficiency = self._analyze_collaboration_efficiency(team_collaboration_data)
        
        # 识别协作瓶颈
        bottlenecks = self._identify_collaboration_bottlenecks(team_collaboration_data)
        
        # 创建网络图
        network_data = self._create_collaboration_network(collaboration_analytics['team_collaboration_matrix'])
        
        # 生成建议
        recommendations = self._generate_collaboration_recommendations(
            collaboration_efficiency, bottlenecks
        ) if config.include_recommendations else []
        
        report = {
            'report_type': 'collaboration_analytics',
            'generated_at': datetime.now().isoformat(),
            'date_range': config.date_range,
            'overall_analytics': collaboration_analytics,
            'team_analytics': team_collaboration_data,
            'efficiency_analysis': collaboration_efficiency,
            'bottlenecks': bottlenecks,
            'network_data': network_data,
            'recommendations': recommendations
        }
        
        return report
    
    def generate_system_overview_report(self, config: ReportConfig) -> Dict[str, Any]:
        """
        生成系统概览报告
        
        Args:
            config: 报告配置
            
        Returns:
            报告数据
        """
        # 收集系统级数据
        system_stats = self._collect_system_statistics()
        
        # 分析系统健康度
        health_analysis = self._analyze_system_health(system_stats)
        
        # 使用趋势分析
        usage_trends = self._analyze_usage_trends(config.date_range)
        
        # 资源利用率分析
        resource_utilization = self._analyze_resource_utilization()
        
        # 预测分析
        predictions = self._generate_system_predictions(usage_trends) if config.include_statistics else []
        
        # 创建仪表板数据
        dashboard_data = self._create_dashboard_data(system_stats, health_analysis, usage_trends)
        
        report = {
            'report_type': 'system_overview',
            'generated_at': datetime.now().isoformat(),
            'date_range': config.date_range,
            'system_statistics': system_stats,
            'health_analysis': health_analysis,
            'usage_trends': usage_trends,
            'resource_utilization': resource_utilization,
            'predictions': predictions,
            'dashboard_data': dashboard_data
        }
        
        return report
    
    def create_custom_report(self, report_definition: Dict[str, Any],
                           config: ReportConfig) -> Dict[str, Any]:
        """
        创建自定义报告
        
        Args:
            report_definition: 报告定义
            config: 报告配置
            
        Returns:
            报告数据
        """
        report = {
            'report_type': 'custom',
            'definition': report_definition,
            'generated_at': datetime.now().isoformat(),
            'sections': []
        }
        
        # 处理报告的各个部分
        for section in report_definition.get('sections', []):
            section_data = self._process_custom_section(section, config)
            report['sections'].append(section_data)
        
        return report
    
    def export_report_to_html(self, report_data: Dict[str, Any], 
                             output_path: Path) -> Path:
        """
        导出报告为HTML格式
        
        Args:
            report_data: 报告数据
            output_path: 输出路径
            
        Returns:
            生成的HTML文件路径
        """
        html_content = self._generate_html_report(report_data)
        output_path.write_text(html_content, encoding='utf-8')
        return output_path
    
    def _collect_team_data(self, team_name: str, date_range: Optional[Tuple[str, str]]) -> Dict[str, Any]:
        """收集团队数据"""
        team_path = self.directory_manager.get_team_path(team_name)
        
        # 加载记忆
        memories = self._load_team_memories(team_name)
        
        # 应用日期过滤
        if date_range:
            memories = self._filter_memories_by_date(memories, date_range)
        
        # 加载上下文文件
        contexts = {}
        context_dir = team_path / "context"
        if context_dir.exists():
            for context_file in context_dir.glob("*.md"):
                contexts[context_file.stem] = {
                    'content': context_file.read_text(encoding='utf-8'),
                    'size': context_file.stat().st_size,
                    'modified': datetime.fromtimestamp(context_file.stat().st_mtime).isoformat()
                }
        
        # 收集协作数据
        collaboration_data = {
            'shared_from': len(self.collaboration_manager.list_team_permissions(team_name, as_source=True)),
            'shared_to': len(self.collaboration_manager.list_team_permissions(team_name, as_source=False)),
            'shared_resources': len(self.collaboration_manager.get_shared_resources(team_name))
        }
        
        return {
            'memories': memories,
            'contexts': contexts,
            'collaboration': collaboration_data
        }
    
    def _calculate_performance_metrics(self, team_data: Dict[str, Any]) -> Dict[str, AnalyticsData]:
        """计算性能指标"""
        memories = team_data['memories']
        contexts = team_data['contexts']
        collaboration = team_data['collaboration']
        
        metrics = {}
        
        # 记忆相关指标
        metrics['total_memories'] = AnalyticsData(
            metric_name='total_memories',
            value=len(memories),
            description='Total number of memories'
        )
        
        if memories:
            avg_importance = statistics.mean([m.importance for m in memories])
            metrics['avg_importance'] = AnalyticsData(
                metric_name='avg_importance',
                value=round(avg_importance, 2),
                description='Average memory importance score'
            )
            
            # 标签多样性
            all_tags = []
            for memory in memories:
                all_tags.extend(memory.tags)
            
            unique_tags = len(set(all_tags))
            metrics['tag_diversity'] = AnalyticsData(
                metric_name='tag_diversity',
                value=unique_tags,
                description='Number of unique tags used'
            )
            
            # 项目覆盖
            projects = set(m.project for m in memories)
            metrics['project_coverage'] = AnalyticsData(
                metric_name='project_coverage',
                value=len(projects),
                description='Number of different projects'
            )
        
        # 上下文相关指标
        metrics['context_files'] = AnalyticsData(
            metric_name='context_files',
            value=len(contexts),
            description='Number of context files'
        )
        
        if contexts:
            total_context_size = sum(ctx['size'] for ctx in contexts.values())
            metrics['total_context_size'] = AnalyticsData(
                metric_name='total_context_size',
                value=total_context_size,
                description='Total size of context files (bytes)'
            )
        
        # 协作相关指标
        metrics['collaboration_score'] = AnalyticsData(
            metric_name='collaboration_score',
            value=collaboration['shared_from'] + collaboration['shared_to'],
            description='Total collaboration activities'
        )
        
        return metrics
    
    def _analyze_team_performance(self, metrics: Dict[str, AnalyticsData]) -> Dict[str, Any]:
        """分析团队性能"""
        analysis = {
            'overall_score': 0,
            'strengths': [],
            'weaknesses': [],
            'trends': {}
        }
        
        # 计算总体得分
        score_components = []
        
        # 记忆质量得分
        if 'avg_importance' in metrics:
            importance_score = min(metrics['avg_importance'].value / 5.0, 1.0) * 25
            score_components.append(importance_score)
        
        # 内容丰富度得分
        if 'tag_diversity' in metrics and 'total_memories' in metrics:
            if metrics['total_memories'].value > 0:
                diversity_ratio = metrics['tag_diversity'].value / metrics['total_memories'].value
                diversity_score = min(diversity_ratio * 2, 1.0) * 25
                score_components.append(diversity_score)
        
        # 项目覆盖得分
        if 'project_coverage' in metrics:
            coverage_score = min(metrics['project_coverage'].value / 5.0, 1.0) * 25
            score_components.append(coverage_score)
        
        # 协作得分
        if 'collaboration_score' in metrics:
            collab_score = min(metrics['collaboration_score'].value / 10.0, 1.0) * 25
            score_components.append(collab_score)
        
        if score_components:
            analysis['overall_score'] = round(sum(score_components) / len(score_components), 1)
        
        # 识别优势和劣势
        if 'avg_importance' in metrics and metrics['avg_importance'].value >= 4.0:
            analysis['strengths'].append("High-quality memory content")
        
        if 'tag_diversity' in metrics and metrics['tag_diversity'].value >= 10:
            analysis['strengths'].append("Good content organization with diverse tags")
        
        if 'collaboration_score' in metrics and metrics['collaboration_score'].value >= 5:
            analysis['strengths'].append("Active collaboration with other teams")
        
        # 识别需要改进的地方
        if 'total_memories' in metrics and metrics['total_memories'].value < 10:
            analysis['weaknesses'].append("Limited memory content")
        
        if 'project_coverage' in metrics and metrics['project_coverage'].value <= 2:
            analysis['weaknesses'].append("Limited project diversity")
        
        return analysis
    
    def _calculate_memory_statistics(self, memories: List[MemoryEntry]) -> Dict[str, Any]:
        """计算记忆统计信息"""
        if not memories:
            return {'total': 0}
        
        stats = {
            'total': len(memories),
            'by_importance': Counter(m.importance for m in memories),
            'by_project': Counter(m.project for m in memories),
            'by_tags': Counter(tag for m in memories for tag in m.tags),
            'content_length': {
                'min': min(len(m.content) for m in memories),
                'max': max(len(m.content) for m in memories),
                'avg': round(statistics.mean(len(m.content) for m in memories), 2),
                'median': statistics.median(len(m.content) for m in memories)
            },
            'temporal_distribution': self._analyze_temporal_distribution(memories)
        }
        
        return stats
    
    def _analyze_temporal_distribution(self, memories: List[MemoryEntry]) -> Dict[str, Any]:
        """分析时间分布"""
        if not memories:
            return {}
        
        # 按月统计
        monthly_counts = defaultdict(int)
        
        for memory in memories:
            try:
                # 尝试解析时间戳
                if memory.timestamp:
                    dt = datetime.fromisoformat(memory.timestamp.replace('Z', '+00:00'))
                    month_key = dt.strftime('%Y-%m')
                    monthly_counts[month_key] += 1
            except:
                continue
        
        return {
            'monthly_counts': dict(monthly_counts),
            'most_active_month': max(monthly_counts.items(), key=lambda x: x[1])[0] if monthly_counts else None,
            'creation_rate': len(memories) / max(len(monthly_counts), 1)  # 每月平均创建数
        }
    
    def _create_performance_charts(self, metrics: Dict[str, AnalyticsData]) -> List[Dict[str, Any]]:
        """创建性能图表"""
        charts = []
        
        # 雷达图：多维度性能
        radar_data = {
            'type': 'radar',
            'title': 'Team Performance Radar',
            'data': {
                'labels': ['Memory Quality', 'Tag Diversity', 'Project Coverage', 'Collaboration'],
                'values': []
            }
        }
        
        # 提取相关指标值并标准化
        quality_score = min(metrics.get('avg_importance', AnalyticsData('', 3, '')).value / 5.0, 1.0) * 100
        diversity_score = min(metrics.get('tag_diversity', AnalyticsData('', 0, '')).value / 20.0, 1.0) * 100
        coverage_score = min(metrics.get('project_coverage', AnalyticsData('', 1, '')).value / 5.0, 1.0) * 100
        collab_score = min(metrics.get('collaboration_score', AnalyticsData('', 0, '')).value / 10.0, 1.0) * 100
        
        radar_data['data']['values'] = [quality_score, diversity_score, coverage_score, collab_score]
        charts.append(radar_data)
        
        # 柱状图：记忆分布
        if 'total_memories' in metrics and metrics['total_memories'].value > 0:
            bar_chart = {
                'type': 'bar',
                'title': 'Memory Distribution',
                'data': {
                    'labels': ['Total Memories', 'Context Files', 'Collaboration Activities'],
                    'values': [
                        metrics.get('total_memories', AnalyticsData('', 0, '')).value,
                        metrics.get('context_files', AnalyticsData('', 0, '')).value,
                        metrics.get('collaboration_score', AnalyticsData('', 0, '')).value
                    ]
                }
            }
            charts.append(bar_chart)
        
        return charts
    
    def _create_memory_charts(self, stats: Dict[str, Any], patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建记忆图表"""
        charts = []
        
        # 饼图：按重要性分布
        if 'by_importance' in stats and stats['by_importance']:
            importance_chart = {
                'type': 'pie',
                'title': 'Memory Distribution by Importance',
                'data': {
                    'labels': [f'Level {k}' for k in sorted(stats['by_importance'].keys())],
                    'values': [stats['by_importance'][k] for k in sorted(stats['by_importance'].keys())]
                }
            }
            charts.append(importance_chart)
        
        # 柱状图：按项目分布
        if 'by_project' in stats and stats['by_project']:
            project_items = list(stats['by_project'].items())
            project_items.sort(key=lambda x: x[1], reverse=True)
            
            project_chart = {
                'type': 'bar',
                'title': 'Memory Distribution by Project',
                'data': {
                    'labels': [item[0] for item in project_items[:10]],  # 前10个项目
                    'values': [item[1] for item in project_items[:10]]
                }
            }
            charts.append(project_chart)
        
        # 折线图：时间分布
        if 'temporal_distribution' in stats and 'monthly_counts' in stats['temporal_distribution']:
            monthly_data = stats['temporal_distribution']['monthly_counts']
            if monthly_data:
                sorted_months = sorted(monthly_data.keys())
                
                timeline_chart = {
                    'type': 'line',
                    'title': 'Memory Creation Timeline',
                    'data': {
                        'labels': sorted_months,
                        'values': [monthly_data[month] for month in sorted_months]
                    }
                }
                charts.append(timeline_chart)
        
        return charts
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """生成HTML报告"""
        html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ContextX Team Report - {title}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #007acc; padding-bottom: 20px; }}
        .header h1 {{ color: #007acc; margin: 0; font-size: 2.5em; }}
        .header .meta {{ color: #666; margin-top: 10px; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #333; border-left: 4px solid #007acc; padding-left: 15px; margin-bottom: 20px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #007acc; }}
        .metric-card h3 {{ margin: 0 0 10px 0; color: #333; font-size: 1.1em; }}
        .metric-card .value {{ font-size: 2em; font-weight: bold; color: #007acc; }}
        .metric-card .description {{ color: #666; font-size: 0.9em; margin-top: 5px; }}
        .chart-container {{ margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 6px; }}
        .recommendations {{ background: #e8f5e8; padding: 20px; border-radius: 6px; border-left: 4px solid #28a745; }}
        .recommendations h3 {{ color: #28a745; margin-top: 0; }}
        .recommendations ul {{ margin: 10px 0; padding-left: 20px; }}
        .recommendations li {{ margin: 8px 0; }}
        .analysis-section {{ background: #fff3cd; padding: 20px; border-radius: 6px; border-left: 4px solid #ffc107; margin: 20px 0; }}
        .strengths {{ color: #28a745; }}
        .weaknesses {{ color: #dc3545; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ContextX Team Report</h1>
            <div class="meta">
                Report Type: {report_type} | Generated: {generated_at}
                {team_info}
            </div>
        </div>
        
        {content}
        
        <div class="footer">
            Generated by ContextX Team Context System
        </div>
    </div>
</body>
</html>
'''
        
        # 构建内容
        content_sections = []
        
        # 性能指标部分
        if 'metrics' in report_data:
            metrics_html = self._build_metrics_html(report_data['metrics'])
            content_sections.append(f'<div class="section"><h2>Performance Metrics</h2>{metrics_html}</div>')
        
        # 分析部分
        if 'analysis' in report_data:
            analysis_html = self._build_analysis_html(report_data['analysis'])
            content_sections.append(f'<div class="section"><h2>Analysis</h2>{analysis_html}</div>')
        
        # 统计部分
        if 'statistics' in report_data:
            stats_html = self._build_statistics_html(report_data['statistics'])
            content_sections.append(f'<div class="section"><h2>Statistics</h2>{stats_html}</div>')
        
        # 建议部分
        if 'recommendations' in report_data and report_data['recommendations']:
            rec_html = self._build_recommendations_html(report_data['recommendations'])
            content_sections.append(f'<div class="section">{rec_html}</div>')
        
        # 图表部分
        if 'charts' in report_data and report_data['charts']:
            charts_html = self._build_charts_html(report_data['charts'])
            content_sections.append(f'<div class="section"><h2>Visualizations</h2>{charts_html}</div>')
        
        content = '\n'.join(content_sections)
        
        # 填充模板
        team_info = f" | Team: {report_data.get('team_name', 'N/A')}" if 'team_name' in report_data else ""
        
        return html_template.format(
            title=report_data.get('report_type', 'Report'),
            report_type=report_data.get('report_type', 'Unknown'),
            generated_at=report_data.get('generated_at', datetime.now().isoformat()),
            team_info=team_info,
            content=content
        )
    
    def _build_metrics_html(self, metrics: Dict[str, AnalyticsData]) -> str:
        """构建指标HTML"""
        html_parts = ['<div class="metric-grid">']
        
        for metric in metrics.values():
            html_parts.append(f'''
                <div class="metric-card">
                    <h3>{metric.metric_name.replace('_', ' ').title()}</h3>
                    <div class="value">{metric.value}</div>
                    <div class="description">{metric.description}</div>
                </div>
            ''')
        
        html_parts.append('</div>')
        return ''.join(html_parts)
    
    def _build_analysis_html(self, analysis: Dict[str, Any]) -> str:
        """构建分析HTML"""
        html_parts = ['<div class="analysis-section">']
        
        if 'overall_score' in analysis:
            html_parts.append(f'<h3>Overall Score: {analysis["overall_score"]}/100</h3>')
        
        if 'strengths' in analysis and analysis['strengths']:
            html_parts.append('<h4 class="strengths">Strengths:</h4>')
            html_parts.append('<ul class="strengths">')
            for strength in analysis['strengths']:
                html_parts.append(f'<li>{strength}</li>')
            html_parts.append('</ul>')
        
        if 'weaknesses' in analysis and analysis['weaknesses']:
            html_parts.append('<h4 class="weaknesses">Areas for Improvement:</h4>')
            html_parts.append('<ul class="weaknesses">')
            for weakness in analysis['weaknesses']:
                html_parts.append(f'<li>{weakness}</li>')
            html_parts.append('</ul>')
        
        html_parts.append('</div>')
        return ''.join(html_parts)
    
    def _build_recommendations_html(self, recommendations: List[str]) -> str:
        """构建建议HTML"""
        html_parts = ['<div class="recommendations">']
        html_parts.append('<h3>Recommendations</h3>')
        html_parts.append('<ul>')
        
        for rec in recommendations:
            html_parts.append(f'<li>{rec}</li>')
        
        html_parts.append('</ul>')
        html_parts.append('</div>')
        return ''.join(html_parts)
    
    def _build_charts_html(self, charts: List[Dict[str, Any]]) -> str:
        """构建图表HTML"""
        html_parts = []
        
        for chart in charts:
            html_parts.append(f'''
                <div class="chart-container">
                    <h3>{chart.get('title', 'Chart')}</h3>
                    <p>Chart Type: {chart.get('type', 'unknown').title()}</p>
                    <div>Chart data: {json.dumps(chart.get('data', {}))}</div>
                    <p><em>Note: Interactive charts require JavaScript visualization library integration.</em></p>
                </div>
            ''')
        
        return ''.join(html_parts)
    
    def _load_chart_templates(self) -> Dict[str, str]:
        """加载图表模板"""
        return {
            'radar': '''
                <canvas id="radar-{id}" width="400" height="400"></canvas>
                <script>
                    // Chart.js radar chart implementation
                </script>
            ''',
            'bar': '''
                <canvas id="bar-{id}" width="400" height="300"></canvas>
                <script>
                    // Chart.js bar chart implementation
                </script>
            ''',
            'pie': '''
                <canvas id="pie-{id}" width="400" height="400"></canvas>
                <script>
                    // Chart.js pie chart implementation
                </script>
            '''
        }
    
    def _load_team_memories(self, team_name: str) -> List[MemoryEntry]:
        """加载团队记忆"""
        if not self.directory_manager.team_exists(team_name):
            return []
        
        team_path = self.directory_manager.get_team_path(team_name)
        memories = []
        
        # 加载各类记忆文件
        memory_files = [
            team_path / "memory" / "declarative.md",
            team_path / "memory" / "procedural.md"
        ]
        
        # 加载情景性记忆
        episodic_dir = team_path / "memory" / "episodic"
        if episodic_dir.exists():
            memory_files.extend(episodic_dir.glob("*.md"))
        
        for file_path in memory_files:
            if file_path.exists():
                file_memories = self.markdown_engine.load_memories(file_path)
                memories.extend(file_memories)
        
        return memories
    
    def _filter_memories_by_date(self, memories: List[MemoryEntry], 
                                date_range: Tuple[str, str]) -> List[MemoryEntry]:
        """按日期范围过滤记忆"""
        start_date, end_date = date_range
        filtered = []
        
        for memory in memories:
            try:
                if memory.timestamp:
                    memory_date = datetime.fromisoformat(memory.timestamp.replace('Z', '+00:00'))
                    if start_date <= memory_date.isoformat() <= end_date:
                        filtered.append(memory)
            except:
                continue
        
        return filtered
    
    def _save_report(self, report_data: Dict[str, Any], team_name: str, config: ReportConfig):
        """保存报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if config.output_format == 'html':
            filename = f"{team_name}_{report_data['report_type']}_{timestamp}.html"
            output_path = self.reports_dir / filename
            self.export_report_to_html(report_data, output_path)
        elif config.output_format == 'json':
            filename = f"{team_name}_{report_data['report_type']}_{timestamp}.json"
            output_path = self.reports_dir / filename
            output_path.write_text(
                json.dumps(report_data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
    
    # 占位符方法，用于其他功能
    def _generate_performance_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成性能建议"""
        recommendations = []
        
        if analysis.get('overall_score', 0) < 50:
            recommendations.append("Consider increasing team activity and memory creation")
        
        if 'Limited memory content' in analysis.get('weaknesses', []):
            recommendations.append("Focus on documenting more team knowledge and experiences")
        
        if 'Limited project diversity' in analysis.get('weaknesses', []):
            recommendations.append("Expand involvement in different projects to increase knowledge breadth")
        
        return recommendations
    
    def _analyze_memory_patterns(self, memories: List[MemoryEntry]) -> Dict[str, Any]:
        """分析记忆模式"""
        patterns = {}
        
        if memories:
            # 标签共现分析
            tag_cooccurrence = defaultdict(int)
            for memory in memories:
                tags = memory.tags
                for i, tag1 in enumerate(tags):
                    for tag2 in tags[i+1:]:
                        pair = tuple(sorted([tag1, tag2]))
                        tag_cooccurrence[pair] += 1
            
            patterns['tag_cooccurrence'] = dict(tag_cooccurrence)
            
            # 内容长度模式
            content_lengths = [len(m.content) for m in memories]
            patterns['content_length_patterns'] = {
                'short_memories': len([l for l in content_lengths if l < 200]),
                'medium_memories': len([l for l in content_lengths if 200 <= l < 1000]),
                'long_memories': len([l for l in content_lengths if l >= 1000])
            }
        
        return patterns
    
    def _generate_memory_insights(self, stats: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
        """生成记忆洞察"""
        insights = []
        
        if stats.get('total', 0) > 0:
            insights.append(f"Team has created {stats['total']} memories")
            
            if 'by_importance' in stats:
                high_importance = stats['by_importance'].get(4, 0) + stats['by_importance'].get(5, 0)
                if high_importance > stats['total'] * 0.5:
                    insights.append("Team focuses on high-importance content")
        
        return insights
    
    def _collect_system_statistics(self) -> Dict[str, Any]:
        """收集系统统计信息"""
        stats = {
            'total_teams': 0,
            'total_memories': 0,
            'total_contexts': 0,
            'system_health': 'good'
        }
        
        teams_dir = self.base_path / "teams"
        if teams_dir.exists():
            stats['total_teams'] = len([d for d in teams_dir.iterdir() if d.is_dir()])
        
        return stats
    
    def _analyze_system_health(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """分析系统健康度"""
        return {
            'status': 'healthy',
            'score': 85,
            'issues': []
        }
    
    def _analyze_usage_trends(self, date_range: Optional[Tuple[str, str]]) -> Dict[str, Any]:
        """分析使用趋势"""
        return {
            'trend_direction': 'increasing',
            'growth_rate': 5.2
        }
    
    def _analyze_resource_utilization(self) -> Dict[str, Any]:
        """分析资源利用率"""
        return {
            'storage_usage': 65,
            'memory_efficiency': 78
        }
    
    def _generate_system_predictions(self, trends: Dict[str, Any]) -> List[str]:
        """生成系统预测"""
        return [
            "System usage expected to grow by 10% next month",
            "Collaboration activities likely to increase"
        ]
    
    def _create_dashboard_data(self, stats: Dict[str, Any], health: Dict[str, Any], trends: Dict[str, Any]) -> Dict[str, Any]:
        """创建仪表板数据"""
        return {
            'key_metrics': stats,
            'health_status': health,
            'trend_indicators': trends
        }
    
    def _analyze_collaboration_efficiency(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析协作效率"""
        return {
            'overall_efficiency': 75,
            'top_collaborators': []
        }
    
    def _identify_collaboration_bottlenecks(self, team_data: Dict[str, Any]) -> List[str]:
        """识别协作瓶颈"""
        return [
            "Limited cross-team knowledge sharing",
            "Uneven collaboration distribution"
        ]
    
    def _create_collaboration_network(self, matrix: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """创建协作网络数据"""
        nodes = []
        edges = []
        
        # 提取节点（团队）
        all_teams = set()
        for source, targets in matrix.items():
            all_teams.add(source)
            all_teams.update(targets.keys())
        
        for team in all_teams:
            nodes.append({'id': team, 'label': team})
        
        # 提取边（协作关系）
        for source, targets in matrix.items():
            for target, weight in targets.items():
                if weight > 0:
                    edges.append({
                        'from': source,
                        'to': target,
                        'weight': weight
                    })
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def _generate_collaboration_recommendations(self, efficiency: Dict[str, Any], bottlenecks: List[str]) -> List[str]:
        """生成协作建议"""
        recommendations = []
        
        if efficiency.get('overall_efficiency', 0) < 60:
            recommendations.append("Implement regular cross-team knowledge sharing sessions")
        
        for bottleneck in bottlenecks:
            if "Limited cross-team" in bottleneck:
                recommendations.append("Create shared project channels for better communication")
        
        return recommendations
    
    def _process_custom_section(self, section: Dict[str, Any], config: ReportConfig) -> Dict[str, Any]:
        """处理自定义报告部分"""
        return {
            'title': section.get('title', 'Custom Section'),
            'type': section.get('type', 'text'),
            'content': section.get('content', '')
        }
    
    def _build_statistics_html(self, statistics: Dict[str, Any]) -> str:
        """构建统计信息HTML"""
        html_parts = ['<div class="statistics-section">']
        
        for key, value in statistics.items():
            if isinstance(value, dict):
                html_parts.append(f'<h4>{key.replace("_", " ").title()}</h4>')
                html_parts.append('<ul>')
                for sub_key, sub_value in value.items():
                    html_parts.append(f'<li>{sub_key}: {sub_value}</li>')
                html_parts.append('</ul>')
            else:
                html_parts.append(f'<p><strong>{key.replace("_", " ").title()}:</strong> {value}</p>')
        
        html_parts.append('</div>')
        return ''.join(html_parts) 