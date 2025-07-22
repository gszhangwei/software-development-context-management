"""
ContextX Team Context Generation Command

Responsible for triggering and managing team context generation, supporting:
- Three context generation modes: memory-only, framework-only, hybrid
- Complete or selective generation of seven-stage framework
- Different output formats and configuration options
- Deep integration with memory system
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .base_command import BaseCommand, CommandResult, TeamCommandMixin
from ..core.context_processor import (
    ContextProcessor, 
    ContextMode, 
    MemoryType,
    ContextGenerationConfig,
    create_memory_only_config,
    create_framework_only_config,
    create_hybrid_config
)


class TeamContextCommand(BaseCommand, TeamCommandMixin):
    """Team context generation command"""
    
    def __init__(self, root_path = None):
        super().__init__(root_path)
        self.base_path = root_path or Path.cwd()
    
    @property
    def name(self) -> str:
        return "team_context"
    
    @property
    def description(self) -> str:
        return "Generate structured team context based on three modes"
    
    def execute(self, team_name: str, action: str = "generate", 
                mode: str = "hybrid", stages: str = None, 
                memory_types: str = "all", output_format: str = "markdown",
                save_results: bool = True, project_scope: str = None,
                memory_importance: int = 2, max_memory_items: int = 50,
                tags_filter: str = None, **kwargs) -> CommandResult:
        """
        Execute team context generation command
        
        Args:
            team_name: Team name
            action: Operation type ('generate', 'list_modes', 'list_stages', 'list_memory_types')
            mode: Generation mode ('memory_only', 'framework_only', 'hybrid')
            stages: Framework stages list, comma-separated, e.g. 'requirements,solution', or 'all'
            memory_types: Memory types ('declarative', 'procedural', 'episodic', 'all')
            output_format: Output format ('markdown', 'json')
            save_results: Whether to save generation results
            project_scope: Project scope filter
            memory_importance: Memory importance threshold (1-5)
            max_memory_items: Maximum number of memory items
            tags_filter: Tags filter, comma-separated
            **kwargs: Other parameters
        
        Returns:
            Command execution result
        """
        try:
            # Validate team exists
            if not self.validate_team_exists(team_name):
                return CommandResult(
                    success=False,
                    message=f"Team '{team_name}' does not exist",
                    error="TEAM_NOT_FOUND"
                )
            
            # Dispatch handling based on action
            if action == "generate":
                return self._generate_context(
                    team_name, mode, stages, memory_types, output_format,
                    save_results, project_scope, memory_importance, 
                    max_memory_items, tags_filter, **kwargs
                )
            elif action == "list_modes":
                return self._list_available_modes()
            elif action == "list_stages":
                return self._list_available_stages()
            elif action == "list_memory_types":
                return self._list_memory_types()
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
    
    def _generate_context(self, team_name: str, mode: str, stages: str, 
                         memory_types: str, output_format: str, save_results: bool,
                         project_scope: str, memory_importance: int,
                         max_memory_items: int, tags_filter: str,
                         user_message: str = None, **kwargs) -> CommandResult:
        """Generate team context"""
        try:
            # Parse mode
            context_mode = self._parse_mode(mode)
            if not context_mode:
                return CommandResult(
                    success=False,
                    message=f"Invalid mode: {mode}. Valid modes: memory_only, framework_only, hybrid",
                    error="INVALID_MODE"
                )
            
            # Create context processor
            processor = ContextProcessor(self.base_path)
            
            # Create configuration based on mode
            config = self._create_config(
                team_name, context_mode, stages, memory_types,
                project_scope, memory_importance, max_memory_items, tags_filter
            )
            
            # Generate context
            context = processor.generate_context(config, user_message)
            
            # Prepare return data
            result_data = {
                'team_name': context.team_name,
                'mode': context.mode.value,
                'content_length': len(context.content),
                'source_memories': context.source_memories,
                'framework_stages': context.framework_stages,
                'generation_time': context.generation_time,
                'metadata': context.metadata
            }
            
            # Save results (if needed)
            if save_results:
                saved_path = self._save_context_result(context, output_format)
                result_data['saved_to'] = str(saved_path)
            
            # Format output
            if output_format == "json":
                result_data['content'] = context.content
            
            return CommandResult(
                success=True,
                message=f"Successfully generated {context.mode.value} context for team '{team_name}'",
                data=result_data
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Context generation failed: {str(e)}",
                error=str(e)
            )
    
    def _parse_mode(self, mode: str) -> Optional[ContextMode]:
        """Parse generation mode"""
        mode_mapping = {
            'memory_only': ContextMode.MEMORY_ONLY,
            'memory': ContextMode.MEMORY_ONLY,
            'framework_only': ContextMode.FRAMEWORK_ONLY,
            'framework': ContextMode.FRAMEWORK_ONLY,
            'hybrid': ContextMode.HYBRID,
            'mixed': ContextMode.HYBRID,
            'combined': ContextMode.HYBRID
        }
        return mode_mapping.get(mode.lower())
    
    def _parse_stages(self, stages: str) -> List[str]:
        """Parse stages parameter"""
        if not stages or stages.lower() == "all":
            return ["requirements", "business-model", "solution", "structure", 
                   "tasks", "common-tasks", "constraints"]
        
        stage_names = [name.strip() for name in stages.split(',')]
        
        # Stage name mapping and validation
        valid_stages = {
            'requirements', 'req', 'business-model', 'business', 'biz',
            'solution', 'sol', 'structure', 'arch', 'architecture',
            'tasks', 'task', 'common-tasks', 'common', 'constraints', 'constraint'
        }
        
        # Normalize stage names
        stage_mapping = {
            'req': 'requirements',
            'business': 'business-model',
            'biz': 'business-model',
            'sol': 'solution',
            'arch': 'structure',
            'architecture': 'structure',
            'task': 'tasks',
            'common': 'common-tasks',
            'constraint': 'constraints'
        }
        
        parsed_stages = []
        for stage in stage_names:
            normalized = stage.lower()
            if normalized in valid_stages:
                parsed_stages.append(stage_mapping.get(normalized, normalized))
        
        return list(set(parsed_stages))  # Remove duplicates
    
    def _parse_memory_types(self, memory_types: str) -> List[MemoryType]:
        """Parse memory types"""
        if not memory_types or memory_types.lower() == "all":
            return [MemoryType.ALL]
        
        type_mapping = {
            'declarative': MemoryType.DECLARATIVE,
            'procedural': MemoryType.PROCEDURAL,
            'episodic': MemoryType.EPISODIC,
            'all': MemoryType.ALL
        }
        
        type_names = [name.strip().lower() for name in memory_types.split(',')]
        parsed_types = []
        
        for type_name in type_names:
            if type_name in type_mapping:
                parsed_types.append(type_mapping[type_name])
        
        return parsed_types if parsed_types else [MemoryType.ALL]
    
    def _create_config(self, team_name: str, mode: ContextMode, stages: str,
                      memory_types: str, project_scope: str, memory_importance: int,
                      max_memory_items: int, tags_filter: str) -> ContextGenerationConfig:
        """Create context generation configuration"""
        
        # Parse parameters
        parsed_stages = self._parse_stages(stages)
        parsed_memory_types = self._parse_memory_types(memory_types)
        
        # Handle tags filter
        memory_filters = {}
        if tags_filter:
            tags = [tag.strip() for tag in tags_filter.split(',')]
            memory_filters['tags'] = tags
        
        # Use convenience functions based on mode
        if mode == ContextMode.MEMORY_ONLY:
            return create_memory_only_config(
                team_name=team_name,
                include_memory_types=parsed_memory_types,
                max_memory_items=max_memory_items,
                memory_importance_threshold=memory_importance,
                project_scope=project_scope,
                memory_filters=memory_filters
            )
        elif mode == ContextMode.FRAMEWORK_ONLY:
            return create_framework_only_config(
                team_name=team_name,
                stages=parsed_stages if stages else None
            )
        else:  # HYBRID
            return create_hybrid_config(
                team_name=team_name,
                stages=parsed_stages if stages else None,
                include_memory_types=parsed_memory_types,
                max_memory_items=max_memory_items,
                memory_importance_threshold=memory_importance,
                project_scope=project_scope,
                memory_filters=memory_filters
            )
    
    def _save_context_result(self, context, output_format: str) -> Path:
        """Save context result"""
        team_path = self.get_team_path(context.team_name)
        output_dir = team_path / "context_outputs"
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{context.mode.value}_context"
        
        if output_format == "json":
            file_path = output_dir / f"{filename}.json"
            result_data = {
                'team_name': context.team_name,
                'mode': context.mode.value,
                'content': context.content,
                'source_memories': context.source_memories,
                'framework_stages': context.framework_stages,
                'metadata': context.metadata,
                'generation_time': context.generation_time
            }
            file_path.write_text(
                json.dumps(result_data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        else:  # markdown
            file_path = output_dir / f"{filename}.md"
            context.save_to_file(file_path)
        
        return file_path
    
    def _list_available_modes(self) -> CommandResult:
        """List available generation modes"""
        modes_info = [
            {
                'name': 'memory_only',
                'display_name': 'Memory Only',
                'description': 'Generate context based only on team memories',
                'aliases': ['memory'],
                'use_cases': ['Review team experience', 'View historical decisions', 'Analyze past projects']
            },
            {
                'name': 'framework_only',
                'display_name': 'Framework Only',
                'description': 'Generate context based only on seven-stage framework',
                'aliases': ['framework'],
                'use_cases': ['New project initiation', 'Standardized processes', 'Framework guidance']
            },
            {
                'name': 'hybrid',
                'display_name': 'Hybrid',
                'description': 'Generate comprehensive context combining memories and framework',
                'aliases': ['mixed', 'combined'],
                'use_cases': ['Comprehensive project analysis', 'Experience-based solution design', 'Comprehensive decision support']
            }
        ]
        
        return CommandResult(
            success=True,
            message=f"Available generation modes: {len(modes_info)}",
            data={
                'modes': modes_info,
                'default_mode': 'hybrid',
                'usage_examples': [
                    "team_context generate frontend-team --mode=memory_only",
                    "team_context generate backend-team --mode=framework_only --stages=requirements,solution",
                    "team_context generate data-team --mode=hybrid --memory-types=declarative,procedural"
                ]
            }
        )
    
    def _list_available_stages(self) -> CommandResult:
        """List available framework stages"""
        stages_info = [
            {
                'name': 'requirements',
                'display_name': 'Requirements',
                'description': 'Requirements Anchoring - Extract core problem essence and fundamental goals from requirements description',
                'aliases': ['req']
            },
            {
                'name': 'business-model',
                'display_name': 'Business Model',
                'description': 'Business Model - Build clear business entity relationship model',
                'aliases': ['business', 'biz']
            },
            {
                'name': 'solution',
                'display_name': 'Solution',
                'description': 'Solution - Provide high-level solution strategies and architectural schemes',
                'aliases': ['sol']
            },
            {
                'name': 'structure',
                'display_name': 'Structure',
                'description': 'Structure Definition - Define system technical architecture and component dependencies',
                'aliases': ['arch', 'architecture']
            },
            {
                'name': 'tasks',
                'display_name': 'Tasks',
                'description': 'Task Orchestration - Transform abstract solutions into specific executable implementation tasks',
                'aliases': ['task']
            },
            {
                'name': 'common-tasks',
                'display_name': 'Common Tasks',
                'description': 'Common Tasks - Define unified coding standards and common implementation patterns',
                'aliases': ['common']
            },
            {
                'name': 'constraints',
                'display_name': 'Constraints',
                'description': 'Constraint Control - Define clear boundary conditions and quality standards',
                'aliases': ['constraint']
            }
        ]
        
        return CommandResult(
            success=True,
            message=f"Available framework stages: {len(stages_info)}",
            data={
                'stages': stages_info,
                'default_stages': 'all (includes all 7 stages)',
                'usage_examples': [
                    "team_context generate frontend-team --stages=requirements,solution",
                    "team_context generate backend-team --stages=all",
                    "team_context generate data-team --stages=req,biz,arch"
                ]
            }
        )
    
    def _list_memory_types(self) -> CommandResult:
        """List available memory types"""
        memory_types_info = [
            {
                'name': 'declarative',
                'display_name': 'Declarative Memory',
                'description': 'Declarative Memory - Facts, concepts, knowledge',
                'examples': ['Technical specifications', 'Business rules', 'Design principles']
            },
            {
                'name': 'procedural',
                'display_name': 'Procedural Memory',
                'description': 'Procedural Memory - Skills, processes, methods',
                'examples': ['Workflows', 'Operation steps', 'Best practices']
            },
            {
                'name': 'episodic',
                'display_name': 'Episodic Memory',
                'description': 'Episodic Memory - Specific events, experiences',
                'examples': ['Project experiences', 'Problem solving', 'Decision processes']
            },
            {
                'name': 'all',
                'display_name': 'All Memory Types',
                'description': 'All memory types',
                'examples': ['Includes all above types']
            }
        ]
        
        return CommandResult(
            success=True,
            message=f"Available memory types: {len(memory_types_info)}",
            data={
                'memory_types': memory_types_info,
                'default_type': 'all',
                'usage_examples': [
                    "team_context generate frontend-team --memory-types=declarative",
                    "team_context generate backend-team --memory-types=declarative,procedural",
                    "team_context generate data-team --memory-types=all"
                ]
            }
        )
    
    def get_help_text(self) -> str:
        """Get help text"""
        return """
Team Context Generation Command (team_context)

Usage:
  team_context <action> <team_name> [options]

Actions:
  generate          Generate team context
  list_modes        List available generation modes
  list_stages       List available framework stages
  list_memory_types List available memory types

Generate Options:
  --mode=<mode>               Generation mode (memory_only/framework_only/hybrid, default: hybrid)
  --stages=<stages>           Framework stages, comma-separated or 'all' (default: all)
  --memory-types=<types>      Memory types, comma-separated (declarative/procedural/episodic/all, default: all)
  --output-format=<format>    Output format (markdown/json, default: markdown)
  --save-results=<bool>       Whether to save results (default: true)
  --project-scope=<project>   Project scope filter
  --memory-importance=<int>   Memory importance threshold (1-5, default: 2)
  --max-memory-items=<int>    Maximum number of memory items (default: 50)
  --tags-filter=<tags>        Tags filter, comma-separated

Generation Modes:
  memory_only      Generate context based only on team memories
  framework_only   Generate context based only on seven-stage framework
  hybrid          Generate comprehensive context combining memories and framework (recommended)

Examples:
  # Generate hybrid mode context (default)
  team_context generate frontend-team
  
  # Generate memory-only context
  team_context generate frontend-team --mode=memory_only --memory-types=declarative
  
  # Generate framework-only context
  team_context generate backend-team --mode=framework_only --stages=requirements,solution
  
  # Generate filtered hybrid context
  team_context generate data-team --mode=hybrid --tags-filter=ui,performance --memory-importance=3
  
  # View available options
  team_context list_modes
  team_context list_stages
  team_context list_memory_types

Framework Stages:
  requirements     Requirements Anchoring (aliases: req)
  business-model   Business Model (aliases: business, biz)
  solution         Solution (aliases: sol)
  structure        System Architecture (aliases: arch, architecture)
  tasks            Task Orchestration (aliases: task)
  common-tasks     Common Tasks (aliases: common)
  constraints      Constraints (aliases: constraint)

Memory Types:
  declarative      Declarative Memory - Facts, concepts, knowledge
  procedural       Procedural Memory - Skills, processes, methods
  episodic         Episodic Memory - Specific events, experiences
  all              All memory types
        """.strip() 