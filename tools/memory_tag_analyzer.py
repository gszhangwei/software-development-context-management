#!/usr/bin/env python3
"""
记忆项目标签质量分析工具

基于标签策略指南，提供标签质量评估、优化建议和批量分析功能
"""

import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

@dataclass
class MemoryEntry:
    """记忆条目数据结构"""
    id: str
    content: str
    tags: List[str]
    project: str = 'general'
    importance: int = 3
    file_path: str = ''

class TagAnalyzer:
    """标签质量分析器"""
    
    def __init__(self):
        self.load_tag_dictionaries()
    
    def load_tag_dictionaries(self):
        """加载标签词典"""
        self.core_business_tags = {
            'workflow', 'solution', 'rule', 'step', 'api', 'data', 'model', 
            'validation', 'creation', 'enhancement', 'optimization', 
            'integration', 'reference', 'authentication', 'authorization'
        }
        
        self.tech_stack_tags = {
            'rest-api', 'database', 'controller', 'service', 'repository', 
            'entity', 'dto', 'json', 'http', 'sql', 'nosql', 'cache', 
            'microservice', 'spring-boot'
        }
        
        self.action_tags = {
            'create', 'update', 'delete', 'validate', 'enhance', 'optimize', 
            'fix', 'implement', 'design', 'configure', 'deploy', 'test'
        }
        
        self.concept_combination_patterns = [
            r'.*-as-.*', r'.*-step.*', r'.*-validation', r'.*-enhancement',
            r'.*-processing', r'.*-routing', r'.*-integration'
        ]
        
        self.architecture_tags = {
            'architecture', 'design', 'microservice', 'scalability',
            'inheritance', 'polymorphism'
        }
    
    def analyze_memory_file(self, file_path: Path) -> Dict:
        """分析记忆文件的标签质量"""
        memories = self.load_memories_from_file(file_path)
        results = {
            'file_path': str(file_path),
            'total_memories': len(memories),
            'memories': [],
            'overall_score': 0,
            'recommendations': []
        }
        
        total_score = 0
        for memory in memories:
            memory_analysis = self.analyze_memory_tags(memory)
            results['memories'].append(memory_analysis)
            total_score += memory_analysis['score']
        
        if memories:
            results['overall_score'] = total_score / len(memories)
            
        # 生成整体建议
        results['recommendations'] = self.generate_file_recommendations(results)
        
        return results
    
    def load_memories_from_file(self, file_path: Path) -> List[MemoryEntry]:
        """从文件加载记忆条目"""
        if not file_path.exists():
            return []
        
        content = file_path.read_text(encoding='utf-8')
        memories = []
        
        # 匹配记忆条目
        memory_pattern = re.compile(
            r'### 记忆项目 #(\w+)\n(.*?)(?=### 记忆项目 #|\Z)',
            re.MULTILINE | re.DOTALL
        )
        
        matches = memory_pattern.findall(content)
        for entry_id, entry_content in matches:
            memory = self.parse_memory_entry(entry_id, entry_content, str(file_path))
            if memory:
                memories.append(memory)
        
        return memories
    
    def parse_memory_entry(self, entry_id: str, entry_content: str, file_path: str) -> Optional[MemoryEntry]:
        """解析单个记忆条目"""
        metadata_pattern = re.compile(r'- \*\*([^*]+)\*\*:\s*(.+?)(?=\n- \*\*|\Z)', re.DOTALL)
        metadata_matches = metadata_pattern.findall(entry_content)
        
        entry_data = {
            'id': entry_id,
            'file_path': file_path,
            'tags': [],
            'content': '',
            'project': 'general',
            'importance': 3
        }
        
        for key, value in metadata_matches:
            key = key.strip()
            value = value.strip()
            
            if key == '内容':
                entry_data['content'] = value
            elif key == '标签':
                if ',' in value:
                    tags = [tag.strip().lstrip('#') for tag in value.split(',') if tag.strip()]
                else:
                    tags = [tag.strip().lstrip('#') for tag in value.split() if tag.strip()]
                entry_data['tags'] = tags
            elif key == '项目':
                entry_data['project'] = value
            elif key == '重要性':
                entry_data['importance'] = value.count('⭐')
        
        if not entry_data['content']:
            return None
        
        return MemoryEntry(**entry_data)
    
    def analyze_memory_tags(self, memory: MemoryEntry) -> Dict:
        """分析单个记忆的标签质量"""
        analysis = {
            'id': memory.id,
            'tag_count': len(memory.tags),
            'tags': memory.tags,
            'score': 0,
            'breakdown': {},
            'issues': [],
            'suggestions': []
        }
        
        # 1. 标签数量检查 (20分)
        tag_count_score = self.check_tag_count(memory.tags)
        analysis['breakdown']['tag_count'] = tag_count_score
        analysis['score'] += tag_count_score
        
        if tag_count_score < 15:
            if len(memory.tags) < 8:
                analysis['issues'].append(f"标签数量过少 ({len(memory.tags)}个)，建议8-15个")
                analysis['suggestions'].append("增加更多描述性标签")
            else:
                analysis['issues'].append(f"标签数量过多 ({len(memory.tags)}个)，建议8-15个")
                analysis['suggestions'].append("删减冗余标签")
        
        # 2. 分层标签检查 (30分)
        layer_score = self.check_tag_layers(memory.tags)
        analysis['breakdown']['layer_distribution'] = layer_score
        analysis['score'] += sum(layer_score.values())
        
        if layer_score['core_function'] < 10:
            analysis['issues'].append("缺少核心功能标签")
            analysis['suggestions'].append("添加直接描述解决问题的标签")
        
        if layer_score['tech_implementation'] < 5:
            analysis['issues'].append("缺少技术实现标签")
            analysis['suggestions'].append("添加技术栈相关标签")
        
        # 3. 关键词覆盖检查 (25分)
        coverage_score = self.check_keyword_coverage(memory)
        analysis['breakdown']['keyword_coverage'] = coverage_score
        analysis['score'] += coverage_score
        
        if coverage_score < 15:
            analysis['issues'].append("标签与内容关键词覆盖度低")
            analysis['suggestions'].append("分析内容关键词，添加相关标签")
        
        # 4. 命名规范检查 (25分)
        naming_score = self.check_naming_conventions(memory.tags)
        analysis['breakdown']['naming_conventions'] = naming_score
        analysis['score'] += naming_score
        
        if naming_score < 20:
            analysis['issues'].append("标签命名不符合规范")
            analysis['suggestions'].append("使用连字符分隔，避免下划线和驼峰命名")
        
        # 生成具体的标签建议
        tag_suggestions = self.suggest_tags_for_memory(memory)
        if tag_suggestions:
            analysis['suggested_tags'] = tag_suggestions
        
        return analysis
    
    def check_tag_count(self, tags: List[str]) -> int:
        """检查标签数量得分"""
        count = len(tags)
        if 8 <= count <= 15:
            return 20
        elif 5 <= count < 8 or 15 < count <= 20:
            return 15
        else:
            return 10
    
    def check_tag_layers(self, tags: List[str]) -> Dict[str, int]:
        """检查标签分层分布"""
        scores = {
            'core_function': 0,
            'tech_implementation': 0,
            'concept_combination': 0,
            'architecture_design': 0
        }
        
        # 核心功能标签检查
        core_count = sum(1 for tag in tags if tag in self.core_business_tags or tag in self.action_tags)
        if core_count >= 3:
            scores['core_function'] = 15
        elif core_count >= 2:
            scores['core_function'] = 10
        else:
            scores['core_function'] = 5
        
        # 技术实现标签检查
        tech_count = sum(1 for tag in tags if tag in self.tech_stack_tags)
        if tech_count >= 2:
            scores['tech_implementation'] = 8
        elif tech_count >= 1:
            scores['tech_implementation'] = 5
        else:
            scores['tech_implementation'] = 2
        
        # 概念组合标签检查
        concept_count = sum(1 for tag in tags 
                           if any(re.match(pattern, tag) for pattern in self.concept_combination_patterns))
        if concept_count >= 2:
            scores['concept_combination'] = 7
        elif concept_count >= 1:
            scores['concept_combination'] = 4
        else:
            scores['concept_combination'] = 1
        
        # 架构设计标签检查
        arch_count = sum(1 for tag in tags if tag in self.architecture_tags)
        if arch_count <= 2 and arch_count > 0:
            scores['architecture_design'] = 5
        elif arch_count > 2:
            scores['architecture_design'] = 2  # 太多架构标签
        else:
            scores['architecture_design'] = 3  # 没有架构标签也可以
        
        return scores
    
    def check_keyword_coverage(self, memory: MemoryEntry) -> int:
        """检查关键词覆盖度"""
        content_words = set(re.findall(r'\b[a-z]+\b', memory.content.lower()))
        tech_words = content_words & (self.core_business_tags | self.tech_stack_tags | self.action_tags)
        
        tag_words_lists = [tag.lower().replace('-', ' ').split() for tag in memory.tags]
        tag_words = {word for words in tag_words_lists for word in words}
        
        if not tech_words:
            return 15  # 如果内容中没有技术词汇，给默认分
        
        coverage = len(tech_words & tag_words) / len(tech_words)
        return int(coverage * 25)
    
    def check_naming_conventions(self, tags: List[str]) -> int:
        """检查命名规范"""
        score = 25
        
        for tag in tags:
            # 检查是否使用连字符
            if '_' in tag:
                score -= 2  # 使用下划线扣分
            elif any(c.isupper() for c in tag):
                score -= 2  # 使用大写字母扣分
            elif len(tag.split('-')) > 4:
                score -= 1  # 过长的复合词扣分
        
        return max(0, score)
    
    def suggest_tags_for_memory(self, memory: MemoryEntry) -> List[str]:
        """为记忆建议新标签"""
        suggestions = []
        content_lower = memory.content.lower()
        existing_tags = set(tag.lower() for tag in memory.tags)
        
        # 建议核心业务标签
        for tag in self.core_business_tags:
            if tag in content_lower and tag not in existing_tags:
                suggestions.append(tag)
        
        # 建议技术栈标签
        for tag in self.tech_stack_tags:
            if tag.replace('-', ' ') in content_lower and tag not in existing_tags:
                suggestions.append(tag)
        
        # 建议动作标签
        for tag in self.action_tags:
            if tag in content_lower and tag not in existing_tags:
                suggestions.append(tag)
        
        # 建议概念组合标签
        concept_suggestions = self.suggest_concept_combinations(memory)
        suggestions.extend(concept_suggestions)
        
        return suggestions[:8]  # 最多建议8个新标签
    
    def suggest_concept_combinations(self, memory: MemoryEntry) -> List[str]:
        """建议概念组合标签"""
        suggestions = []
        content_lower = memory.content.lower()
        
        # 常见概念组合模式
        combinations = [
            ('solution', 'step', 'solution-as-step'),
            ('workflow', 'step', 'workflow-steps'),
            ('solution', 'reference', 'solution-reference'),
            ('step', 'validation', 'step-validation'),
            ('api', 'enhancement', 'api-enhancement'),
            ('workflow', 'creation', 'workflow-creation'),
            ('data', 'validation', 'data-validation'),
            ('error', 'handling', 'error-handling'),
            ('performance', 'optimization', 'performance-optimization')
        ]
        
        for word1, word2, combo_tag in combinations:
            if word1 in content_lower and word2 in content_lower:
                if combo_tag not in [tag.lower() for tag in memory.tags]:
                    suggestions.append(combo_tag)
        
        return suggestions
    
    def generate_file_recommendations(self, analysis_results: Dict) -> List[str]:
        """生成文件级别的建议"""
        recommendations = []
        
        avg_score = analysis_results['overall_score']
        if avg_score < 70:
            recommendations.append(f"整体标签质量需要改进 (平均分: {avg_score:.1f})")
        
        # 统计常见问题
        all_issues = []
        for memory in analysis_results['memories']:
            all_issues.extend(memory['issues'])
        
        issue_counts = Counter(all_issues)
        for issue, count in issue_counts.most_common(3):
            if count > 1:
                recommendations.append(f"常见问题: {issue} (影响{count}个记忆)")
        
        return recommendations

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python memory_tag_analyzer.py <memory_file_or_directory>")
        print("示例: python memory_tag_analyzer.py test_data/teams/engineering_team/memory/")
        return
    
    path = Path(sys.argv[1])
    analyzer = TagAnalyzer()
    
    if path.is_file():
        # 分析单个文件
        results = analyzer.analyze_memory_file(path)
        print_analysis_results(results)
    elif path.is_dir():
        # 分析目录下的所有记忆文件
        memory_files = list(path.rglob("*.md"))
        memory_files = [f for f in memory_files if '/memory/' in str(f)]
        
        if not memory_files:
            print(f"在 {path} 中未找到记忆文件")
            return
        
        print(f"🔍 找到 {len(memory_files)} 个记忆文件")
        print("=" * 60)
        
        all_results = []
        for file_path in memory_files:
            results = analyzer.analyze_memory_file(file_path)
            all_results.append(results)
            print(f"\n📁 {file_path.name}")
            print_analysis_results(results, brief=True)
        
        # 生成汇总报告
        print("\n" + "=" * 60)
        print("📊 汇总报告")
        generate_summary_report(all_results)
    else:
        print(f"路径不存在: {path}")

def print_analysis_results(results: Dict, brief: bool = False):
    """打印分析结果"""
    if brief:
        print(f"  平均分: {results['overall_score']:.1f}/100")
        print(f"  记忆数: {results['total_memories']}")
        if results['recommendations']:
            print(f"  主要问题: {results['recommendations'][0]}")
        return
    
    print(f"📄 文件: {results['file_path']}")
    print(f"📊 总体评分: {results['overall_score']:.1f}/100")
    print(f"🧠 记忆数量: {results['total_memories']}")
    
    if results['recommendations']:
        print("\n💡 文件级建议:")
        for rec in results['recommendations']:
            print(f"  - {rec}")
    
    print(f"\n📋 详细分析:")
    for memory in results['memories']:
        print(f"\n  记忆 {memory['id']}:")
        print(f"    评分: {memory['score']}/100")
        print(f"    标签数: {memory['tag_count']}")
        print(f"    标签: {', '.join(memory['tags'][:5])}{'...' if len(memory['tags']) > 5 else ''}")
        
        if memory['issues']:
            print(f"    问题: {', '.join(memory['issues'][:2])}")
        
        if memory.get('suggested_tags'):
            print(f"    建议新增: {', '.join(memory['suggested_tags'][:3])}")

def generate_summary_report(all_results: List[Dict]):
    """生成汇总报告"""
    total_memories = sum(r['total_memories'] for r in all_results)
    avg_score = sum(r['overall_score'] * r['total_memories'] for r in all_results) / total_memories if total_memories > 0 else 0
    
    print(f"总记忆数: {total_memories}")
    print(f"平均分: {avg_score:.1f}/100")
    
    # 找出得分最低的记忆
    all_memories = []
    for results in all_results:
        for memory in results['memories']:
            memory['file'] = results['file_path']
            all_memories.append(memory)
    
    all_memories.sort(key=lambda x: x['score'])
    
    print(f"\n🚨 需要优先优化的记忆 (评分 < 60):")
    low_score_memories = [m for m in all_memories if m['score'] < 60]
    for memory in low_score_memories[:5]:
        print(f"  {memory['id']} ({memory['score']}/100) - {Path(memory['file']).name}")

if __name__ == "__main__":
    main() 