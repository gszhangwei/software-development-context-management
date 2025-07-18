"""
PromptX上下文模板引擎

提供灵活的模板系统，支持：
- 自定义上下文模板定义
- 动态内容插值和变量替换
- 模板继承和组合
- 条件渲染和循环结构
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .markdown_engine import MarkdownEngine, MemoryEntry
from .content_optimizer import ContentOptimizer, ContentAnalysis


class TemplateType(Enum):
    """模板类型枚举"""
    CONTEXT = "context"
    MEMORY = "memory"
    REPORT = "report"
    SUMMARY = "summary"
    CUSTOM = "custom"


@dataclass
class TemplateVariable:
    """模板变量定义"""
    name: str
    type: str  # string, number, boolean, list, dict, date
    description: str
    default: Any = None
    required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'default': self.default,
            'required': self.required
        }


@dataclass
class Template:
    """模板定义"""
    name: str
    type: TemplateType
    content: str
    variables: List[TemplateVariable] = field(default_factory=list)
    parent_template: Optional[str] = None
    description: str = ""
    author: str = ""
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'type': self.type.value,
            'content': self.content,
            'variables': [var.to_dict() for var in self.variables],
            'parent_template': self.parent_template,
            'description': self.description,
            'author': self.author,
            'version': self.version,
            'created_at': self.created_at,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """从字典创建模板"""
        variables = [
            TemplateVariable(**var_data) 
            for var_data in data.get('variables', [])
        ]
        
        return cls(
            name=data['name'],
            type=TemplateType(data['type']),
            content=data['content'],
            variables=variables,
            parent_template=data.get('parent_template'),
            description=data.get('description', ''),
            author=data.get('author', ''),
            version=data.get('version', '1.0'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            tags=data.get('tags', [])
        )


@dataclass
class RenderContext:
    """渲染上下文"""
    variables: Dict[str, Any] = field(default_factory=dict)
    helpers: Dict[str, Callable] = field(default_factory=dict)
    team_name: str = ""
    project_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取变量值"""
        return self.variables.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置变量值"""
        self.variables[key] = value


class TemplateEngine:
    """模板引擎"""
    
    def __init__(self, base_path: Path):
        """
        初始化模板引擎
        
        Args:
            base_path: 基础路径
        """
        self.base_path = Path(base_path)
        self.templates_dir = self.base_path / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        # 模板缓存
        self.template_cache: Dict[str, Template] = {}
        
        # 内置助手函数
        self.builtin_helpers = {
            'now': lambda: datetime.now().isoformat(),
            'date': lambda fmt='%Y-%m-%d': datetime.now().strftime(fmt),
            'time': lambda fmt='%H:%M:%S': datetime.now().strftime(fmt),
            'upper': lambda text: str(text).upper(),
            'lower': lambda text: str(text).lower(),
            'title': lambda text: str(text).title(),
            'join': lambda items, sep=', ': sep.join(str(item) for item in items),
            'length': lambda items: len(items) if hasattr(items, '__len__') else 0,
            'default': lambda value, default_val: value if value is not None else default_val,
            'truncate': lambda text, length=100: str(text)[:length] + '...' if len(str(text)) > length else str(text)
        }
        
        # 初始化默认模板
        self._initialize_default_templates()
    
    def create_template(self, template: Template) -> bool:
        """
        创建新模板
        
        Args:
            template: 模板对象
            
        Returns:
            创建是否成功
        """
        try:
            # 验证模板
            self._validate_template(template)
            
            # 保存模板文件
            template_file = self.templates_dir / f"{template.name}.json"
            template_data = template.to_dict()
            
            template_file.write_text(
                json.dumps(template_data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            
            # 更新缓存
            self.template_cache[template.name] = template
            
            return True
            
        except Exception as e:
            print(f"Error creating template {template.name}: {e}")
            return False
    
    def load_template(self, name: str) -> Optional[Template]:
        """
        加载模板
        
        Args:
            name: 模板名称
            
        Returns:
            模板对象，如果不存在返回None
        """
        # 检查缓存
        if name in self.template_cache:
            return self.template_cache[name]
        
        # 从文件加载
        template_file = self.templates_dir / f"{name}.json"
        if not template_file.exists():
            return None
        
        try:
            template_data = json.loads(template_file.read_text(encoding='utf-8'))
            template = Template.from_dict(template_data)
            
            # 加载父模板
            if template.parent_template:
                parent = self.load_template(template.parent_template)
                if parent:
                    template = self._merge_templates(parent, template)
            
            # 更新缓存
            self.template_cache[name] = template
            
            return template
            
        except Exception as e:
            print(f"Error loading template {name}: {e}")
            return None
    
    def render_template(self, template_name: str, context: RenderContext) -> Optional[str]:
        """
        渲染模板
        
        Args:
            template_name: 模板名称
            context: 渲染上下文
            
        Returns:
            渲染结果，如果失败返回None
        """
        template = self.load_template(template_name)
        if not template:
            return None
        
        try:
            # 合并助手函数
            all_helpers = {**self.builtin_helpers, **context.helpers}
            
            # 准备渲染环境
            render_env = {
                **context.variables,
                'team_name': context.team_name,
                'project_name': context.project_name,
                'timestamp': context.timestamp,
                'helpers': all_helpers
            }
            
            # 渲染模板内容
            rendered_content = self._render_content(template.content, render_env)
            
            return rendered_content
            
        except Exception as e:
            print(f"Error rendering template {template_name}: {e}")
            return None
    
    def list_templates(self, template_type: Optional[TemplateType] = None) -> List[str]:
        """
        列出可用模板
        
        Args:
            template_type: 模板类型过滤器
            
        Returns:
            模板名称列表
        """
        templates = []
        
        for template_file in self.templates_dir.glob("*.json"):
            template_name = template_file.stem
            
            if template_type:
                template = self.load_template(template_name)
                if template and template.type == template_type:
                    templates.append(template_name)
            else:
                templates.append(template_name)
        
        return sorted(templates)
    
    def get_template_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取模板信息
        
        Args:
            name: 模板名称
            
        Returns:
            模板信息字典
        """
        template = self.load_template(name)
        if not template:
            return None
        
        return {
            'name': template.name,
            'type': template.type.value,
            'description': template.description,
            'author': template.author,
            'version': template.version,
            'created_at': template.created_at,
            'tags': template.tags,
            'variables': [var.to_dict() for var in template.variables],
            'parent_template': template.parent_template
        }
    
    def delete_template(self, name: str) -> bool:
        """
        删除模板
        
        Args:
            name: 模板名称
            
        Returns:
            删除是否成功
        """
        try:
            template_file = self.templates_dir / f"{name}.json"
            if template_file.exists():
                template_file.unlink()
            
            # 清除缓存
            if name in self.template_cache:
                del self.template_cache[name]
            
            return True
            
        except Exception as e:
            print(f"Error deleting template {name}: {e}")
            return False
    
    def _validate_template(self, template: Template):
        """验证模板"""
        if not template.name:
            raise ValueError("Template name is required")
        
        if not template.content:
            raise ValueError("Template content is required")
        
        # 验证模板语法
        self._validate_template_syntax(template.content)
        
        # 验证变量定义
        for variable in template.variables:
            if not variable.name:
                raise ValueError("Variable name is required")
    
    def _validate_template_syntax(self, content: str):
        """验证模板语法"""
        # 检查变量语法 {{variable}}
        variable_pattern = r'\{\{([^}]+)\}\}'
        variables = re.findall(variable_pattern, content)
        
        for var in variables:
            var = var.strip()
            if not var:
                raise ValueError("Empty variable placeholder found")
        
        # 检查条件语法 {% if condition %}...{% endif %}
        condition_pattern = r'\{%\s*(if|elif|else|endif|for|endfor)\s*([^%]*)\s*%\}'
        conditions = re.findall(condition_pattern, content)
        
        # 简单的平衡检查
        if_count = sum(1 for cmd, _ in conditions if cmd == 'if')
        endif_count = sum(1 for cmd, _ in conditions if cmd == 'endif')
        for_count = sum(1 for cmd, _ in conditions if cmd == 'for')
        endfor_count = sum(1 for cmd, _ in conditions if cmd == 'endfor')
        
        if if_count != endif_count:
            raise ValueError("Unbalanced if/endif statements")
        
        if for_count != endfor_count:
            raise ValueError("Unbalanced for/endfor statements")
    
    def _merge_templates(self, parent: Template, child: Template) -> Template:
        """合并父子模板"""
        # 创建新模板，继承父模板的属性
        merged_content = parent.content
        
        # 查找子模板中的块定义
        block_pattern = r'\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}'
        child_blocks = re.findall(block_pattern, child.content, re.DOTALL)
        
        # 替换父模板中的块
        for block_name, block_content in child_blocks:
            block_placeholder = f'{{% block {block_name} %}}{{% endblock %}}'
            parent_block_pattern = r'\{%\s*block\s+' + block_name + r'\s*%\}.*?\{%\s*endblock\s*%\}'
            
            if re.search(parent_block_pattern, merged_content, re.DOTALL):
                merged_content = re.sub(
                    parent_block_pattern,
                    f'{{% block {block_name} %}}{block_content}{{% endblock %}}',
                    merged_content,
                    flags=re.DOTALL
                )
        
        # 合并变量定义
        merged_variables = parent.variables.copy()
        for child_var in child.variables:
            # 子模板变量覆盖父模板
            merged_variables = [var for var in merged_variables if var.name != child_var.name]
            merged_variables.append(child_var)
        
        return Template(
            name=child.name,
            type=child.type,
            content=merged_content,
            variables=merged_variables,
            parent_template=parent.name,
            description=child.description or parent.description,
            author=child.author or parent.author,
            version=child.version,
            created_at=child.created_at,
            tags=list(set(parent.tags + child.tags))
        )
    
    def _render_content(self, content: str, env: Dict[str, Any]) -> str:
        """渲染模板内容"""
        rendered = content
        
        # 渲染变量 {{variable}}
        rendered = self._render_variables(rendered, env)
        
        # 渲染条件语句 {% if %}...{% endif %}
        rendered = self._render_conditions(rendered, env)
        
        # 渲染循环语句 {% for %}...{% endfor %}
        rendered = self._render_loops(rendered, env)
        
        # 渲染助手函数 {{helper(args)}}
        rendered = self._render_helpers(rendered, env)
        
        return rendered
    
    def _render_variables(self, content: str, env: Dict[str, Any]) -> str:
        """渲染变量"""
        def replace_var(match):
            var_expr = match.group(1).strip()
            
            # 处理点号路径 user.name
            if '.' in var_expr:
                parts = var_expr.split('.')
                value = env
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break
            else:
                value = env.get(var_expr)
            
            return str(value) if value is not None else f"{{{{{var_expr}}}}}"
        
        variable_pattern = r'\{\{([^}]+)\}\}'
        return re.sub(variable_pattern, replace_var, content)
    
    def _render_conditions(self, content: str, env: Dict[str, Any]) -> str:
        """渲染条件语句"""
        # 匹配 if...endif 块
        if_pattern = r'\{%\s*if\s+([^%]+)\s*%\}(.*?)\{%\s*endif\s*%\}'
        
        def replace_if(match):
            condition = match.group(1).strip()
            if_content = match.group(2)
            
            # 简单的条件评估
            try:
                # 替换变量引用
                condition_with_vars = self._replace_condition_vars(condition, env)
                result = eval(condition_with_vars)
                
                if result:
                    return if_content
                else:
                    return ""
            except:
                return if_content  # 如果条件评估失败，默认显示内容
        
        return re.sub(if_pattern, replace_if, content, flags=re.DOTALL)
    
    def _render_loops(self, content: str, env: Dict[str, Any]) -> str:
        """渲染循环语句"""
        # 匹配 for...endfor 块
        for_pattern = r'\{%\s*for\s+(\w+)\s+in\s+([^%]+)\s*%\}(.*?)\{%\s*endfor\s*%\}'
        
        def replace_for(match):
            var_name = match.group(1).strip()
            iterable_expr = match.group(2).strip()
            loop_content = match.group(3)
            
            # 获取可迭代对象
            if iterable_expr in env:
                items = env[iterable_expr]
                if not hasattr(items, '__iter__'):
                    return ""
                
                # 渲染循环内容
                result_parts = []
                for item in items:
                    loop_env = env.copy()
                    loop_env[var_name] = item
                    
                    rendered_item = self._render_content(loop_content, loop_env)
                    result_parts.append(rendered_item)
                
                return ''.join(result_parts)
            
            return ""
        
        return re.sub(for_pattern, replace_for, content, flags=re.DOTALL)
    
    def _render_helpers(self, content: str, env: Dict[str, Any]) -> str:
        """渲染助手函数"""
        helpers = env.get('helpers', {})
        
        # 匹配助手函数调用 {{helper_name(args)}}
        helper_pattern = r'\{\{(\w+)\((.*?)\)\}\}'
        
        def replace_helper(match):
            helper_name = match.group(1)
            args_str = match.group(2)
            
            if helper_name in helpers:
                try:
                    # 简单的参数解析
                    if args_str.strip():
                        # 替换参数中的变量
                        args_with_vars = self._replace_condition_vars(args_str, env)
                        args = eval(f"[{args_with_vars}]")
                    else:
                        args = []
                    
                    result = helpers[helper_name](*args)
                    return str(result)
                except:
                    pass
            
            return match.group(0)  # 返回原始内容
        
        return re.sub(helper_pattern, replace_helper, content)
    
    def _replace_condition_vars(self, condition: str, env: Dict[str, Any]) -> str:
        """替换条件中的变量引用"""
        # 简单的变量替换，支持字符串和数字
        for var_name, value in env.items():
            if var_name in condition:
                if isinstance(value, str):
                    condition = condition.replace(var_name, f'"{value}"')
                elif isinstance(value, (int, float, bool)):
                    condition = condition.replace(var_name, str(value).lower())
        
        return condition
    
    def _initialize_default_templates(self):
        """初始化默认模板"""
        # 需求分析模板
        requirements_template = Template(
            name="requirements_analysis",
            type=TemplateType.CONTEXT,
            content="""# Requirements Analysis - {{stage_name}}

**Team:** {{team_name}}
**Project:** {{project_name}}
**Generated:** {{timestamp}}

## Functional Requirements

{% for req in functional_requirements %}
### {{req.title}}
**Priority:** {{req.priority}}
**Description:** {{req.description}}

{% if req.acceptance_criteria %}
**Acceptance Criteria:**
{% for criteria in req.acceptance_criteria %}
- {{criteria}}
{% endfor %}
{% endif %}

{% endfor %}

## Non-functional Requirements

{% for req in non_functional_requirements %}
### {{req.category}}
- **Requirement:** {{req.description}}
- **Metric:** {{req.metric}}
- **Target:** {{req.target}}
{% endfor %}

## Memory Insights

{% if memories %}
{% for memory in memories %}
### {{memory.id}}
**Tags:** {{join(memory.tags)}}
**Importance:** {{memory.importance}}/5

{{memory.content}}

{% endfor %}
{% endif %}

## Summary

Total functional requirements: {{length(functional_requirements)}}
Total non-functional requirements: {{length(non_functional_requirements)}}
Memory sources: {{length(memories)}}

Generated at {{now()}}""",
            variables=[
                TemplateVariable("stage_name", "string", "阶段名称", "Requirements"),
                TemplateVariable("team_name", "string", "团队名称", required=True),
                TemplateVariable("project_name", "string", "项目名称", required=True),
                TemplateVariable("functional_requirements", "list", "功能需求列表", []),
                TemplateVariable("non_functional_requirements", "list", "非功能需求列表", []),
                TemplateVariable("memories", "list", "相关记忆列表", [])
            ],
            description="需求分析上下文模板",
            author="PromptX System",
            tags=["requirements", "analysis", "context"]
        )
        
        # 解决方案设计模板
        solution_template = Template(
            name="solution_design",
            type=TemplateType.CONTEXT,
            content="""# Solution Design - {{stage_name}}

**Team:** {{team_name}}
**Project:** {{project_name}}
**Generated:** {{timestamp}}

## Architecture Overview

{{architecture_overview}}

## Technology Stack

{% for tech in technology_stack %}
### {{tech.category}}
- **Choice:** {{tech.name}}
- **Version:** {{tech.version}}
- **Justification:** {{tech.reason}}
{% endfor %}

## Component Design

{% for component in components %}
### {{component.name}}
**Type:** {{component.type}}
**Responsibility:** {{component.responsibility}}

{% if component.interfaces %}
**Interfaces:**
{% for interface in component.interfaces %}
- {{interface}}
{% endfor %}
{% endif %}

{% endfor %}

## Implementation Strategy

{{implementation_strategy}}

## Risk Assessment

{% for risk in risks %}
### {{risk.title}}
**Probability:** {{risk.probability}}
**Impact:** {{risk.impact}}
**Mitigation:** {{risk.mitigation}}
{% endfor %}

## Memory Insights

{% if memories %}
{% for memory in memories %}
### {{memory.id}}
{{truncate(memory.content, 200)}}
{% endfor %}
{% endif %}

Generated at {{now()}}""",
            variables=[
                TemplateVariable("stage_name", "string", "阶段名称", "Solution"),
                TemplateVariable("team_name", "string", "团队名称", required=True),
                TemplateVariable("project_name", "string", "项目名称", required=True),
                TemplateVariable("architecture_overview", "string", "架构概述", ""),
                TemplateVariable("technology_stack", "list", "技术栈列表", []),
                TemplateVariable("components", "list", "组件列表", []),
                TemplateVariable("implementation_strategy", "string", "实施策略", ""),
                TemplateVariable("risks", "list", "风险列表", []),
                TemplateVariable("memories", "list", "相关记忆列表", [])
            ],
            description="解决方案设计上下文模板",
            author="PromptX System",
            tags=["solution", "design", "context"]
        )
        
        # 保存默认模板
        self.create_template(requirements_template)
        self.create_template(solution_template) 