# Setup Guide

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Figma account with API access
- Git

## Quick Start

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/jgtolentino/figma-mcp-bridge.git
cd figma-mcp-bridge

# Install Python dependencies
pip install -r server/requirements.txt

# Install Node.js dependencies (for Style Dictionary)
npm install
```

### 2. Configure Figma Access

1. **Get Your Figma Personal Access Token:**
   - Go to [Figma Settings → Personal Access Tokens](https://www.figma.com/settings)
   - Click "Create new token"
   - Give it a descriptive name like "MCP Bridge"
   - Copy the token (you won't see it again!)

2. **Get Your Figma File ID:**
   - Open your Figma file in the browser
   - Copy the file ID from the URL: `figma.com/file/[FILE_ID]/...`

3. **Create Environment File:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```bash
   FIGMA_PAT=your_figma_personal_access_token_here
   FIGMA_FILE_ID=your_figma_file_id_here
   ```

### 3. Initialize and Test

```bash
# Initialize configuration
python cli/figma_ds_sync.py init

# Test connection by pulling tokens
python cli/figma_ds_sync.py pull

# Start the MCP server
python -m uvicorn server.main:app --reload
```

Visit `http://localhost:8000/docs` to see the API documentation.

## Development Setup

### Using Docker

```bash
# Build and start all services
docker-compose up --build

# Run in development mode with hot reload
docker-compose --profile dev up

# Run tests
docker-compose exec figma-mcp-server pytest
```

### Manual Development Setup

```bash
# Install development dependencies
pip install pytest pytest-asyncio black ruff mypy

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests
pytest

# Format code
black .
ruff check --fix .

# Type checking
mypy server/ cli/
```

## Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FIGMA_PAT` | Yes | - | Figma Personal Access Token |
| `FIGMA_FILE_ID` | Yes | - | Target Figma file ID |
| `FIGMA_API_BASE_URL` | No | `https://api.figma.com/v1` | Figma API base URL |

### CLI Configuration

The CLI can be configured via `.env` file or command line arguments:

```bash
# Use specific file ID
python cli/figma_ds_sync.py pull --file-id YOUR_FILE_ID

# Use custom output location
python cli/figma_ds_sync.py pull --output ./my-tokens.json

# Enable pretty printing
python cli/figma_ds_sync.py pull --pretty
```

### Style Dictionary Configuration

Edit `style-dictionary.config.js` to customize token output:

```javascript
module.exports = {
  source: ['tokens/**/*.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      buildPath: 'build/css/',
      files: [{
        destination: 'variables.css',
        format: 'css/variables'
      }]
    }
    // Add more platforms as needed
  }
};
```

## Figma File Setup

### Required Figma File Structure

Your Figma file should have:

1. **Design Tokens as Variables** (recommended)
   - Use Figma's variable system for colors, spacing, etc.
   - Organize into collections by category

2. **Or Design Tokens as Styles** (legacy)
   - Color styles for color tokens
   - Text styles for typography tokens

3. **Components for Component Push**
   - Well-organized component library
   - Use variants for different states
   - Clear naming conventions

### Best Practices

1. **Token Naming:**
   ```
   ✅ Good: colors/primary, spacing/base, typography/heading-large
   ❌ Bad: Blue #1, 16px spacing, Big text
   ```

2. **Component Organization:**
   ```
   ✅ Good: Button/Primary/Large, Card/Elevated/Medium
   ❌ Bad: button-primary-large, card_elevated_medium
   ```

3. **Documentation:**
   - Add descriptions to tokens and components
   - Use consistent naming patterns
   - Group related tokens together

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   Error: FIGMA_PAT environment variable not set
   ```
   **Solution:** Ensure `.env` file exists with valid `FIGMA_PAT`

2. **File Not Found**
   ```
   Error: Failed to fetch Figma file
   ```
   **Solutions:**
   - Verify file ID is correct
   - Check token has access to the file
   - Ensure file isn't in a restricted team

3. **Token Validation Failed**
   ```
   Error: Token 'primary' missing 'value' field
   ```
   **Solution:** Ensure tokens follow the required structure with `value` and `type` fields

4. **Rate Limit Exceeded**
   ```
   Error: Too many requests
   ```
   **Solution:** Wait a minute before retrying, or implement request throttling

### Debug Mode

Enable debug logging:

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Run with verbose output
python cli/figma_ds_sync.py pull --verbose
```

### Testing Connection

```bash
# Test Figma API connection
curl -H "X-Figma-Token: YOUR_TOKEN" \
  "https://api.figma.com/v1/files/YOUR_FILE_ID"

# Test local server
curl http://localhost:8000/

# Test token validation
python cli/figma_ds_sync.py validate tokens.json
```

## IDE Integration

### VS Code

Install recommended extensions:
- Python
- Pylance
- Ruff
- Black Formatter

Add to `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

1. Open the project in PyCharm
2. Configure Python interpreter to use virtual environment
3. Enable Black formatting and Ruff linting
4. Set up run configurations for server and CLI

## Next Steps

1. **Explore Examples:** Check the `examples/` directory for sample components and tokens
2. **Read API Docs:** Visit `http://localhost:8000/docs` for interactive API documentation
3. **Set Up CI/CD:** Use the provided GitHub Actions workflow for automated token syncing
4. **Customize:** Modify Style Dictionary config and agent settings for your needs

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/jgtolentino/figma-mcp-bridge/issues)
- **Discussions:** [GitHub Discussions](https://github.com/jgtolentino/figma-mcp-bridge/discussions)
- **Documentation:** Check the `docs/` directory for detailed guides