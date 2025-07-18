# Figma MCP Bridge <	

Bi-directional sync between Figma Dev Mode and design systems via MCP (Model Context Protocol) server and Claude agent.

## Overview

The Figma MCP Bridge enables seamless synchronization of design tokens between Figma and your codebase. It provides:

- **Pull**: Fetch design tokens from Figma files
- **Push**: Update Figma with local token changes
- **Transform**: Convert between Figma and standard token formats
- **Automate**: GitHub Actions for continuous sync

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/jgtolentino/figma-mcp-bridge.git
cd figma-mcp-bridge

# Install dependencies
pip install -r server/requirements.txt
```

### 2. Configuration

```bash
# Initialize configuration
python cli/figma_ds_sync.py init

# Or manually create .env file
cat > .env << EOF
FIGMA_PAT=your_figma_personal_access_token
FIGMA_FILE_ID=your_figma_file_id
EOF
```

### 3. Basic Usage

```bash
# Pull tokens from Figma
python cli/figma_ds_sync.py pull

# Push tokens to Figma
python cli/figma_ds_sync.py push

# Validate token structure
python cli/figma_ds_sync.py validate tokens/tokens.json
```

## MCP Server

Start the MCP server to enable API access:

```bash
# Start server
cd server
uvicorn main:app --reload

# Server will be available at http://localhost:8000
```

### API Endpoints

- `GET /` - Health check
- `GET /figma/design-tokens` - Fetch design tokens
- `POST /figma/push` - Push tokens to Figma
- `GET /figma/components` - Fetch component definitions

## CLI Commands

### Pull Command
```bash
python cli/figma_ds_sync.py pull [OPTIONS]

Options:
  -o, --output PATH      Output file path [default: tokens/tokens.json]
  -f, --file-id TEXT     Figma file ID (overrides env)
  -p, --pretty          Pretty print JSON [default: True]
```

### Push Command
```bash
python cli/figma_ds_sync.py push [OPTIONS]

Options:
  -i, --input PATH       Input file path [default: tokens/tokens.json]
  -f, --file-id TEXT     Figma file ID (overrides env)
  -m, --merge           Merge with existing tokens [default: True]
  -d, --dry-run         Preview changes without applying
```

### Build Command (Style Dictionary)
```bash
python cli/figma_ds_sync.py build [OPTIONS]

Options:
  -c, --config PATH      Style Dictionary config [default: style-dictionary.config.js]
  -p, --platform TEXT    Build specific platform only
```

### Transform Command
```bash
python cli/figma_ds_sync.py transform INPUT OUTPUT [OPTIONS]

Options:
  -d, --direction TEXT   Transform direction: figma-to-sd or sd-to-figma
  -p, --platform TEXT    Target platform for transformation
```

### Push Component Command
```bash
python cli/figma_ds_sync.py push-component COMPONENT_PATH [OPTIONS]

Options:
  -f, --file-id TEXT     Figma file ID (overrides env)
  -s, --as-set          Create as component set
  -d, --dry-run         Preview without pushing
```

### Merge Command
```bash
python cli/figma_ds_sync.py merge INPUT_FILES... [OPTIONS]

Options:
  -o, --output PATH      Output file for merged tokens [default: tokens/merged.json]
```

## Token Structure

Tokens should follow this structure:

```json
{
  "colors": {
    "primary": {
      "value": "#1E40AF",
      "type": "color"
    }
  },
  "spacing": {
    "sm": {
      "value": "8px",
      "type": "dimension"
    }
  },
  "typography": {
    "heading": {
      "value": {
        "fontFamily": "Inter",
        "fontSize": 24,
        "fontWeight": 700
      },
      "type": "typography"
    }
  }
}
```

## GitHub Actions

Automatic token sync on push:

1. Add secrets to your GitHub repository:
   - `FIGMA_PAT` - Your Figma Personal Access Token
   - `FIGMA_FILE_ID` - Your Figma file ID

2. Tokens will auto-sync when you push changes to `tokens/` directory

## Pulser Integration

Register with Pulser CLI:

```bash
# In your main repository
:clodrep run figma-agent.yaml

# Use Pulser commands
pulser figma:pull
pulser figma:push
pulser figma:build
pulser figma:transform
```

## Style Dictionary Integration

The bridge includes full Style Dictionary support for multi-platform token generation:

### Supported Platforms
- **Web**: CSS variables, SCSS, JavaScript/TypeScript
- **iOS**: Swift, Objective-C color/font definitions  
- **Android**: XML resources for colors, dimensions, fonts

### Example Workflow
```bash
# 1. Pull tokens from Figma
python cli/figma_ds_sync.py pull

# 2. Transform to Style Dictionary format
python cli/figma_ds_sync.py transform tokens/tokens.json tokens/sd-tokens.json

# 3. Build for all platforms
python cli/figma_ds_sync.py build

# 4. Or build for specific platform
python cli/figma_ds_sync.py build --platform css
```

## Component Push (Beta)

Push React components back to Figma as native components:

```bash
# Push single component
python cli/figma_ds_sync.py push-component src/components/Button.tsx

# Push directory of components
python cli/figma_ds_sync.py push-component src/components/

# Create component set from variants
python cli/figma_ds_sync.py push-component src/components/Button/ --as-set
```

### Supported Component Features
- TypeScript prop extraction
- Variant detection from union types
- Default prop values
- Component documentation

## Development

### Project Structure
```
figma-mcp-bridge/
   server/                 # FastAPI MCP server
      main.py            # API endpoints
      figma_client.py    # Figma API client
      design_token_utils.py  # Token utilities
   cli/                   # CLI tool
      figma_ds_sync.py  # Typer CLI app
   tokens/                # Token files
   .github/workflows/     # GitHub Actions
   figma-agent.yaml      # Claude agent config
```

### Running Tests
```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

## Figma Setup

1. Generate a Personal Access Token:
   - Go to Figma � Settings � Personal access tokens
   - Create new token with file read/write permissions

2. Get your File ID:
   - Open Figma file in browser
   - Copy ID from URL: `figma.com/file/[FILE_ID]/...`

3. Enable Dev Mode:
   - Open file in Figma
   - Toggle Dev Mode in toolbar

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   Error: FIGMA_PAT environment variable not set
   ```
   Solution: Ensure `.env` file exists with valid token

2. **File Not Found**
   ```
   Error: Failed to fetch Figma file
   ```
   Solution: Verify file ID and token permissions

3. **Token Validation Failed**
   ```
   Error: Token 'primary' missing 'value' field
   ```
   Solution: Ensure tokens follow required structure

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Author

Jake A. ([@jgtolentino](https://github.com/jgtolentino))

---

Built with d for the design-to-code community