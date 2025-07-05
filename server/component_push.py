"""
Component push functionality for Figma
Handles pushing React components back to Figma as component sets
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import ast

class ComponentPusher:
    """Push React components to Figma as component sets"""
    
    @staticmethod
    def parse_react_component(file_path: Path) -> Dict[str, Any]:
        """Parse React component file and extract component info"""
        content = file_path.read_text()
        
        # Extract component name
        name_match = re.search(r'export (?:const|function) (\w+)', content)
        component_name = name_match.group(1) if name_match else file_path.stem
        
        # Extract props interface
        props = ComponentPusher._extract_props(content)
        
        # Extract variants from props
        variants = ComponentPusher._extract_variants(props)
        
        # Extract default props
        defaults = ComponentPusher._extract_defaults(content, component_name)
        
        return {
            "name": component_name,
            "type": "COMPONENT",
            "props": props,
            "variants": variants,
            "defaults": defaults,
            "file_path": str(file_path)
        }
    
    @staticmethod
    def _extract_props(content: str) -> Dict[str, Any]:
        """Extract props from TypeScript interface"""
        props = {}
        
        # Find interface definition
        interface_match = re.search(
            r'interface \w+Props\s*\{([^}]+)\}', 
            content, 
            re.DOTALL
        )
        
        if interface_match:
            interface_body = interface_match.group(1)
            
            # Parse each prop
            prop_pattern = r'(\w+)(\?)?\s*:\s*([^;]+);'
            for match in re.finditer(prop_pattern, interface_body):
                prop_name = match.group(1)
                is_optional = bool(match.group(2))
                prop_type = match.group(3).strip()
                
                props[prop_name] = {
                    "type": prop_type,
                    "required": not is_optional,
                    "figmaType": ComponentPusher._map_ts_type_to_figma(prop_type)
                }
        
        return props
    
    @staticmethod
    def _extract_variants(props: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract variant options from props"""
        variants = {}
        
        for prop_name, prop_info in props.items():
            prop_type = prop_info["type"]
            
            # Check for union types (variants)
            if "|" in prop_type:
                # Extract string literal union types
                options = re.findall(r"'([^']+)'|\"([^\"]+)\"", prop_type)
                options = [opt[0] or opt[1] for opt in options]
                
                if options:
                    variants[prop_name] = options
        
        return variants
    
    @staticmethod
    def _extract_defaults(content: str, component_name: str) -> Dict[str, Any]:
        """Extract default prop values"""
        defaults = {}
        
        # Look for default props in function parameters
        default_pattern = rf'{component_name}.*?\(.*?{{([^}}]+)}}'
        match = re.search(default_pattern, content, re.DOTALL)
        
        if match:
            params = match.group(1)
            # Extract default values
            default_value_pattern = r'(\w+)\s*=\s*([^,\s]+)'
            for match in re.finditer(default_value_pattern, params):
                prop_name = match.group(1)
                default_value = match.group(2).strip("'\"")
                defaults[prop_name] = default_value
        
        return defaults
    
    @staticmethod
    def _map_ts_type_to_figma(ts_type: str) -> str:
        """Map TypeScript type to Figma property type"""
        ts_type = ts_type.strip()
        
        if ts_type == "string":
            return "TEXT"
        elif ts_type == "boolean":
            return "BOOLEAN"
        elif ts_type == "React.ReactNode" or ts_type == "ReactNode":
            return "INSTANCE_SWAP"
        elif "|" in ts_type and all(
            re.match(r"['\"].*['\"]", part.strip()) 
            for part in ts_type.split("|")
        ):
            return "VARIANT"
        else:
            return "TEXT"
    
    @staticmethod
    def create_figma_component_spec(component_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create Figma component specification from parsed component"""
        spec = {
            "name": component_info["name"],
            "type": "COMPONENT",
            "componentPropertyDefinitions": {}
        }
        
        # Add properties
        for prop_name, prop_info in component_info["props"].items():
            figma_type = prop_info["figmaType"]
            
            prop_def = {
                "type": figma_type,
                "defaultValue": component_info["defaults"].get(prop_name)
            }
            
            # Add variant options if applicable
            if prop_name in component_info["variants"]:
                prop_def["variantOptions"] = component_info["variants"][prop_name]
            
            spec["componentPropertyDefinitions"][prop_name] = prop_def
        
        return spec
    
    @staticmethod
    def create_component_set(components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a component set from multiple component variants"""
        if not components:
            return {}
        
        # Use first component as base
        base_component = components[0]
        
        component_set = {
            "name": base_component["name"],
            "type": "COMPONENT_SET",
            "componentPropertyDefinitions": {},
            "children": []
        }
        
        # Merge all variant properties
        all_variants = {}
        for component in components:
            for prop_name, options in component.get("variants", {}).items():
                if prop_name not in all_variants:
                    all_variants[prop_name] = set()
                all_variants[prop_name].update(options)
        
        # Create property definitions
        for prop_name, options in all_variants.items():
            component_set["componentPropertyDefinitions"][prop_name] = {
                "type": "VARIANT",
                "variantOptions": list(options)
            }
        
        # Add components as children
        for component in components:
            component_set["children"].append({
                "name": ComponentPusher._generate_variant_name(
                    component["name"], 
                    component.get("defaults", {})
                ),
                "type": "COMPONENT",
                "componentProperties": component.get("defaults", {})
            })
        
        return component_set
    
    @staticmethod
    def _generate_variant_name(base_name: str, properties: Dict[str, Any]) -> str:
        """Generate variant name from properties"""
        parts = [base_name]
        
        for prop, value in properties.items():
            if value:
                parts.append(f"{prop}={value}")
        
        return ", ".join(parts)
    
    @staticmethod
    def scan_component_directory(directory: Path) -> List[Dict[str, Any]]:
        """Scan directory for React components"""
        components = []
        
        # Look for component files
        patterns = ["*.tsx", "*.jsx", "*.ts", "*.js"]
        for pattern in patterns:
            for file_path in directory.glob(f"**/{pattern}"):
                # Skip test files and stories
                if any(skip in file_path.name for skip in [".test.", ".spec.", ".stories."]):
                    continue
                
                # Skip node_modules and build directories
                if any(skip in file_path.parts for skip in ["node_modules", "build", "dist"]):
                    continue
                
                try:
                    component_info = ComponentPusher.parse_react_component(file_path)
                    if component_info["props"]:  # Only include if has props
                        components.append(component_info)
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
        
        return components
    
    @staticmethod
    def group_components_by_base_name(components: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group components by their base name for component sets"""
        groups = {}
        
        for component in components:
            # Extract base name (before variant indicators)
            base_name = re.sub(r'(Primary|Secondary|Large|Small|Default)', '', component["name"])
            base_name = base_name.strip()
            
            if base_name not in groups:
                groups[base_name] = []
            groups[base_name].append(component)
        
        return groups