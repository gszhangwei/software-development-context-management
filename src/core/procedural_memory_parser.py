#!/usr/bin/env python3
"""
Procedural Memory Parser

专门用于解析procedural.md文件格式的解析器，
适配tools中MemoryItem的数据结构。
"""

import re
from pathlib import Path
from typing import List
from tools.enhanced_memory_scoring_engine import MemoryItem


class ProceduralMemoryParser:
    """Procedural Memory解析器"""
    
    def __init__(self):
        # 匹配条目标题和内容的正则表达式
        self.entry_pattern = re.compile(
            r'### (\d+)\.\s*(.+?)\n'
            r'\*\*记忆ID\*\*:\s*(.+?)\s*\n'
            r'\*\*分类\*\*:\s*(.+?)\s*\n'
            r'\*\*作用域\*\*:\s*(.+?)\s*\n'
            r'\*\*项目\*\*:\s*(.+?)\s*\n'
            r'\*\*标签\*\*:\s*(.+?)\s*\n'
            r'\*\*重要性\*\*:\s*(.+?)\s*\n'
            r'\n'
            r'(.*?)(?=\n---\n|\n### \d+\.|\Z)',
            re.MULTILINE | re.DOTALL
        )
    
    def parse_file(self, file_path: Path) -> List[MemoryItem]:
        """解析procedural.md文件"""
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            return []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            entries = []
            
            matches = self.entry_pattern.findall(content)
            print(f"🔍 找到 {len(matches)} 个记忆条目")
            
            for match in matches:
                entry = self._parse_entry(match)
                if entry:
                    entries.append(entry)
            
            return entries
            
        except Exception as e:
            print(f"❌ 解析文件时出错: {e}")
            return []
    
    def _parse_entry(self, match) -> MemoryItem:
        """解析单个记忆条目"""
        try:
            (number, title, memory_id, category, scope, 
             project, tags_str, importance_str, content) = match
            
            # 解析标签
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            
            # 解析重要性
            importance = self._parse_importance(importance_str)
            
            # 清理内容
            content = content.strip()
            
            memory_item = MemoryItem(
                id=memory_id.strip(),
                title=title.strip(),
                content=content,
                tags=tags,
                project=project.strip(),
                importance=importance
            )
            
            print(f"✅ 解析成功: {memory_id} - {title}")
            return memory_item
            
        except Exception as e:
            print(f"❌ 解析条目时出错: {e}")
            return None
    
    def _parse_importance(self, importance_str: str) -> int:
        """解析重要性分数"""
        importance_str = importance_str.strip()
        
        # 处理 "9/10" 格式
        if '/' in importance_str:
            try:
                numerator = int(importance_str.split('/')[0])
                return max(1, min(5, numerator // 2))  # 转换为1-5星级
            except:
                return 3
        
        # 处理星号格式
        star_count = importance_str.count('⭐')
        if star_count > 0:
            return star_count
        
        # 默认值
        return 3


def load_procedural_memories(file_path: Path = None) -> List[MemoryItem]:
    """便捷函数：加载procedural.md记忆条目"""
    if file_path is None:
        file_path = Path("test_data/teams/engineering_team/memory/procedural.md")
    
    parser = ProceduralMemoryParser()
    return parser.parse_file(file_path)


if __name__ == "__main__":
    # 测试解析器
    print("🧪 测试Procedural Memory解析器")
    print("=" * 50)
    
    memories = load_procedural_memories()
    
    print(f"\n📚 解析结果: 共 {len(memories)} 个记忆条目")
    
    for i, memory in enumerate(memories[:3], 1):  # 显示前3个
        print(f"\n{i}. {memory.title}")
        print(f"   ID: {memory.id}")
        print(f"   项目: {memory.project}")
        print(f"   重要性: {'⭐' * memory.importance}")
        print(f"   标签: {', '.join(memory.tags[:5])}")
        print(f"   内容长度: {len(memory.content)} 字符")
    
    if len(memories) > 3:
        print(f"\n... 还有 {len(memories) - 3} 个记忆条目") 