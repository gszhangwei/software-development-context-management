"""
PromptX RESTful API服务器

提供完整的HTTP API接口，包括：
- 团队管理API
- 记忆管理API
- 上下文生成API
- 协作管理API
- 搜索和分析API
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import asdict

try:
    from fastapi import FastAPI, HTTPException, Depends, Query, Body, Path as PathParam
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from pydantic import BaseModel
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    # 如果没有FastAPI，创建基本的HTTP服务器
    HAS_FASTAPI = False
    print("FastAPI not available, falling back to basic HTTP server")

from ..core.directory_manager import DirectoryManager
from ..core.markdown_engine import MarkdownEngine, MemoryEntry
from ..core.advanced_search import AdvancedSearchEngine, SearchConfig
from ..core.content_optimizer import ContentOptimizer, OptimizationConfig
from ..core.template_engine import TemplateEngine, RenderContext
from ..core.collaboration_manager import CollaborationManager, ShareType, AccessLevel
from ..commands.team_memory_command import TeamMemoryCommand
from ..commands.team_context_command import TeamContextCommand


# Pydantic模型定义（如果有FastAPI）
if HAS_FASTAPI:
    class TeamCreateRequest(BaseModel):
        name: str
        description: str = ""
        members: List[str] = []
    
    class MemoryCreateRequest(BaseModel):
        content: str
        tags: List[str] = []
        project: str = "general"
        importance: int = 3
        memory_type: str = "declarative"
    
    class ContextGenerateRequest(BaseModel):
        stages: List[str] = []
        memory_integration: bool = True
        stage_dependencies: bool = True
        output_format: str = "markdown"
        project_scope: Optional[str] = None
        memory_importance: int = 2
    
    class SearchRequest(BaseModel):
        query: str
        search_types: List[str] = ["exact", "semantic", "tag"]
        max_results: int = 20
        min_relevance: float = 0.1
        include_related: bool = True
        project_filter: Optional[str] = None
        tag_filter: Optional[List[str]] = None
    
    class SharePermissionRequest(BaseModel):
        target_team: str
        share_type: str
        resource_id: str
        access_level: str
        description: str = ""
        expires_in_days: Optional[int] = None
    
    class CollaborationProjectRequest(BaseModel):
        name: str
        description: str
        teams: List[str]


class APIServer:
    """RESTful API服务器"""
    
    def __init__(self, base_path: Path, host: str = "127.0.0.1", port: int = 8000):
        """
        初始化API服务器
        
        Args:
            base_path: 数据基础路径
            host: 服务器主机
            port: 服务器端口
        """
        self.base_path = Path(base_path)
        self.host = host
        self.port = port
        
        # 初始化核心组件
        self.directory_manager = DirectoryManager(base_path)
        self.markdown_engine = MarkdownEngine()
        self.search_engine = AdvancedSearchEngine(base_path)
        self.content_optimizer = ContentOptimizer()
        self.template_engine = TemplateEngine(base_path)
        self.collaboration_manager = CollaborationManager(base_path)
        
        # 初始化命令
        self.memory_command = TeamMemoryCommand()
        self.memory_command.base_path = base_path
        self.context_command = TeamContextCommand()
        self.context_command.base_path = base_path
        
        # 安全设置
        self.security = HTTPBearer() if HAS_FASTAPI else None
        
        if HAS_FASTAPI:
            # 创建FastAPI应用
            self.app = FastAPI(
                title="PromptX Team Context API",
                description="RESTful API for PromptX Team Context System",
                version="1.0.0"
            )
            
            # 配置CORS
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            # 注册路由
            self._register_routes()
        else:
            self.app = None
    
    def _register_routes(self):
        """注册API路由"""
        if not self.app:
            return
        
        # 健康检查
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        # 团队管理API
        @self.app.get("/api/teams")
        async def list_teams():
            """列出所有团队"""
            try:
                teams_dir = self.base_path / "teams"
                if not teams_dir.exists():
                    return {"teams": []}
                
                teams = []
                for team_dir in teams_dir.iterdir():
                    if team_dir.is_dir():
                        config_file = team_dir / "config.json"
                        if config_file.exists():
                            try:
                                config = json.loads(config_file.read_text(encoding='utf-8'))
                                teams.append({
                                    "name": team_dir.name,
                                    "description": config.get("description", ""),
                                    "members": config.get("members", []),
                                    "created_at": config.get("created_at", "")
                                })
                            except:
                                teams.append({"name": team_dir.name})
                
                return {"teams": teams}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/teams")
        async def create_team(request: TeamCreateRequest):
            """创建新团队"""
            try:
                team_path = self.directory_manager.create_team(
                    request.name, request.description, request.members
                )
                return {
                    "message": f"Team '{request.name}' created successfully",
                    "team_path": str(team_path)
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/teams/{team_name}")
        async def get_team_info(team_name: str):
            """获取团队信息"""
            try:
                if not self.directory_manager.team_exists(team_name):
                    raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
                
                team_path = self.directory_manager.get_team_path(team_name)
                config_file = team_path / "config.json"
                
                if config_file.exists():
                    config = json.loads(config_file.read_text(encoding='utf-8'))
                    return config
                else:
                    return {"name": team_name}
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # 记忆管理API
        @self.app.get("/api/teams/{team_name}/memories")
        async def list_memories(team_name: str, project: Optional[str] = Query(None)):
            """列出团队记忆"""
            try:
                result = self.memory_command.execute(
                    team_name, action="list", project=project
                )
                if result.success:
                    return result.data
                else:
                    raise HTTPException(status_code=400, detail=result.message)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/teams/{team_name}/memories")
        async def create_memory(team_name: str, request: MemoryCreateRequest):
            """创建新记忆"""
            try:
                result = self.memory_command.execute(
                    team_name,
                    action="save",
                    content=request.content,
                    tags=",".join(request.tags),
                    project=request.project,
                    importance=request.importance,
                    memory_type=request.memory_type
                )
                if result.success:
                    return {"message": "Memory created successfully", "data": result.data}
                else:
                    raise HTTPException(status_code=400, detail=result.message)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # 搜索API
        @self.app.post("/api/teams/{team_name}/search")
        async def search_memories(team_name: str, request: SearchRequest):
            """搜索团队记忆"""
            try:
                config = SearchConfig(
                    query=request.query,
                    team_name=team_name,
                    search_types=request.search_types,
                    max_results=request.max_results,
                    min_relevance=request.min_relevance,
                    include_related=request.include_related,
                    project_filter=request.project_filter,
                    tag_filter=request.tag_filter
                )
                
                results = self.search_engine.search_memories(config)
                
                return {
                    "results": [result.to_dict() for result in results],
                    "total_count": len(results)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/teams/{team_name}/search/stats")
        async def get_search_stats(team_name: str):
            """获取搜索统计"""
            try:
                stats = self.search_engine.get_search_statistics(team_name)
                return stats
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # 上下文生成API
        @self.app.post("/api/teams/{team_name}/context")
        async def generate_context(team_name: str, request: ContextGenerateRequest):
            """生成团队上下文"""
            try:
                result = self.context_command.execute(
                    team_name,
                    action="generate",
                    stages=",".join(request.stages) if request.stages else "all",
                    memory_integration=request.memory_integration,
                    stage_dependencies=request.stage_dependencies,
                    save_results=True,
                    project_scope=request.project_scope,
                    memory_importance=request.memory_importance
                )
                
                if result.success:
                    return {"message": "Context generated successfully", "data": result.data}
                else:
                    raise HTTPException(status_code=400, detail=result.message)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/teams/{team_name}/context/stages")
        async def list_context_stages(team_name: str):
            """列出可用的上下文阶段"""
            try:
                result = self.context_command.execute(team_name, action="list_stages")
                if result.success:
                    return result.data
                else:
                    raise HTTPException(status_code=400, detail=result.message)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # 协作管理API
        @self.app.post("/api/teams/{team_name}/share")
        async def create_share_permission(team_name: str, request: SharePermissionRequest):
            """创建共享权限"""
            try:
                permission_id = self.collaboration_manager.create_share_permission(
                    source_team=team_name,
                    target_team=request.target_team,
                    share_type=ShareType(request.share_type),
                    resource_id=request.resource_id,
                    access_level=AccessLevel(request.access_level),
                    created_by="api_user",  # 在实际应用中应该从认证信息获取
                    description=request.description,
                    expires_in_days=request.expires_in_days
                )
                
                return {
                    "message": "Share permission created successfully",
                    "permission_id": permission_id
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/teams/{team_name}/shared")
        async def get_shared_resources(team_name: str, share_type: Optional[str] = Query(None)):
            """获取共享资源"""
            try:
                share_type_enum = ShareType(share_type) if share_type else None
                resources = self.collaboration_manager.get_shared_resources(team_name, share_type_enum)
                return {"shared_resources": resources}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/collaboration/projects")
        async def create_collaboration_project(request: CollaborationProjectRequest):
            """创建协作项目"""
            try:
                project_id = self.collaboration_manager.create_collaboration_project(
                    name=request.name,
                    description=request.description,
                    owner_team=request.teams[0] if request.teams else "",
                    teams=request.teams,
                    created_by="api_user"
                )
                
                return {
                    "message": "Collaboration project created successfully",
                    "project_id": project_id
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/collaboration/analytics")
        async def get_collaboration_analytics(team: Optional[str] = Query(None)):
            """获取协作分析"""
            try:
                analytics = self.collaboration_manager.get_collaboration_analytics(team)
                return analytics
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # 模板管理API
        @self.app.get("/api/templates")
        async def list_templates():
            """列出所有模板"""
            try:
                templates = self.template_engine.list_templates()
                template_info = []
                for template_name in templates:
                    info = self.template_engine.get_template_info(template_name)
                    if info:
                        template_info.append(info)
                
                return {"templates": template_info}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/templates/{template_name}")
        async def get_template_info(template_name: str):
            """获取模板信息"""
            try:
                info = self.template_engine.get_template_info(template_name)
                if info:
                    return info
                else:
                    raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # 内容优化API
        @self.app.post("/api/optimize")
        async def optimize_content(content: str = Body(..., embed=True)):
            """优化内容"""
            try:
                config = OptimizationConfig()
                optimized_content, analysis = self.content_optimizer.optimize_content(content, config)
                
                return {
                    "optimized_content": optimized_content,
                    "analysis": analysis.to_dict()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # 系统信息API
        @self.app.get("/api/system/info")
        async def get_system_info():
            """获取系统信息"""
            try:
                teams_count = len([d for d in (self.base_path / "teams").iterdir() if d.is_dir()]) if (self.base_path / "teams").exists() else 0
                
                return {
                    "system_info": {
                        "version": "1.0.0",
                        "base_path": str(self.base_path),
                        "teams_count": teams_count,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start_server(self):
        """启动服务器"""
        if not HAS_FASTAPI:
            print("FastAPI not available. Please install fastapi and uvicorn:")
            print("pip install fastapi uvicorn")
            return
        
        if not self.app:
            print("API server not initialized")
            return
        
        print(f"Starting PromptX API server on {self.host}:{self.port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    def run_server(self):
        """运行服务器（同步方式）"""
        if not HAS_FASTAPI:
            print("FastAPI not available. Please install fastapi and uvicorn:")
            print("pip install fastapi uvicorn")
            return
        
        asyncio.run(self.start_server())


# 简单的HTTP服务器实现（如果没有FastAPI）
if not HAS_FASTAPI:
    import http.server
    import socketserver
    import urllib.parse
    import threading
    
    class SimpleAPIHandler(http.server.BaseHTTPRequestHandler):
        """简单的API处理器"""
        
        def __init__(self, *args, api_server=None, **kwargs):
            self.api_server = api_server
            super().__init__(*args, **kwargs)
        
        def do_GET(self):
            """处理GET请求"""
            try:
                parsed_path = urllib.parse.urlparse(self.path)
                path = parsed_path.path
                
                if path == "/health":
                    response = {"status": "healthy", "timestamp": datetime.now().isoformat()}
                elif path == "/api/system/info":
                    response = {"message": "Simple HTTP server running", "timestamp": datetime.now().isoformat()}
                else:
                    response = {"error": "Endpoint not found"}
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                    return
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"error": str(e)}
                self.wfile.write(json.dumps(response).encode())
        
        def do_POST(self):
            """处理POST请求"""
            self.send_response(501)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"error": "POST not implemented in simple server"}
            self.wfile.write(json.dumps(response).encode())
    
    class SimpleAPIServer:
        """简单的API服务器"""
        
        def __init__(self, base_path: Path, host: str = "127.0.0.1", port: int = 8000):
            self.base_path = base_path
            self.host = host
            self.port = port
            self.server = None
        
        def run_server(self):
            """运行简单服务器"""
            handler = lambda *args, **kwargs: SimpleAPIHandler(*args, api_server=self, **kwargs)
            
            with socketserver.TCPServer((self.host, self.port), handler) as httpd:
                print(f"Simple HTTP server running on {self.host}:{self.port}")
                print("Note: For full API functionality, please install FastAPI")
                httpd.serve_forever()


def create_api_server(base_path: Path, host: str = "127.0.0.1", port: int = 8000):
    """创建API服务器实例"""
    if HAS_FASTAPI:
        return APIServer(base_path, host, port)
    else:
        return SimpleAPIServer(base_path, host, port) 