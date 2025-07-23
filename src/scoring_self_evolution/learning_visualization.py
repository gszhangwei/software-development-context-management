#!/usr/bin/env python3
"""
自学习记忆评分引擎可视化工具

用于展示关键词权重变化、学习进度和系统稳定性的可视化脚本。
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class LearningVisualization:
    """学习过程可视化器"""
    
    def __init__(self, matrix_file: str = "self_learning_keyword_matrix.json"):
        self.matrix_file = matrix_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """加载矩阵数据"""
        if Path(self.matrix_file).exists():
            with open(self.matrix_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def plot_learning_progress(self):
        """绘制学习进度图表"""
        if not self.data:
            print("No data available for visualization")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('自学习记忆评分引擎 - 学习进度可视化', fontsize=16, fontweight='bold')
        
        # 1. 关键词使用频率分布
        self._plot_keyword_usage_distribution(ax1)
        
        # 2. 维度权重分布
        self._plot_dimension_weights(ax2)
        
        # 3. 学习会话趋势
        self._plot_learning_sessions(ax3)
        
        # 4. 关键词稳定性分析
        self._plot_keyword_stability(ax4)
        
        plt.tight_layout()
        plt.savefig('learning_progress.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def _plot_keyword_usage_distribution(self, ax):
        """绘制关键词使用频率分布"""
        keyword_stats = self.data.get('keyword_stats', {})
        if not keyword_stats:
            ax.text(0.5, 0.5, 'No keyword usage data', ha='center', va='center')
            ax.set_title('关键词使用频率分布')
            return
        
        # 获取使用次数数据
        usage_counts = [stats['usage_count'] for stats in keyword_stats.values()]
        keywords = [stats['keyword'] for stats in keyword_stats.values()]
        
        # 选择使用次数最多的前15个关键词
        sorted_indices = np.argsort(usage_counts)[-15:]
        top_keywords = [keywords[i] for i in sorted_indices]
        top_usage = [usage_counts[i] for i in sorted_indices]
        
        bars = ax.barh(range(len(top_keywords)), top_usage, color='skyblue')
        ax.set_yticks(range(len(top_keywords)))
        ax.set_yticklabels(top_keywords)
        ax.set_xlabel('使用次数')
        ax.set_title('关键词使用频率分布 (Top 15)')
        
        # 添加数值标签
        for bar, usage in zip(bars, top_usage):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                   str(usage), va='center', fontsize=8)
    
    def _plot_dimension_weights(self, ax):
        """绘制维度权重分布"""
        matrix = self.data.get('matrix', {})
        if not matrix:
            ax.text(0.5, 0.5, 'No matrix data', ha='center', va='center')
            ax.set_title('维度权重分布')
            return
        
        dimensions = list(matrix.keys())
        avg_weights = []
        
        for dimension in dimensions:
            weights = list(matrix[dimension].values())
            avg_weights.append(np.mean(weights) if weights else 0)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(dimensions)))
        wedges, texts, autotexts = ax.pie(avg_weights, labels=dimensions, autopct='%1.1f%%', 
                                         colors=colors, startangle=90)
        
        ax.set_title('维度平均权重分布')
        
        # 美化文本
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
    
    def _plot_learning_sessions(self, ax):
        """绘制学习会话趋势"""
        scoring_history = self.data.get('scoring_history', [])
        if not scoring_history:
            ax.text(0.5, 0.5, 'No session history', ha='center', va='center')
            ax.set_title('学习会话趋势')
            return
        
        sessions = sorted(scoring_history, key=lambda x: x['timestamp'])
        timestamps = [datetime.fromisoformat(s['timestamp']) for s in sessions]
        top_scores = [s['top_score'] for s in sessions]
        usage_counts = [s.get('matrix_usage_count', 0) for s in sessions]
        
        ax2 = ax.twinx()
        
        line1 = ax.plot(timestamps, top_scores, 'b-o', label='最高评分', markersize=4)
        line2 = ax2.plot(timestamps, usage_counts, 'r-s', label='总使用次数', markersize=4)
        
        ax.set_xlabel('时间')
        ax.set_ylabel('最高评分', color='b')
        ax2.set_ylabel('总使用次数', color='r')
        ax.tick_params(axis='y', labelcolor='b')
        ax2.tick_params(axis='y', labelcolor='r')
        
        # 合并图例
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper left')
        
        ax.set_title('学习会话趋势')
        ax.grid(True, alpha=0.3)
    
    def _plot_keyword_stability(self, ax):
        """绘制关键词稳定性分析"""
        keyword_stats = self.data.get('keyword_stats', {})
        if not keyword_stats:
            ax.text(0.5, 0.5, 'No stability data', ha='center', va='center')
            ax.set_title('关键词稳定性分析')
            return
        
        stability_scores = []
        avg_contributions = []
        usage_counts = []
        keywords = []
        
        for stats in keyword_stats.values():
            stability_scores.append(stats.get('stability_score', 0))
            avg_contributions.append(stats.get('avg_score_contribution', 0))
            usage_counts.append(stats.get('usage_count', 0))
            keywords.append(stats['keyword'])
        
        # 创建散点图，气泡大小表示使用次数
        sizes = [max(20, count * 10) for count in usage_counts]
        scatter = ax.scatter(stability_scores, avg_contributions, s=sizes, 
                           alpha=0.6, c=usage_counts, cmap='viridis')
        
        ax.set_xlabel('稳定性分数')
        ax.set_ylabel('平均贡献分数')
        ax.set_title('关键词稳定性 vs 贡献度分析')
        
        # 添加颜色条
        plt.colorbar(scatter, ax=ax, label='使用次数')
        
        # 标注表现最好的几个关键词
        for i, (x, y, keyword) in enumerate(zip(stability_scores, avg_contributions, keywords)):
            if y > 8 or x > 0.15:  # 高贡献度或高稳定性
                ax.annotate(keyword, (x, y), xytext=(5, 5), 
                           textcoords='offset points', fontsize=8, alpha=0.8)
    
    def generate_learning_report(self) -> str:
        """生成学习报告"""
        if not self.data:
            return "无数据可用于生成报告"
        
        report = []
        report.append("# 自学习记忆评分引擎 - 学习报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 基本统计信息
        metadata = self.data.get('metadata', {})
        keyword_stats = self.data.get('keyword_stats', {})
        scoring_history = self.data.get('scoring_history', [])
        discovered_log = self.data.get('discovered_keywords_log', [])
        
        report.append("## 基本统计信息")
        report.append(f"- 总关键词数: {metadata.get('total_keywords', 0)}")
        report.append(f"- 总使用次数: {metadata.get('total_usage_count', 0)}")
        report.append(f"- 发现新关键词数: {metadata.get('discovered_keywords_count', 0)}")
        report.append(f"- 评分会话数: {len(scoring_history)}")
        report.append(f"- 矩阵版本: {self.data.get('version', 'unknown')}")
        report.append("")
        
        # 学习参数
        learning_params = self.data.get('learning_parameters', {})
        if learning_params:
            report.append("## 学习参数")
            for key, value in learning_params.items():
                report.append(f"- {key}: {value}")
            report.append("")
        
        # 关键词性能分析
        if keyword_stats:
            report.append("## 关键词性能分析")
            
            # 表现最好的关键词
            top_performers = sorted(
                keyword_stats.items(),
                key=lambda x: x[1].get('avg_score_contribution', 0),
                reverse=True
            )[:10]
            
            report.append("### 表现最好的关键词 (Top 10)")
            for key, stats in top_performers:
                keyword = stats['keyword']
                dimension = stats['dimension']
                contribution = stats.get('avg_score_contribution', 0)
                usage = stats.get('usage_count', 0)
                report.append(f"- {keyword} ({dimension}): 贡献度={contribution:.3f}, 使用次数={usage}")
            report.append("")
            
            # 最稳定的关键词
            most_stable = sorted(
                keyword_stats.items(),
                key=lambda x: x[1].get('stability_score', 0),
                reverse=True
            )[:10]
            
            report.append("### 最稳定的关键词 (Top 10)")
            for key, stats in most_stable:
                keyword = stats['keyword']
                dimension = stats['dimension']
                stability = stats.get('stability_score', 0)
                usage = stats.get('usage_count', 0)
                report.append(f"- {keyword} ({dimension}): 稳定性={stability:.3f}, 使用次数={usage}")
            report.append("")
        
        # 新发现关键词
        if discovered_log:
            report.append("## 新发现关键词")
            total_discovered = sum(len(log.get('added_keywords', [])) for log in discovered_log)
            report.append(f"总计发现 {total_discovered} 个新关键词")
            report.append("")
            
            # 最近的发现
            recent_discoveries = []
            for log in discovered_log:
                for keyword_info in log.get('added_keywords', []):
                    recent_discoveries.append({
                        'keyword': keyword_info['keyword'],
                        'dimension': keyword_info['dimension'],
                        'confidence': keyword_info['confidence'],
                        'timestamp': log['timestamp']
                    })
            
            recent_discoveries.sort(key=lambda x: x['timestamp'], reverse=True)
            
            report.append("### 最近发现的关键词 (Top 10)")
            for discovery in recent_discoveries[:10]:
                timestamp = datetime.fromisoformat(discovery['timestamp']).strftime('%Y-%m-%d %H:%M')
                report.append(f"- {discovery['keyword']} ({discovery['dimension']}): "
                            f"置信度={discovery['confidence']:.3f}, 时间={timestamp}")
            report.append("")
        
        # 维度分析
        matrix = self.data.get('matrix', {})
        if matrix:
            report.append("## 维度分析")
            for dimension, keywords in matrix.items():
                avg_weight = np.mean(list(keywords.values())) if keywords else 0
                keyword_count = len(keywords)
                
                # 计算该维度的总使用次数
                dimension_usage = sum(
                    stats.get('usage_count', 0) for stats in keyword_stats.values()
                    if stats.get('dimension') == dimension
                )
                
                report.append(f"### {dimension}")
                report.append(f"- 关键词数量: {keyword_count}")
                report.append(f"- 平均权重: {avg_weight:.2f}")
                report.append(f"- 总使用次数: {dimension_usage}")
                report.append("")
        
        # 学习趋势
        if scoring_history:
            report.append("## 学习趋势")
            first_session = min(scoring_history, key=lambda x: x['timestamp'])
            last_session = max(scoring_history, key=lambda x: x['timestamp'])
            
            first_usage = first_session.get('matrix_usage_count', 0)
            last_usage = last_session.get('matrix_usage_count', 0)
            usage_growth = last_usage - first_usage
            
            first_score = first_session.get('top_score', 0)
            last_score = last_session.get('top_score', 0)
            score_improvement = last_score - first_score
            
            report.append(f"- 学习周期: {len(scoring_history)} 个会话")
            report.append(f"- 使用量增长: {usage_growth} 次")
            report.append(f"- 评分改进: {score_improvement:.2f} 分")
            report.append(f"- 平均会话间隔: 估算为持续学习")
            report.append("")
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "learning_report.md"):
        """保存学习报告到文件"""
        report = self.generate_learning_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"学习报告已保存到: {filename}")


def main():
    """主函数"""
    print("=== 自学习记忆评分引擎可视化工具 ===\n")
    
    visualizer = LearningVisualization()
    
    if not visualizer.data:
        print("错误: 未找到矩阵数据文件 'self_learning_keyword_matrix.json'")
        print("请先运行增强的记忆评分引擎以生成数据。")
        return
    
    # 生成可视化图表
    print("正在生成学习进度可视化图表...")
    try:
        visualizer.plot_learning_progress()
        print("可视化图表已保存为 'learning_progress.png'")
    except Exception as e:
        print(f"生成图表时出错: {e}")
        print("可能是因为缺少matplotlib或中文字体支持")
    
    # 生成文本报告
    print("\n正在生成学习报告...")
    visualizer.save_report()
    
    # 显示简要报告
    print("\n=== 学习状态摘要 ===")
    metadata = visualizer.data.get('metadata', {})
    keyword_stats = visualizer.data.get('keyword_stats', {})
    
    total_keywords = metadata.get('total_keywords', 0)
    total_usage = metadata.get('total_usage_count', 0)
    discovered_count = metadata.get('discovered_keywords_count', 0)
    
    print(f"总关键词数: {total_keywords}")
    print(f"总使用次数: {total_usage}")
    print(f"新发现关键词: {discovered_count}")
    
    if keyword_stats:
        stable_count = sum(1 for stats in keyword_stats.values() 
                          if stats.get('stability_score', 0) >= 0.8)
        print(f"稳定关键词数: {stable_count}")
        
        high_contrib_count = sum(1 for stats in keyword_stats.values() 
                               if stats.get('avg_score_contribution', 0) >= 5.0)
        print(f"高贡献关键词数: {high_contrib_count}")
    
    print(f"\n系统版本: {visualizer.data.get('version', 'unknown')}")
    print("学习状态: 持续优化中...")


if __name__ == "__main__":
    main() 