# Figma MCP Bridge API Documentation

## Overview

The Figma MCP Bridge provides a RESTful API for synchronizing design tokens between Figma and your codebase. The API is built with FastAPI and follows OpenAPI 3.0 specifications.

## Base URL

```
http://localhost:8000
```

## Authentication

All requests to the Figma API require authentication via environment variables:

- `FIGMA_PAT`: Your Figma Personal Access Token
- `FIGMA_FILE_ID`: Target Figma file ID

## Endpoints

### Health Check

#### `GET /`

Returns the API status and version information.

**Response:**
```json
{
  "name": "Figma MCP Bridge",
  "version": "1.0.0",
  "status": "active"
}
```

---

### Design Tokens

#### `GET /figma/design-tokens`

Fetch all design tokens from the configured Figma file.

**Parameters:**
- None (uses `FIGMA_FILE_ID` from environment)

**Response:**
```json
{
  "colors": {
    "primary": {
      "value": "#1E40AF",
      "type": "color",
      "description": "Primary brand color"
    }
  },
  "spacing": {
    "base": {
      "value": "16px",
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

**Error Responses:**
- `400`: FIGMA_FILE_ID not configured
- `500`: Failed to fetch from Figma API

---

#### `POST /figma/push`

Push design tokens to Figma file.

**Request Body:**
```json
{
  "colors": {
    "primary": {
      "value": "#1E40AF",
      "type": "color"
    }
  },
  "spacing": {
    "base": {
      "value": "16px",
      "type": "dimension"
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Tokens synced to Figma",
  "updated_count": 12
}
```

**Error Responses:**
- `400`: FIGMA_FILE_ID not configured or invalid token structure
- `500`: Failed to update Figma file

---

### Components

#### `GET /figma/components`

Fetch component definitions from Figma file.

**Response:**
```json
{
  "components": [
    {
      "id": "123:456",
      "name": "Button/Primary",
      "type": "COMPONENT",
      "componentProperties": {
        "variant": {
          "type": "VARIANT",
          "options": ["primary", "secondary"]
        }
      }
    }
  ]
}
```

---

## CLI Integration

The API can also be accessed via the CLI tool:

```bash
# Pull tokens
python cli/figma_ds_sync.py pull

# Push tokens
python cli/figma_ds_sync.py push

# Validate tokens
python cli/figma_ds_sync.py validate tokens.json
```

## Error Handling

All endpoints return structured error responses:

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-01-06T10:30:00Z"
}
```

Common error codes:
- `FIGMA_AUTH_ERROR`: Invalid or missing Figma token
- `FIGMA_FILE_NOT_FOUND`: File ID not found or inaccessible
- `TOKEN_VALIDATION_ERROR`: Invalid token structure
- `RATE_LIMIT_EXCEEDED`: Too many requests to Figma API

## Rate Limits

The API respects Figma's rate limits:
- 100 requests per minute per token
- Automatic retry with exponential backoff

## Examples

### Python

```python
import httpx

# Fetch design tokens
async with httpx.AsyncClient() as client:
    response = await client.get("http://localhost:8000/figma/design-tokens")
    tokens = response.json()
    print(tokens)

# Push tokens
tokens_to_push = {
    "colors": {
        "primary": {"value": "#1E40AF", "type": "color"}
    }
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/figma/push",
        json=tokens_to_push
    )
    result = response.json()
    print(f"Updated {result['updated_count']} tokens")
```

### JavaScript

```javascript
// Fetch design tokens
const response = await fetch('http://localhost:8000/figma/design-tokens');
const tokens = await response.json();
console.log(tokens);

// Push tokens
const tokensTopush = {
  colors: {
    primary: { value: '#1E40AF', type: 'color' }
  }
};

const pushResponse = await fetch('http://localhost:8000/figma/push', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(tokensToPush)
});

const result = await pushResponse.json();
console.log(`Updated ${result.updated_count} tokens`);
```

### cURL

```bash
# Fetch tokens
curl -X GET "http://localhost:8000/figma/design-tokens" \
  -H "accept: application/json"

# Push tokens
curl -X POST "http://localhost:8000/figma/push" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "colors": {
      "primary": {"value": "#1E40AF", "type": "color"}
    }
  }'
```

## OpenAPI Schema

The complete OpenAPI schema is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`