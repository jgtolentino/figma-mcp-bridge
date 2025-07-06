"""
Pytest configuration and fixtures for Figma MCP Bridge tests
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import tempfile
import json
import os

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_figma_client():
    """Mock Figma client for testing"""
    client = Mock()
    client.get_file_variables = AsyncMock()
    client.update_file_variables = AsyncMock()
    client.get_file_components = AsyncMock()
    client.close = AsyncMock()
    return client

@pytest.fixture
def sample_figma_tokens():
    """Sample Figma tokens for testing"""
    return {
        "meta": {
            "variableCollections": {
                "collection1": {
                    "modes": [{
                        "name": "Default",
                        "values": {
                            "var1": {"r": 0.1, "g": 0.4, "b": 0.7, "a": 1.0},
                            "var2": 16
                        }
                    }],
                    "variableIds": {
                        "var1": {"id": "var1", "name": "primary-color"},
                        "var2": {"id": "var2", "name": "base-spacing"}
                    }
                }
            }
        }
    }

@pytest.fixture
def sample_design_tokens():
    """Sample design tokens in standard format"""
    return {
        "colors": {
            "primary": {
                "value": "#1A67B7",
                "type": "color",
                "description": "Primary brand color"
            }
        },
        "spacing": {
            "base": {
                "value": "16px",
                "type": "dimension",
                "description": "Base spacing unit"
            }
        }
    }

@pytest.fixture
def temp_token_file(sample_design_tokens):
    """Create a temporary token file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_design_tokens, f)
        temp_file = f.name
    
    yield Path(temp_file)
    
    # Cleanup
    os.unlink(temp_file)

@pytest.fixture
def mock_env_vars():
    """Mock environment variables"""
    env_vars = {
        'FIGMA_PAT': 'test_token',
        'FIGMA_FILE_ID': 'test_file_id'
    }
    
    # Store original values
    original_values = {}
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield env_vars
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value

@pytest.fixture
def sample_react_component():
    """Sample React component code for testing"""
    return '''
import React from 'react';

interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  disabled = false,
  children
}) => {
  return (
    <button
      className={`btn btn-${variant} btn-${size}`}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
'''

@pytest.fixture
def temp_component_file(sample_react_component):
    """Create a temporary React component file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsx', delete=False) as f:
        f.write(sample_react_component)
        temp_file = f.name
    
    yield Path(temp_file)
    
    # Cleanup
    os.unlink(temp_file)