"""
personAI - Personal AI Assistant
Main application entry point
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, RedirectResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Optional, List
import httpx
import secrets
from finetuning import FineTuningEngine, FineTuningConfig
from connectors.mcp import create_default_mcp_manager
from connectors.llm import create_llm

load_dotenv()

app = FastAPI(
    title="personAI",
    description="Personal AI Assistant for GitHub, Google Drive, and Web",
    version="0.2.0"
)

# Initialize MCP manager
mcp_manager = create_default_mcp_manager()

# Initialize LLM
llm = create_llm()

# GitHub OAuth configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Store OAuth states temporarily (in production, use Redis or similar)
oauth_states = {}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize fine-tuning engine
finetuning_config = FineTuningConfig()
finetuning_engine = FineTuningEngine(finetuning_config)


class Query(BaseModel):
    question: str
    sources: list[str] = ["github", "drive", "web"]
    stream: bool = False


class Response(BaseModel):
    answer: str
    sources: list[dict]
    confidence: float


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "personAI",
        "version": "0.2.0",
        "finetuning_enabled": finetuning_config.enabled
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "read_only_mode": os.getenv("READ_ONLY_MODE", "true").lower() == "true",
        "available_sources": ["github", "drive", "web"],
        "github_oauth_enabled": bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET),
        "finetuning": {
            "enabled": finetuning_config.enabled,
            "auto": finetuning_config.auto_tune,
            "backend": finetuning_config.backend,
            "require_approval": finetuning_config.require_approval
        }
    }


@app.get("/auth/github/device/start")
async def github_device_start():
    """Start GitHub Device Flow"""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/device/code",
            headers={"Accept": "application/json"},
            data={"client_id": GITHUB_CLIENT_ID, "scope": "repo read:user user:email"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to start device flow")
        
        return response.json()


@app.post("/auth/github/device/poll")
async def github_device_poll(device_code: str):
    """Poll for device flow completion"""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }
        )
        
        data = response.json()
        
        # Return the response as-is (includes error codes like authorization_pending)
        if "access_token" in data:
            # Get user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {data['access_token']}",
                    "Accept": "application/json"
                }
            )
            user_data = user_response.json()
            data["user"] = user_data
        
        return data


@app.get("/auth/github")
async def github_auth():
    """Initiate GitHub OAuth flow"""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = True
    
    # Redirect to GitHub OAuth
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&scope=repo,read:user,user:email"
        f"&state={state}"
    )
    
    return {"auth_url": github_auth_url, "state": state}


@app.get("/auth/github/callback")
async def github_callback(code: str, state: str):
    """Handle GitHub OAuth callback"""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    
    # Verify state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Remove used state
    del oauth_states[state]
    
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            }
        )
        
        token_data = token_response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data.get("error_description", "OAuth failed"))
        
        access_token = token_data.get("access_token")
        
        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        
        user_data = user_response.json()
        
        # Redirect back to frontend with token
        redirect_url = f"{FRONTEND_URL}?token={access_token}&user={user_data.get('login')}&name={user_data.get('name', '')}"
        return RedirectResponse(url=redirect_url)


@app.get("/auth/github/user")
async def get_github_user(token: str):
    """Get GitHub user info from token"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return response.json()


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "read_only_mode": os.getenv("READ_ONLY_MODE", "true").lower() == "true",
        "available_sources": ["github", "drive", "web"],
        "finetuning": {
            "enabled": finetuning_config.enabled,
            "auto": finetuning_config.auto_tune,
            "backend": finetuning_config.backend,
            "require_approval": finetuning_config.require_approval
        }
    }


@app.post("/query", response_model=Response)
async def query(q: Query):
    """
    Query your personal data across GitHub, Google Drive, and the web
    
    Args:
        q: Query object containing question and desired sources
        
    Returns:
        Response with answer, sources, and confidence score
    """
    try:
        # Build messages for LLM
        messages = [
            {
                "role": "system",
                "content": "You are PersonAI, a helpful coding assistant. You help students with their code and assignments. Be concise, clear, and educational."
            },
            {
                "role": "user",
                "content": q.question
            }
        ]
        
        # Stream or regular response
        if q.stream:
            async def generate():
                try:
                    async for chunk in llm.stream_chat(messages):
                        yield f"data: {chunk}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    yield f"data: Error: {str(e)}\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # Get response from LLM
            assistant_output = await llm.chat(messages)
            
            # Add interaction to fine-tuning buffer
            if finetuning_config.enabled:
                finetuning_engine.add_interaction(q.question, assistant_output)
            
            return Response(
                answer=assistant_output,
                sources=[],
                confidence=0.8
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/finetune/trigger")
async def trigger_finetuning(num_steps: Optional[int] = None):
    """
    Manually trigger a fine-tuning session
    
    Args:
        num_steps: Number of training steps (defaults to config value)
        
    Returns:
        Training statistics
    """
    if not finetuning_config.enabled:
        raise HTTPException(status_code=400, detail="Fine-tuning is disabled")
    
    if finetuning_config.require_approval:
        # In production, this would check user authentication and approval
        pass
    
    result = finetuning_engine.fine_tune_step(num_steps)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@app.get("/finetune/stats")
async def get_finetuning_stats():
    """Get fine-tuning statistics"""
    if not finetuning_config.enabled:
        return {"enabled": False}
    
    return {
        "enabled": True,
        "stats": finetuning_engine.get_training_stats(),
        "config": {
            "auto": finetuning_config.auto_tune,
            "backend": finetuning_config.backend,
            "learning_rate": finetuning_config.learning_rate,
            "steps_per_session": finetuning_config.steps_per_session
        }
    }


@app.post("/finetune/rollback")
async def rollback_model(checkpoint_name: Optional[str] = None):
    """
    Rollback model to a previous checkpoint
    
    Args:
        checkpoint_name: Name of checkpoint to rollback to (or latest if None)
        
    Returns:
        Success status
    """
    if not finetuning_config.enabled or not finetuning_config.rollback_enabled:
        raise HTTPException(status_code=400, detail="Rollback is disabled")
    
    success = finetuning_engine.rollback(checkpoint_name)
    
    if not success:
        raise HTTPException(status_code=500, detail="Rollback failed")
    
    return {"status": "success", "checkpoint": checkpoint_name or "latest"}


@app.get("/finetune/buffer")
async def get_conversation_buffer():
    """Get current conversation buffer for review"""
    if not finetuning_config.enabled:
        raise HTTPException(status_code=400, detail="Fine-tuning is disabled")
    
    return {
        "messages": finetuning_engine.buffer.messages,
        "training_pairs": finetuning_engine.buffer.get_training_pairs(),
        "buffer_size": len(finetuning_engine.buffer.messages),
        "max_size": finetuning_engine.buffer.max_size
    }


@app.post("/index/github")
async def index_github():
    """Index GitHub repositories for faster querying"""
    # TODO: Implement GitHub indexing
    return {"status": "not_implemented"}


@app.post("/index/drive")
async def index_drive():
    """Index Google Drive for faster querying"""
    # TODO: Implement Drive indexing
    return {"status": "not_implemented"}


# MCP Tool Endpoints
@app.get("/mcp/{server_name}/tools")
async def list_mcp_tools(server_name: str):
    """List available tools from an MCP server"""
    try:
        tools = await mcp_manager.list_tools(server_name)
        return tools
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/{server_name}/call")
async def call_mcp_tool(server_name: str, request: dict):
    """Call a tool on an MCP server"""
    try:
        tool_name = request.get("tool")
        arguments = request.get("arguments", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="tool name is required")
        
        result = await mcp_manager.call_tool(server_name, tool_name, arguments)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    mcp_manager.shutdown()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
