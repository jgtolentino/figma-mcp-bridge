#!/usr/bin/env python3
"""
Figma Design System Sync CLI
Pull design tokens from Figma or push local tokens back to Figma
"""

import typer
import json
import os
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
import httpx

# Add parent directory to path to import server modules
sys.path.append(str(Path(__file__).parent.parent))

from server.figma_client import FigmaClient
from server.design_token_utils import validate_token_structure, merge_tokens

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

if __name__ == "__main__":
    app()