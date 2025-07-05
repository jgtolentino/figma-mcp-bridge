"""
Style Dictionary transformer for Figma tokens
Converts between Figma format and Style Dictionary format
"""

import json
from typing import Dict, Any, List
from pathlib import Path

class StyleDictionaryTransformer:
    """Transform tokens between Figma and Style Dictionary formats"""
    
    @staticmethod
    def figma_to_style_dictionary(figma_tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Figma tokens to Style Dictionary format"""
        sd_tokens = {}
        
        for category, tokens in figma_tokens.items():
            sd_tokens[category] = {}
            
            for token_name, token_data in tokens.items():
                # Transform token structure
                sd_token = {
                    "value": token_data.get("value"),
                    "type": token_data.get("type", category),
                }
                
                # Add optional fields
                if "description" in token_data:
                    sd_token["description"] = token_data["description"]
                
                # Add metadata for Style Dictionary
                sd_token["attributes"] = {
                    "category": category,
                    "type": token_data.get("type", category),
                    "item": token_name
                }
                
                # Handle complex values
                if isinstance(token_data.get("value"), dict):
                    sd_token = StyleDictionaryTransformer._transform_complex_value(
                        sd_token, token_data["value"], category
                    )
                
                sd_tokens[category][token_name] = sd_token
        
        return sd_tokens
    
    @staticmethod
    def style_dictionary_to_figma(sd_tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Style Dictionary tokens to Figma format"""
        figma_tokens = {}
        
        for category, tokens in sd_tokens.items():
            figma_tokens[category] = {}
            
            for token_name, token_data in tokens.items():
                figma_token = {
                    "value": token_data.get("value"),
                    "type": token_data.get("type", category)
                }
                
                if "description" in token_data:
                    figma_token["description"] = token_data["description"]
                
                figma_tokens[category][token_name] = figma_token
        
        return figma_tokens
    
    @staticmethod
    def _transform_complex_value(token: Dict, value: Any, category: str) -> Dict:
        """Transform complex values based on category"""
        if category == "typography":
            # Transform typography tokens
            token["value"] = {
                "fontFamily": value.get("fontFamily", "Inter"),
                "fontWeight": value.get("fontWeight", 400),
                "fontSize": value.get("fontSize", 16),
                "lineHeight": value.get("lineHeight", 1.5),
                "letterSpacing": value.get("letterSpacing", 0)
            }
        elif category == "shadows":
            # Transform shadow tokens
            if isinstance(value, list):
                token["value"] = value
            else:
                token["value"] = [{
                    "x": value.get("x", 0),
                    "y": value.get("y", 0),
                    "blur": value.get("blur", 0),
                    "spread": value.get("spread", 0),
                    "color": value.get("color", "#000000"),
                    "type": value.get("type", "dropShadow")
                }]
        elif category == "borderRadius":
            # Ensure border radius has units
            if isinstance(value, (int, float)):
                token["value"] = f"{value}px"
        
        return token
    
    @staticmethod
    def generate_platform_tokens(tokens: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Generate platform-specific token transformations"""
        platform_tokens = tokens.copy()
        
        if platform == "ios":
            # iOS-specific transformations
            for category, category_tokens in platform_tokens.items():
                for token_name, token_data in category_tokens.items():
                    if category == "colors" and isinstance(token_data["value"], str):
                        # Convert hex to UIColor format
                        token_data["value"] = StyleDictionaryTransformer._hex_to_uicolor(
                            token_data["value"]
                        )
        
        elif platform == "android":
            # Android-specific transformations
            for category, category_tokens in platform_tokens.items():
                for token_name, token_data in category_tokens.items():
                    if category == "colors" and isinstance(token_data["value"], str):
                        # Ensure Android color format
                        if token_data["value"].startswith("#"):
                            # Add alpha if needed
                            if len(token_data["value"]) == 7:
                                token_data["value"] = "#FF" + token_data["value"][1:]
        
        return platform_tokens
    
    @staticmethod
    def _hex_to_uicolor(hex_color: str) -> Dict[str, float]:
        """Convert hex color to UIColor components"""
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            a = 1.0
        elif len(hex_color) == 8:
            a = int(hex_color[0:2], 16) / 255.0
            r = int(hex_color[2:4], 16) / 255.0
            g = int(hex_color[4:6], 16) / 255.0
            b = int(hex_color[6:8], 16) / 255.0
        else:
            return {"r": 0, "g": 0, "b": 0, "a": 1}
        
        return {
            "r": round(r, 3),
            "g": round(g, 3),
            "b": round(b, 3),
            "a": round(a, 3)
        }
    
    @staticmethod
    def merge_token_files(token_files: List[Path]) -> Dict[str, Any]:
        """Merge multiple token files into one"""
        merged = {}
        
        for file_path in token_files:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    file_tokens = json.load(f)
                    
                    for category, tokens in file_tokens.items():
                        if category not in merged:
                            merged[category] = {}
                        merged[category].update(tokens)
        
        return merged
    
    @staticmethod
    def validate_style_dictionary_config(config_path: Path) -> List[str]:
        """Validate Style Dictionary configuration"""
        errors = []
        
        if not config_path.exists():
            errors.append(f"Configuration file not found: {config_path}")
            return errors
        
        try:
            # For JS config files, we'll do basic validation
            config_content = config_path.read_text()
            
            required_fields = ["source", "platforms"]
            for field in required_fields:
                if field not in config_content:
                    errors.append(f"Missing required field: {field}")
            
        except Exception as e:
            errors.append(f"Failed to read configuration: {str(e)}")
        
        return errors