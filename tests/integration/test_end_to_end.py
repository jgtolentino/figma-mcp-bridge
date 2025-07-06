"""
End-to-end integration tests for Figma MCP Bridge
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
import httpx
from pathlib import Path
import json
import tempfile

# Import modules
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from server.figma_client import FigmaClient
from server.design_token_utils import parse_figma_variables, format_tokens_for_export
from server.style_dictionary_transformer import StyleDictionaryTransformer
from server.component_push import ComponentPusher

class TestEndToEndWorkflow:
    
    @pytest.mark.asyncio
    async def test_complete_token_sync_workflow(self, mock_env_vars, sample_figma_tokens):
        """Test complete workflow: Figma → parse → transform → export"""
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock Figma API response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = sample_figma_tokens
            mock_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Step 1: Fetch from Figma
            client = FigmaClient()
            figma_data = await client.get_file_variables("test_file_id")
            
            # Step 2: Parse Figma variables
            parsed_tokens = parse_figma_variables(figma_data)
            
            # Step 3: Format for export
            formatted_tokens = format_tokens_for_export(parsed_tokens)
            
            # Step 4: Transform to Style Dictionary
            sd_tokens = StyleDictionaryTransformer.figma_to_style_dictionary(formatted_tokens)
            
            # Verify the complete workflow
            assert isinstance(sd_tokens, dict)
            assert len(sd_tokens) > 0
            
            # Check that tokens have Style Dictionary format
            for category, tokens in sd_tokens.items():
                assert isinstance(tokens, dict)
                for token_name, token_data in tokens.items():
                    assert "value" in token_data
                    assert "attributes" in token_data
    
    @pytest.mark.asyncio
    async def test_bidirectional_sync(self, mock_env_vars, sample_design_tokens):
        """Test bidirectional sync: local tokens → Figma → back to local"""
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock responses
            mock_get_response = Mock()
            mock_get_response.raise_for_status.return_value = None
            mock_get_response.json.return_value = {"success": True}
            mock_get_response.status_code = 200
            
            mock_post_response = Mock()
            mock_post_response.raise_for_status.return_value = None
            mock_post_response.json.return_value = {"success": True, "updated_count": 2}
            mock_post_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_get_response
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_post_response
            
            client = FigmaClient()
            
            # Push local tokens to Figma
            result = await client.update_file_variables("test_file_id", sample_design_tokens)
            assert result["success"] is True
            
            # Fetch back from Figma
            fetched_data = await client.get_file_variables("test_file_id")
            assert fetched_data["success"] is True
    
    def test_component_parsing_workflow(self, temp_component_file):
        """Test complete component parsing workflow"""
        
        # Step 1: Parse React component
        component_info = ComponentPusher.parse_react_component(temp_component_file)
        
        # Step 2: Create Figma component spec
        figma_spec = ComponentPusher.create_figma_component_spec(component_info)
        
        # Verify workflow
        assert component_info["name"] == "Button"
        assert "props" in component_info
        assert "variants" in component_info
        
        assert figma_spec["name"] == "Button"
        assert figma_spec["type"] == "COMPONENT"
        assert "componentPropertyDefinitions" in figma_spec
    
    def test_style_dictionary_platform_generation(self, sample_design_tokens):
        """Test generating tokens for different platforms"""
        
        # Transform to Style Dictionary format
        sd_tokens = StyleDictionaryTransformer.figma_to_style_dictionary(sample_design_tokens)
        
        # Generate platform-specific tokens
        ios_tokens = StyleDictionaryTransformer.generate_platform_tokens(sd_tokens, "ios")
        android_tokens = StyleDictionaryTransformer.generate_platform_tokens(sd_tokens, "android")
        
        # Verify platform-specific transformations
        assert ios_tokens != sd_tokens  # Should be transformed
        assert android_tokens != sd_tokens  # Should be transformed
        assert ios_tokens != android_tokens  # Should be different
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, mock_env_vars):
        """Test error handling in the complete workflow"""
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock HTTP error
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPError("API Error")
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            client = FigmaClient()
            
            with pytest.raises(Exception, match="Failed to fetch Figma file"):
                await client.get_file_variables("test_file_id")
    
    def test_file_operations_workflow(self, sample_design_tokens):
        """Test file I/O operations in the workflow"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            
            # Write tokens to file
            token_file = temp_dir / "tokens.json"
            with open(token_file, 'w') as f:
                json.dump(sample_design_tokens, f)
            
            # Read and transform
            with open(token_file, 'r') as f:
                loaded_tokens = json.load(f)
            
            # Transform through Style Dictionary
            sd_tokens = StyleDictionaryTransformer.figma_to_style_dictionary(loaded_tokens)
            
            # Write transformed tokens
            sd_file = temp_dir / "sd_tokens.json"
            with open(sd_file, 'w') as f:
                json.dump(sd_tokens, f)
            
            # Verify files exist and contain expected data
            assert token_file.exists()
            assert sd_file.exists()
            
            with open(sd_file, 'r') as f:
                final_tokens = json.load(f)
            
            assert isinstance(final_tokens, dict)
            assert len(final_tokens) > 0