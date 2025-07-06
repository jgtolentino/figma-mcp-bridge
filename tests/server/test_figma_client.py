"""
Tests for Figma API client
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from server.figma_client import FigmaClient

class TestFigmaClient:
    
    def test_init_without_token_raises_error(self):
        """Test that initializing without FIGMA_PAT raises ValueError"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="FIGMA_PAT environment variable not set"):
                FigmaClient()
    
    def test_init_with_token_succeeds(self, mock_env_vars):
        """Test successful initialization with token"""
        client = FigmaClient()
        assert client.pat == "test_token"
        assert client.base_url == "https://api.figma.com/v1"
        assert "X-Figma-Token" in client.headers
    
    @pytest.mark.asyncio
    async def test_get_file_variables_success(self, mock_env_vars, sample_figma_tokens):
        """Test successful retrieval of file variables"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock the HTTP responses
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = sample_figma_tokens
            mock_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            client = FigmaClient()
            result = await client.get_file_variables("test_file_id")
            
            assert result == sample_figma_tokens
    
    @pytest.mark.asyncio
    async def test_get_file_variables_http_error(self, mock_env_vars):
        """Test handling of HTTP errors"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("HTTP Error")
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            client = FigmaClient()
            
            with pytest.raises(Exception, match="Failed to fetch Figma file"):
                await client.get_file_variables("test_file_id")
    
    @pytest.mark.asyncio
    async def test_update_file_variables_success(self, mock_env_vars, sample_design_tokens):
        """Test successful update of file variables"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"success": True, "updated_count": 2}
            mock_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            client = FigmaClient()
            result = await client.update_file_variables("test_file_id", sample_design_tokens)
            
            assert result["success"] is True
            assert result["updated_count"] == 2
    
    def test_extract_color_value(self, mock_env_vars):
        """Test color value extraction from Figma style"""
        client = FigmaClient()
        
        # Test solid color
        style = {
            "fills": [{"type": "SOLID", "color": {"r": 0.1, "g": 0.4, "b": 0.7, "a": 1.0}}]
        }
        result = client._extract_color_value(style)
        assert result == "#1a67b2"
        
        # Test color with alpha
        style = {
            "fills": [{"type": "SOLID", "color": {"r": 0.1, "g": 0.4, "b": 0.7, "a": 0.5}}]
        }
        result = client._extract_color_value(style)
        assert result == "rgba(25, 102, 178, 0.5)"
    
    def test_extract_text_value(self, mock_env_vars):
        """Test text/typography value extraction"""
        client = FigmaClient()
        
        style = {
            "fontFamily": "Inter",
            "fontWeight": 600,
            "fontSize": 24,
            "lineHeightPx": 32,
            "letterSpacing": 0.1
        }
        
        result = client._extract_text_value(style)
        
        assert result["fontFamily"] == "Inter"
        assert result["fontWeight"] == 600
        assert result["fontSize"] == 24
        assert result["lineHeight"] == 32
        assert result["letterSpacing"] == 0.1