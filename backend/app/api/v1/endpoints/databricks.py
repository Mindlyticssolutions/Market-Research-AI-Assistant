"""
Databricks Integration Endpoints
"""
import httpx
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()


class ClusterInfo(BaseModel):
    cluster_id: str
    cluster_name: str
    state: str
    driver_type: Optional[str] = None
    worker_type: Optional[str] = None
    num_workers: Optional[int] = None


class ExecuteRequest(BaseModel):
    cluster_id: str
    code: str
    language: str = "python"


class ExecutionResult(BaseModel):
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
    plot: Optional[str] = None # Base64 encoded image


async def get_databricks_client():
    if not settings.DATABRICKS_WORKSPACE_URL or not settings.DATABRICKS_TOKEN:
        raise HTTPException(status_code=500, detail="Databricks configuration missing")
    
    headers = {
        "Authorization": f"Bearer {settings.DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }
    return httpx.AsyncClient(base_url=settings.DATABRICKS_WORKSPACE_URL, headers=headers)


@router.get("/clusters", response_model=List[ClusterInfo])
async def list_clusters():
    """List all available Databricks clusters"""
    if not settings.DATABRICKS_WORKSPACE_URL:
        # Return mock data if not configured (for dev/demo)
        return [
            ClusterInfo(
                cluster_id="mock-cluster-1", 
                cluster_name="Standard Cluster (Dev)", 
                state="RUNNING",
                driver_type="Standard_DS3_v2",
                num_workers=2
            ),
            ClusterInfo(
                cluster_id="mock-cluster-2", 
                cluster_name="ML Cluster (GPU)", 
                state="TERMINATED",
                driver_type="Standard_NC6",
                num_workers=1
            )
        ]

    async with await get_databricks_client() as client:
        response = await client.get("/api/2.0/clusters/list")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch clusters")
        
        clusters = response.json().get("clusters", [])
        return [
            ClusterInfo(
                cluster_id=c["cluster_id"],
                cluster_name=c["cluster_name"],
                state=c["state"],
                driver_type=c.get("driver_node_type_id"),
                num_workers=c.get("num_workers")
            )
            for c in clusters
        ]


@router.post("/clusters/{cluster_id}/start")
async def start_cluster(cluster_id: str):
    """Start a Databricks cluster"""
    if cluster_id.startswith("mock-"):
        return {"message": "Mock cluster started", "cluster_id": cluster_id}

    async with await get_databricks_client() as client:
        response = await client.post("/api/2.0/clusters/start", json={"cluster_id": cluster_id})
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to start cluster")
        return {"message": "Cluster start initiated", "cluster_id": cluster_id}


@router.post("/clusters/{cluster_id}/stop")
async def stop_cluster(cluster_id: str):
    """Terminate (Stop) a Databricks cluster"""
    if cluster_id.startswith("mock-"):
        return {"message": "Mock cluster stopped", "cluster_id": cluster_id}

    async with await get_databricks_client() as client:
        # Note: Databricks API uses 'delete' to terminate a cluster, but the cluster config remains
        response = await client.post("/api/2.0/clusters/delete", json={"cluster_id": cluster_id})
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to stop cluster")
        return {"message": "Cluster termination initiated", "cluster_id": cluster_id}


# Global cache for execution contexts: cluster_id -> context_id
EXECUTION_CONTEXTS: Dict[str, str] = {}


@router.post("/execute", response_model=ExecutionResult)
async def execute_code(request: ExecuteRequest):
    """Execute code on Databricks cluster using stored Execution Context"""
    if request.cluster_id.startswith("mock-"):
        # Improved Mock execution for demo: Actually run the code!
        import asyncio
        import sys
        import io
        import traceback
        
        await asyncio.sleep(0.5)
        
        # Simple sandbox for mock execution
        output_buffer = io.StringIO()
        error_msg = None
        status = "success"
        
        try:
            # Redirect stdout to capture print() calls
            old_stdout = sys.stdout
            sys.stdout = output_buffer
            
            try:
                # Execution environment
                # Note: This is for MOCK/DEMO only. In production, real Databricks is used.
                import numpy as np
                exec_globals = {"__builtins__": __builtins__, "pd": None, "plt": None, "np": np}
                # Try to import for a better mock experience if available
                try: 
                    import pandas as pd
                    exec_globals["pd"] = pd
                except ImportError: pass
                
                # Use AST to handle the last expression (Jupyter/REPL style)
                import ast
                tree = ast.parse(request.code)
                if tree.body and isinstance(tree.body[-1], ast.Expr):
                    last_expr = tree.body.pop()
                    # Execute pre-blocks
                    if tree.body:
                        exec(compile(tree, filename="<ast>", mode="exec"), exec_globals)
                    # Evaluate last expression
                    result_val = eval(compile(ast.Expression(last_expr.value), filename="<ast>", mode="eval"), exec_globals)
                    if result_val is not None:
                        print(result_val)
                else:
                    exec(request.code, exec_globals)
            finally:
                sys.stdout = old_stdout
        except Exception as e:
            status = "error"
            error_msg = str(e)
            traceback.print_exc()
        
        return ExecutionResult(
            status=status,
            output=output_buffer.getvalue() if status == "success" else None,
            error=error_msg
        )

    async with await get_databricks_client() as client:
        context_id = EXECUTION_CONTEXTS.get(request.cluster_id)
        
        # Create context if not exists
        if not context_id:
            ctx_resp = await client.post("/api/1.2/contexts/create", json={
                "language": request.language,
                "clusterId": request.cluster_id
            })
            if ctx_resp.status_code != 200:
                raise HTTPException(status_code=ctx_resp.status_code, detail="Failed to create execution context")
            context_id = ctx_resp.json()["id"]
            EXECUTION_CONTEXTS[request.cluster_id] = context_id

        # Execute command
        cmd_resp = await client.post("/api/1.2/commands/execute", json={
            "language": request.language,
            "clusterId": request.cluster_id,
            "contextId": context_id,
            "command": request.code
        })
        
        # If context invalid (400/404), try ensuring context is valid by recreating it
        if cmd_resp.status_code in [400, 404]:
            # Try creating new context
            ctx_resp = await client.post("/api/1.2/contexts/create", json={
                 "language": request.language,
                 "clusterId": request.cluster_id
            })
            if ctx_resp.status_code == 200:
                 context_id = ctx_resp.json()["id"]
                 EXECUTION_CONTEXTS[request.cluster_id] = context_id
                 # Retry execution
                 cmd_resp = await client.post("/api/1.2/commands/execute", json={
                    "language": request.language,
                    "clusterId": request.cluster_id,
                    "contextId": context_id,
                    "command": request.code
                })

        if cmd_resp.status_code != 200:
             raise HTTPException(status_code=cmd_resp.status_code, detail="Failed to submit command")
             
        command_id = cmd_resp.json()["id"]

        # Poll for results
        import asyncio
        for _ in range(60): # Timeout after 60s
            await asyncio.sleep(1)
            status_resp = await client.get("/api/1.2/commands/status", params={
                "clusterId": request.cluster_id,
                "contextId": context_id,
                "commandId": command_id
            })
            status_data = status_resp.json()
            if status_data["status"] == "Finished":
                result_data = status_data.get("results", {})
                if result_data.get("resultType") == "error":
                     # Format error nicely
                     error_msg = result_data.get("cause", "")
                     return ExecutionResult(status="error", error=error_msg)
                
                # Handle different output types
                plot_data = None
                if result_data.get("resultType") == "image":
                    plot_data = result_data.get("data", "")
                
                output_content = str(result_data.get("data", "")) if result_data.get("resultType") != "image" else ""
                
                # Check for table schema (Pandas/Spark DataFrame display)
                if result_data.get("resultType") == "table":
                     # For now, just convert table data to string representation for the agent
                     # Ideally we'd parse this into a markdown table
                     output_content = str(result_data.get("data", ""))

                return ExecutionResult(
                    status="success", 
                    output=output_content,
                    plot=plot_data
                )
            
            if status_data["status"] in ["Cancelled", "Error"]:
                return ExecutionResult(status="error", error="Execution failed or cancelled")

        return ExecutionResult(status="timeout", error="Execution timed out")


@router.post("/context/destroy")
async def destroy_context(cluster_id: str):
    """Destroy execution context (Restart Kernel)"""
    if cluster_id in EXECUTION_CONTEXTS:
        context_id = EXECUTION_CONTEXTS[cluster_id]
        async with await get_databricks_client() as client:
            await client.post("/api/1.2/contexts/destroy", json={
                "clusterId": cluster_id,
                "contextId": context_id
            })
        del EXECUTION_CONTEXTS[cluster_id]
    return {"message": "Context destroyed"}

@router.post("/mount-storage")
async def mount_storage(cluster_id: str):
    """
    Mount Azure Blob Storage to the Databricks cluster.
    This gives Databricks direct access to the raw files in the 'uploads' container.
    Mount point: /mnt/uploads (or whatever configured in settings)
    """
    if cluster_id.startswith("mock-"):
        return {"message": "Mock storage mounted", "mount_point": "/mnt/mock-uploads"}

    settings_obj = settings # Local reference to avoid confusion
    if not settings_obj.azure_storage_account_name or not settings_obj.azure_storage_account_key:
         raise HTTPException(status_code=400, detail="Azure Storage credentials not configured")

    mount_script = f"""
container_name = "{settings_obj.AZURE_STORAGE_CONTAINER}"
storage_account_name = "{settings_obj.azure_storage_account_name}"
storage_account_key = "{settings_obj.azure_storage_account_key}"
mount_point = f"/mnt/{{container_name}}"

try:
    # Check if already mounted
    if not any(mount.mountPoint == mount_point for mount in dbutils.fs.mounts()):
        print(f"Mounting {{container_name}} to {{mount_point}}...")
        dbutils.fs.mount(
            source = f"wasbs://{{container_name}}@{{storage_account_name}}.blob.core.windows.net",
            mount_point = mount_point,
            extra_configs = {{
                f"fs.azure.account.key.{{storage_account_name}}.blob.core.windows.net": storage_account_key
            }}
        )
        print(f"Successfully mounted at {{mount_point}}")
    else:
        print(f"Already mounted at {{mount_point}}")
        
    # List files to verify
    files = dbutils.fs.ls(mount_point)
    print(f"Verified access. Found {{len(files)}} files.")
    
except Exception as e:
    print(f"Error mounting storage: {{str(e)}}")
"""
    
    # Execute the mount script
    try:
        req = ExecuteRequest(cluster_id=cluster_id, code=mount_script, language="python")
        result = await execute_code(req)
        
        if result.status == "error":
            raise HTTPException(status_code=500, detail=f"Mount failed: {result.error}")
            
        return {"message": "Storage mount command executed", "output": result.output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/execute/stream/{session_id}")
async def stream_execution(websocket: WebSocket, session_id: str):
    """Stream execution output via WebSocket"""
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        code = data.get("code")
        cluster_id = data.get("cluster_id")
        
        if not code or not cluster_id:
            await websocket.send_json({"type": "error", "message": "Missing code or cluster_id"})
            return

        # Mock streaming for demo if no real credentials
        if not settings.DATABRICKS_WORKSPACE_URL or cluster_id.startswith("mock-"):
            await websocket.send_json({"type": "status", "status": "running"})
            lines = code.split("\n")
            for line in lines:
                import asyncio
                await asyncio.sleep(0.5)
                await websocket.send_json({"type": "output", "content": f"> {line}\n"})
            
            await websocket.send_json({"type": "output", "content": "\n[Mock] Execution complete.\n"})
            await websocket.send_json({"type": "status", "status": "finished"})
            return

        # TODO: Implement real streaming via Databricks API polling
        # This effectively wraps the REST polling logic but pushes updates to WS
        
    except WebSocketDisconnect:
        pass
