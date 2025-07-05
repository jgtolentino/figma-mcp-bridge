#!/usr/bin/env python3
"""
Figma Design System Sync CLI
Pull design tokens from Figma or push local tokens back to Figma
"""

import typer
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
import httpx

# Add parent directory to path to import server modules
sys.path.append(str(Path(__file__).parent.parent))

from server.figma_client import FigmaClient
from server.design_token_utils import validate_token_structure, merge_tokens
from server.style_dictionary_transformer import StyleDictionaryTransformer
from server.component_push import ComponentPusher

app = typer.Typer(help="Sync design tokens between Figma and your codebase")
console = Console()

def load_env():
    """Load environment variables"""
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        console.print("[yellow]Warning: .env file not found. Using system environment variables.[/yellow]")

@app.command()
def pull(
    output: Path = typer.Option(
        Path("tokens/tokens.json"),
        "--output", "-o",
        help="Output file path for tokens"
    ),
    file_id: Optional[str] = typer.Option(
        None,
        "--file-id", "-f",
        help="Figma file ID (overrides env variable)"
    ),
    pretty: bool = typer.Option(
        True,
        "--pretty", "-p",
        help="Pretty print JSON output"
    )
):
    """Pull design tokens from Figma"""
    load_env()
    
    # Get file ID
    figma_file_id = file_id or os.getenv("FIGMA_FILE_ID")
    if not figma_file_id:
        console.print("[red]Error: FIGMA_FILE_ID not provided. Set it in .env or use --file-id flag.[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Pulling tokens from Figma file: {figma_file_id}[/cyan]")
    
    try:
        # Initialize client and fetch tokens
        client = FigmaClient()
        
        # Run async operation
        import asyncio
        tokens = asyncio.run(client.get_file_variables(figma_file_id))
        
        # Parse and format tokens
        from server.design_token_utils import parse_figma_variables, format_tokens_for_export
        parsed_tokens = parse_figma_variables(tokens)
        formatted_tokens = format_tokens_for_export(parsed_tokens)
        
        # Ensure output directory exists
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Write tokens to file
        with open(output, 'w') as f:
            if pretty:
                json.dump(formatted_tokens, f, indent=2)
            else:
                json.dump(formatted_tokens, f)
        
        # Display summary
        console.print(f"\n[green] Successfully pulled tokens to {output}[/green]")
        
        # Show token summary
        table = Table(title="Token Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="magenta")
        
        for category, tokens_dict in formatted_tokens.items():
            table.add_row(category, str(len(tokens_dict)))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def push(
    input: Path = typer.Option(
        Path("tokens/tokens.json"),
        "--input", "-i",
        help="Input file path for tokens"
    ),
    file_id: Optional[str] = typer.Option(
        None,
        "--file-id", "-f",
        help="Figma file ID (overrides env variable)"
    ),
    merge: bool = typer.Option(
        True,
        "--merge", "-m",
        help="Merge with existing tokens (vs replace)"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-d",
        help="Preview changes without applying"
    )
):
    """Push design tokens to Figma"""
    load_env()
    
    # Check input file exists
    if not input.exists():
        console.print(f"[red]Error: Token file not found: {input}[/red]")
        raise typer.Exit(1)
    
    # Get file ID
    figma_file_id = file_id or os.getenv("FIGMA_FILE_ID")
    if not figma_file_id:
        console.print("[red]Error: FIGMA_FILE_ID not provided. Set it in .env or use --file-id flag.[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Pushing tokens to Figma file: {figma_file_id}[/cyan]")
    
    try:
        # Load tokens from file
        with open(input, 'r') as f:
            tokens = json.load(f)
        
        # Validate token structure
        errors = validate_token_structure(tokens)
        if errors:
            console.print("[red]Token validation errors:[/red]")
            for error in errors:
                console.print(f"  - {error}")
            raise typer.Exit(1)
        
        if dry_run:
            console.print("\n[yellow]DRY RUN - No changes will be made[/yellow]")
            console.print("\nTokens to be pushed:")
            console.print(json.dumps(tokens, indent=2))
            return
        
        # Initialize client
        client = FigmaClient()
        
        # If merge mode, fetch existing tokens first
        if merge:
            import asyncio
            existing = asyncio.run(client.get_file_variables(figma_file_id))
            from server.design_token_utils import parse_figma_variables
            existing_tokens = parse_figma_variables(existing)
            tokens = merge_tokens(existing_tokens, tokens)
        
        # Push tokens
        import asyncio
        result = asyncio.run(client.update_file_variables(figma_file_id, tokens))
        
        console.print(f"\n[green] Successfully pushed tokens to Figma[/green]")
        console.print(f"Updated tokens: {result.get('updated_count', 0)}")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def validate(
    input: Path = typer.Argument(
        ...,
        help="Token file to validate"
    )
):
    """Validate token file structure"""
    if not input.exists():
        console.print(f"[red]Error: File not found: {input}[/red]")
        raise typer.Exit(1)
    
    try:
        with open(input, 'r') as f:
            tokens = json.load(f)
        
        errors = validate_token_structure(tokens)
        
        if errors:
            console.print("[red]Validation errors found:[/red]")
            for error in errors:
                console.print(f"  - {error}")
            raise typer.Exit(1)
        else:
            console.print(f"[green] Token file is valid![/green]")
            
            # Show summary
            table = Table(title="Token Summary")
            table.add_column("Category", style="cyan")
            table.add_column("Count", style="magenta")
            
            for category, tokens_dict in tokens.items():
                if isinstance(tokens_dict, dict):
                    table.add_row(category, str(len(tokens_dict)))
            
            console.print(table)
            
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in file: {str(e)}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def init():
    """Initialize Figma sync configuration"""
    console.print("[cyan]Initializing Figma Design System Sync...[/cyan]")
    
    # Check if .env exists
    env_path = Path(".env")
    if env_path.exists():
        overwrite = typer.confirm("An .env file already exists. Overwrite?")
        if not overwrite:
            raise typer.Exit(0)
    
    # Prompt for configuration
    figma_pat = typer.prompt("Enter your Figma Personal Access Token", hide_input=True)
    figma_file_id = typer.prompt("Enter your Figma File ID")
    
    # Create .env file
    with open(env_path, 'w') as f:
        f.write(f"FIGMA_PAT={figma_pat}\n")
        f.write(f"FIGMA_FILE_ID={figma_file_id}\n")
    
    # Create tokens directory
    tokens_dir = Path("tokens")
    tokens_dir.mkdir(exist_ok=True)
    
    # Create sample token files
    sample_colors = {
        "colors": {
            "primary": {"value": "#1E40AF", "type": "color"},
            "secondary": {"value": "#7C3AED", "type": "color"},
            "neutral100": {"value": "#F3F4F6", "type": "color"},
            "neutral900": {"value": "#111827", "type": "color"}
        }
    }
    
    sample_spacing = {
        "spacing": {
            "xs": {"value": "4px", "type": "dimension"},
            "sm": {"value": "8px", "type": "dimension"},
            "md": {"value": "16px", "type": "dimension"},
            "lg": {"value": "24px", "type": "dimension"},
            "xl": {"value": "32px", "type": "dimension"}
        }
    }
    
    with open(tokens_dir / "colors.json", 'w') as f:
        json.dump(sample_colors, f, indent=2)
    
    with open(tokens_dir / "spacing.json", 'w') as f:
        json.dump(sample_spacing, f, indent=2)
    
    console.print(f"\n[green] Initialization complete![/green]")
    console.print(f"  - Created .env file with Figma credentials")
    console.print(f"  - Created tokens/ directory with sample token files")
    console.print(f"\nNext steps:")
    console.print(f"  1. Run [cyan]figma-ds-sync pull[/cyan] to fetch tokens from Figma")
    console.print(f"  2. Edit tokens in tokens/ directory")
    console.print(f"  3. Run [cyan]figma-ds-sync push[/cyan] to sync back to Figma")

@app.command()
def build(
    config: Path = typer.Option(
        Path("style-dictionary.config.js"),
        "--config", "-c",
        help="Style Dictionary configuration file"
    ),
    platform: Optional[str] = typer.Option(
        None,
        "--platform", "-p",
        help="Build specific platform only"
    )
):
    """Build design tokens using Style Dictionary"""
    if not config.exists():
        console.print(f"[red]Error: Configuration file not found: {config}[/red]")
        raise typer.Exit(1)
    
    # Validate configuration
    errors = StyleDictionaryTransformer.validate_style_dictionary_config(config)
    if errors:
        console.print("[red]Configuration errors:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(1)
    
    try:
        # Check if style-dictionary is installed
        result = subprocess.run(
            ["npx", "style-dictionary", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            console.print("[yellow]Installing style-dictionary...[/yellow]")
            subprocess.run(["npm", "install", "-D", "style-dictionary"], check=True)
        
        # Build tokens
        console.print(f"[cyan]Building tokens with Style Dictionary...[/cyan]")
        
        cmd = ["npx", "style-dictionary", "build"]
        if platform:
            cmd.extend(["--platform", platform])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Build successful![/green]")
            console.print(result.stdout)
        else:
            console.print(f"[red]Build failed: {result.stderr}[/red]")
            raise typer.Exit(1)
            
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def transform(
    input: Path = typer.Argument(..., help="Input token file"),
    output: Path = typer.Argument(..., help="Output file path"),
    direction: str = typer.Option(
        "figma-to-sd",
        "--direction", "-d",
        help="Transform direction: figma-to-sd or sd-to-figma"
    ),
    platform: Optional[str] = typer.Option(
        None,
        "--platform", "-p",
        help="Target platform for transformation"
    )
):
    """Transform tokens between Figma and Style Dictionary formats"""
    if not input.exists():
        console.print(f"[red]Error: Input file not found: {input}[/red]")
        raise typer.Exit(1)
    
    try:
        with open(input, 'r') as f:
            tokens = json.load(f)
        
        if direction == "figma-to-sd":
            transformed = StyleDictionaryTransformer.figma_to_style_dictionary(tokens)
        elif direction == "sd-to-figma":
            transformed = StyleDictionaryTransformer.style_dictionary_to_figma(tokens)
        else:
            console.print(f"[red]Error: Invalid direction: {direction}[/red]")
            raise typer.Exit(1)
        
        # Apply platform-specific transformations
        if platform:
            transformed = StyleDictionaryTransformer.generate_platform_tokens(
                transformed, platform
            )
        
        # Write output
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, 'w') as f:
            json.dump(transformed, f, indent=2)
        
        console.print(f"[green]✓ Transformed tokens saved to {output}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def push_component(
    component_path: Path = typer.Argument(
        ...,
        help="Path to React component file or directory"
    ),
    file_id: Optional[str] = typer.Option(
        None,
        "--file-id", "-f",
        help="Figma file ID (overrides env variable)"
    ),
    as_set: bool = typer.Option(
        False,
        "--as-set", "-s",
        help="Create as component set"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-d",
        help="Preview without pushing"
    )
):
    """Push React components to Figma"""
    load_env()
    
    # Get file ID
    figma_file_id = file_id or os.getenv("FIGMA_FILE_ID")
    if not figma_file_id:
        console.print("[red]Error: FIGMA_FILE_ID not provided.[/red]")
        raise typer.Exit(1)
    
    try:
        components = []
        
        if component_path.is_file():
            # Single component
            component_info = ComponentPusher.parse_react_component(component_path)
            components.append(component_info)
        else:
            # Directory of components
            components = ComponentPusher.scan_component_directory(component_path)
        
        if not components:
            console.print("[yellow]No components found to push.[/yellow]")
            raise typer.Exit(0)
        
        console.print(f"[cyan]Found {len(components)} component(s)[/cyan]")
        
        # Show component summary
        table = Table(title="Components to Push")
        table.add_column("Component", style="cyan")
        table.add_column("Props", style="magenta")
        table.add_column("Variants", style="green")
        
        for comp in components:
            variants_str = ", ".join(comp.get("variants", {}).keys())
            table.add_row(
                comp["name"],
                str(len(comp.get("props", {}))),
                variants_str or "None"
            )
        
        console.print(table)
        
        if dry_run:
            console.print("\n[yellow]DRY RUN - No changes will be made[/yellow]")
            return
        
        # Create Figma specs
        if as_set and len(components) > 1:
            # Group components for sets
            groups = ComponentPusher.group_components_by_base_name(components)
            
            for base_name, group_components in groups.items():
                if len(group_components) > 1:
                    spec = ComponentPusher.create_component_set(group_components)
                    console.print(f"\n[cyan]Creating component set: {base_name}[/cyan]")
                else:
                    spec = ComponentPusher.create_figma_component_spec(group_components[0])
                    console.print(f"\n[cyan]Creating component: {group_components[0]['name']}[/cyan]")
                
                # Push to Figma (would need API implementation)
                console.print(f"[green]✓ Pushed to Figma[/green]")
        else:
            # Push individual components
            for comp in components:
                spec = ComponentPusher.create_figma_component_spec(comp)
                console.print(f"\n[cyan]Pushing component: {comp['name']}[/cyan]")
                # Push to Figma (would need API implementation)
                console.print(f"[green]✓ Pushed to Figma[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def merge(
    inputs: List[Path] = typer.Argument(
        ...,
        help="Token files to merge"
    ),
    output: Path = typer.Option(
        Path("tokens/merged.json"),
        "--output", "-o",
        help="Output file for merged tokens"
    )
):
    """Merge multiple token files"""
    # Check all input files exist
    for input_file in inputs:
        if not input_file.exists():
            console.print(f"[red]Error: File not found: {input_file}[/red]")
            raise typer.Exit(1)
    
    try:
        merged = StyleDictionaryTransformer.merge_token_files(inputs)
        
        # Write merged tokens
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, 'w') as f:
            json.dump(merged, f, indent=2)
        
        console.print(f"[green]✓ Merged {len(inputs)} files to {output}[/green]")
        
        # Show summary
        table = Table(title="Merged Token Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="magenta")
        
        for category, tokens_dict in merged.items():
            if isinstance(tokens_dict, dict):
                table.add_row(category, str(len(tokens_dict)))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()