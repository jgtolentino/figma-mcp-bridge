from typing import Dict, Any, List
import json
import re

def parse_figma_variables(variables_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Figma variables into standardized token format"""
    tokens = {
        "colors": {},
        "spacing": {},
        "typography": {},
        "borderRadius": {},
        "shadows": {},
        "opacity": {}
    }
    
    if "meta" in variables_data and "variableCollections" in variables_data["meta"]:
        for collection in variables_data["meta"]["variableCollections"].values():
            for mode in collection.get("modes", []):
                for var_id, var_data in collection.get("variableIds", {}).items():
                    _categorize_variable(var_data, mode, tokens)
    
    return tokens

def _categorize_variable(var_data: Dict, mode: Dict, tokens: Dict):
    """Categorize variable into appropriate token category"""
    name = var_data.get("name", "")
    value = mode.get("values", {}).get(var_data.get("id", ""))
    
    if not value:
        return
    
    # Categorize based on name patterns
    name_lower = name.lower()
    
    if any(keyword in name_lower for keyword in ["color", "fill", "stroke", "bg", "background", "text"]):
        tokens["colors"][_format_token_name(name)] = {
            "value": _format_color_value(value),
            "type": "color"
        }
    elif any(keyword in name_lower for keyword in ["spacing", "space", "gap", "padding", "margin"]):
        tokens["spacing"][_format_token_name(name)] = {
            "value": _format_numeric_value(value),
            "type": "dimension"
        }
    elif any(keyword in name_lower for keyword in ["font", "type", "text"]):
        tokens["typography"][_format_token_name(name)] = {
            "value": value,
            "type": "typography"
        }
    elif any(keyword in name_lower for keyword in ["radius", "corner", "rounded"]):
        tokens["borderRadius"][_format_token_name(name)] = {
            "value": _format_numeric_value(value),
            "type": "dimension"
        }
    elif any(keyword in name_lower for keyword in ["shadow", "elevation"]):
        tokens["shadows"][_format_token_name(name)] = {
            "value": _format_shadow_value(value),
            "type": "shadow"
        }
    elif any(keyword in name_lower for keyword in ["opacity", "alpha"]):
        tokens["opacity"][_format_token_name(name)] = {
            "value": value,
            "type": "number"
        }

def _format_token_name(name: str) -> str:
    """Convert Figma variable name to token name format"""
    # Convert to camelCase and remove special characters
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', ' ', name)
    
    # Convert to camelCase
    parts = name.split()
    if parts:
        return parts[0].lower() + ''.join(word.capitalize() for word in parts[1:])
    return name.lower()

def _format_color_value(value: Any) -> str:
    """Format color value to standard format"""
    if isinstance(value, dict):
        if "r" in value and "g" in value and "b" in value:
            r = int(value["r"] * 255)
            g = int(value["g"] * 255)
            b = int(value["b"] * 255)
            a = value.get("a", 1.0)
            
            if a < 1.0:
                return f"rgba({r}, {g}, {b}, {a})"
            return f"#{r:02x}{g:02x}{b:02x}"
    
    return str(value)

def _format_numeric_value(value: Any) -> str:
    """Format numeric value with units"""
    if isinstance(value, (int, float)):
        return f"{value}px"
    return str(value)

def _format_shadow_value(value: Any) -> str:
    """Format shadow value"""
    if isinstance(value, dict):
        x = value.get("x", 0)
        y = value.get("y", 0)
        blur = value.get("blur", 0)
        spread = value.get("spread", 0)
        color = _format_color_value(value.get("color", {"r": 0, "g": 0, "b": 0, "a": 0.1}))
        return f"{x}px {y}px {blur}px {spread}px {color}"
    
    return str(value)

def format_tokens_for_export(tokens: Dict[str, Any]) -> Dict[str, Any]:
    """Format tokens for export to file or API response"""
    formatted = {}
    
    for category, category_tokens in tokens.items():
        if category_tokens:  # Only include non-empty categories
            formatted[category] = {}
            for token_name, token_data in category_tokens.items():
                formatted[category][token_name] = token_data
    
    return formatted

def validate_token_structure(tokens: Dict[str, Any]) -> List[str]:
    """Validate token structure and return list of errors"""
    errors = []
    
    for category, category_tokens in tokens.items():
        if not isinstance(category_tokens, dict):
            errors.append(f"Category '{category}' must be a dictionary")
            continue
        
        for token_name, token_data in category_tokens.items():
            if not isinstance(token_data, dict):
                errors.append(f"Token '{token_name}' in '{category}' must be a dictionary")
                continue
            
            if "value" not in token_data:
                errors.append(f"Token '{token_name}' in '{category}' missing 'value' field")
    
    return errors

def merge_tokens(existing: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge token updates with existing tokens"""
    merged = existing.copy()
    
    for category, category_tokens in updates.items():
        if category not in merged:
            merged[category] = {}
        
        for token_name, token_data in category_tokens.items():
            merged[category][token_name] = token_data
    
    return merged