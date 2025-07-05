from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from .figma_client import FigmaClient
from .design_token_utils import format_tokens_for_export, parse_figma_variables

load_dotenv()

app = FastAPI(title="Figma MCP Bridge", version="1.0.0")
figma_client = FigmaClient()

@app.get("/")
async def root():
    return {"name": "Figma MCP Bridge", "version": "1.0.0", "status": "active"}

@app.get("/figma/design-tokens")
async def fetch_design_tokens():
    """Fetch design tokens from Figma file"""
    try:
        file_id = os.getenv("FIGMA_FILE_ID")
        if not file_id:
            raise HTTPException(status_code=400, detail="FIGMA_FILE_ID not configured")
        
        # Fetch variables from Figma
        variables = await figma_client.get_file_variables(file_id)
        
        # Parse and format tokens
        tokens = parse_figma_variables(variables)
        formatted_tokens = format_tokens_for_export(tokens)
        
        return JSONResponse(content=formatted_tokens)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/figma/push")
async def sync_design_tokens(tokens: dict):
    """Push design tokens back to Figma"""
    try:
        file_id = os.getenv("FIGMA_FILE_ID")
        if not file_id:
            raise HTTPException(status_code=400, detail="FIGMA_FILE_ID not configured")
        
        # Update variables in Figma
        result = await figma_client.update_file_variables(file_id, tokens)
        
        return JSONResponse(content={
            "success": True,
            "message": "Tokens synced to Figma",
            "updated_count": result.get("updated_count", 0)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/figma/components")
async def fetch_components():
    """Fetch component definitions from Figma"""
    try:
        file_id = os.getenv("FIGMA_FILE_ID")
        if not file_id:
            raise HTTPException(status_code=400, detail="FIGMA_FILE_ID not configured")
        
        components = await figma_client.get_file_components(file_id)
        return JSONResponse(content=components)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)