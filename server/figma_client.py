import httpx
import os
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class FigmaClient:
    """Client for interacting with Figma REST API"""
    
    def __init__(self):
        self.base_url = "https://api.figma.com/v1"
        self.pat = os.getenv("FIGMA_PAT")
        if not self.pat:
            raise ValueError("FIGMA_PAT environment variable not set")
        
        self.headers = {
            "X-Figma-Token": self.pat,
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)
    
    async def get_file_variables(self, file_id: str) -> Dict[str, Any]:
        """Fetch variables/tokens from Figma file"""
        try:
            # Get file data
            response = await self.client.get(f"{self.base_url}/files/{file_id}")
            response.raise_for_status()
            file_data = response.json()
            
            # Extract variables if using new variable system
            variables_response = await self.client.get(
                f"{self.base_url}/files/{file_id}/variables/local"
            )
            
            if variables_response.status_code == 200:
                return variables_response.json()
            
            # Fallback to styles for older files
            return self._extract_styles_as_tokens(file_data)
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch Figma file: {str(e)}")
    
    async def update_file_variables(self, file_id: str, tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Update variables in Figma file"""
        try:
            # Transform tokens to Figma variable format
            figma_variables = self._tokens_to_figma_variables(tokens)
            
            # Post update to Figma
            response = await self.client.post(
                f"{self.base_url}/files/{file_id}/variables",
                json=figma_variables
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to update Figma variables: {str(e)}")
    
    async def get_file_components(self, file_id: str) -> Dict[str, Any]:
        """Fetch component definitions from Figma file"""
        try:
            response = await self.client.get(f"{self.base_url}/files/{file_id}/components")
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch Figma components: {str(e)}")
    
    def _extract_styles_as_tokens(self, file_data: Dict) -> Dict[str, Any]:
        """Extract styles as design tokens from file data"""
        tokens = {
            "colors": {},
            "typography": {},
            "spacing": {},
            "effects": {}
        }
        
        # Extract color styles
        if "styles" in file_data:
            for style_id, style in file_data["styles"].items():
                if style["styleType"] == "FILL":
                    tokens["colors"][style["name"]] = {
                        "value": self._extract_color_value(style),
                        "description": style.get("description", "")
                    }
                elif style["styleType"] == "TEXT":
                    tokens["typography"][style["name"]] = {
                        "value": self._extract_text_value(style),
                        "description": style.get("description", "")
                    }
        
        return tokens
    
    def _extract_color_value(self, style: Dict) -> str:
        """Extract color value from style"""
        # This is simplified - real implementation would handle gradients, opacity, etc.
        if "fills" in style and style["fills"]:
            fill = style["fills"][0]
            if fill["type"] == "SOLID":
                color = fill["color"]
                r = int(color["r"] * 255)
                g = int(color["g"] * 255)
                b = int(color["b"] * 255)
                a = color.get("a", 1.0)
                
                if a < 1.0:
                    return f"rgba({r}, {g}, {b}, {a})"
                return f"#{r:02x}{g:02x}{b:02x}"
        
        return "#000000"
    
    def _extract_text_value(self, style: Dict) -> Dict[str, Any]:
        """Extract typography values from style"""
        return {
            "fontFamily": style.get("fontFamily", "Inter"),
            "fontWeight": style.get("fontWeight", 400),
            "fontSize": style.get("fontSize", 16),
            "lineHeight": style.get("lineHeightPx", 24),
            "letterSpacing": style.get("letterSpacing", 0)
        }
    
    def _tokens_to_figma_variables(self, tokens: Dict) -> Dict[str, Any]:
        """Convert design tokens to Figma variable format"""
        # This would convert token format to Figma's variable API format
        # Simplified for now
        return {
            "variableCollections": [{
                "name": "Design Tokens",
                "modes": [{
                    "name": "Default",
                    "variables": tokens
                }]
            }]
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()