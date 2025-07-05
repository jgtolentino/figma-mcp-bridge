from typing import Dict, Any, List, Optional
import re

class ComponentParser:
    """Parse and transform components between Figma and code formats"""
    
    @staticmethod
    def figma_to_react(figma_component: Dict[str, Any]) -> str:
        """Convert Figma component to React component code"""
        name = ComponentParser._format_component_name(figma_component.get("name", "Component"))
        props = ComponentParser._extract_props(figma_component)
        
        # Generate React component
        component_code = f"""import React from 'react';

interface {name}Props {{
{ComponentParser._generate_prop_types(props)}
}}

export const {name}: React.FC<{name}Props> = ({{
{ComponentParser._generate_prop_destructuring(props)}
}}) => {{
  return (
    <div className="{ComponentParser._generate_class_name(name)}">
      {{/* Component implementation */}}
      {ComponentParser._generate_jsx_structure(figma_component)}
    </div>
  );
}};
"""
        return component_code
    
    @staticmethod
    def react_to_figma_spec(react_code: str) -> Dict[str, Any]:
        """Parse React component and generate Figma component spec"""
        # Extract component name
        name_match = re.search(r'export const (\w+):', react_code)
        component_name = name_match.group(1) if name_match else "Component"
        
        # Extract props
        props_match = re.search(r'interface \w+Props \{([^}]+)\}', react_code, re.DOTALL)
        props = {}
        
        if props_match:
            prop_lines = props_match.group(1).strip().split('\n')
            for line in prop_lines:
                prop_match = re.match(r'\s*(\w+)\??\s*:\s*(.+);?', line.strip())
                if prop_match:
                    props[prop_match.group(1)] = {
                        "type": prop_match.group(2).strip(),
                        "required": '?' not in line
                    }
        
        return {
            "name": component_name,
            "type": "COMPONENT",
            "properties": props,
            "description": f"React component {component_name}"
        }
    
    @staticmethod
    def _format_component_name(name: str) -> str:
        """Format Figma component name to valid React component name"""
        # Remove special characters and convert to PascalCase
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', ' ', name)
        return ''.join(word.capitalize() for word in name.split())
    
    @staticmethod
    def _extract_props(figma_component: Dict[str, Any]) -> Dict[str, Any]:
        """Extract component properties from Figma component"""
        props = {}
        
        # Extract from component properties
        if "componentPropertyDefinitions" in figma_component:
            for prop_name, prop_def in figma_component["componentPropertyDefinitions"].items():
                props[prop_name] = {
                    "type": ComponentParser._map_figma_type_to_ts(prop_def.get("type")),
                    "defaultValue": prop_def.get("defaultValue"),
                    "description": prop_def.get("description", "")
                }
        
        return props
    
    @staticmethod
    def _map_figma_type_to_ts(figma_type: str) -> str:
        """Map Figma property type to TypeScript type"""
        type_mapping = {
            "TEXT": "string",
            "BOOLEAN": "boolean",
            "INSTANCE_SWAP": "React.ReactNode",
            "VARIANT": "string"
        }
        return type_mapping.get(figma_type, "any")
    
    @staticmethod
    def _generate_prop_types(props: Dict[str, Any]) -> str:
        """Generate TypeScript prop type definitions"""
        lines = []
        for prop_name, prop_info in props.items():
            optional = "?" if not prop_info.get("required", True) else ""
            comment = f"  /** {prop_info['description']} */" if prop_info.get("description") else ""
            if comment:
                lines.append(comment)
            lines.append(f"  {prop_name}{optional}: {prop_info['type']};")
        return '\n'.join(lines)
    
    @staticmethod
    def _generate_prop_destructuring(props: Dict[str, Any]) -> str:
        """Generate prop destructuring with defaults"""
        prop_names = []
        for prop_name, prop_info in props.items():
            if prop_info.get("defaultValue") is not None:
                prop_names.append(f"{prop_name} = {repr(prop_info['defaultValue'])}")
            else:
                prop_names.append(prop_name)
        return ',\n  '.join(prop_names)
    
    @staticmethod
    def _generate_class_name(component_name: str) -> str:
        """Generate CSS class name from component name"""
        # Convert PascalCase to kebab-case
        return re.sub(r'(?<!^)(?=[A-Z])', '-', component_name).lower()
    
    @staticmethod
    def _generate_jsx_structure(figma_component: Dict[str, Any]) -> str:
        """Generate basic JSX structure from Figma component"""
        # This is a simplified version - real implementation would parse the component tree
        if "children" in figma_component:
            return "{children}"
        return "<span>Component content</span>"

class ComponentSetManager:
    """Manage component sets and variants"""
    
    @staticmethod
    def create_component_set(components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a Figma component set from multiple components"""
        if not components:
            return {}
        
        # Extract common properties
        base_name = ComponentSetManager._extract_base_name(components)
        variants = ComponentSetManager._extract_variants(components)
        
        return {
            "name": base_name,
            "type": "COMPONENT_SET",
            "variants": variants,
            "componentIds": [comp.get("id") for comp in components if comp.get("id")]
        }
    
    @staticmethod
    def _extract_base_name(components: List[Dict[str, Any]]) -> str:
        """Extract common base name from components"""
        if not components:
            return "Component"
        
        names = [comp.get("name", "") for comp in components]
        if not names:
            return "Component"
        
        # Find common prefix
        common_prefix = names[0]
        for name in names[1:]:
            while not name.startswith(common_prefix):
                common_prefix = common_prefix[:-1]
                if not common_prefix:
                    return "Component"
        
        return common_prefix.strip("/ -_")
    
    @staticmethod
    def _extract_variants(components: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract variant properties from components"""
        variants = {}
        
        for comp in components:
            comp_name = comp.get("name", "")
            # Extract variant properties from name (e.g., "Button/Primary/Large")
            parts = comp_name.split("/")
            
            for i, part in enumerate(parts[1:], 1):  # Skip base name
                variant_key = f"property{i}"
                if variant_key not in variants:
                    variants[variant_key] = []
                if part not in variants[variant_key]:
                    variants[variant_key].append(part)
        
        return variants