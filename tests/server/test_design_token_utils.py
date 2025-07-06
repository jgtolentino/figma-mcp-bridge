"""
Tests for design token utilities
"""

import pytest
from server.design_token_utils import (
    parse_figma_variables,
    format_tokens_for_export,
    validate_token_structure,
    merge_tokens,
    _format_token_name,
    _format_color_value,
    _format_numeric_value
)

class TestDesignTokenUtils:
    
    def test_parse_figma_variables(self, sample_figma_tokens):
        """Test parsing Figma variables into standardized format"""
        result = parse_figma_variables(sample_figma_tokens)
        
        assert "colors" in result
        assert "spacing" in result
        assert isinstance(result, dict)
    
    def test_format_tokens_for_export(self, sample_design_tokens):
        """Test formatting tokens for export"""
        result = format_tokens_for_export(sample_design_tokens)
        
        assert result == sample_design_tokens
        assert "colors" in result
        assert "spacing" in result
    
    def test_validate_token_structure_valid(self, sample_design_tokens):
        """Test validation of valid token structure"""
        errors = validate_token_structure(sample_design_tokens)
        assert len(errors) == 0
    
    def test_validate_token_structure_invalid(self):
        """Test validation of invalid token structure"""
        invalid_tokens = {
            "colors": {
                "primary": "invalid_structure"  # Should be dict with 'value'
            }
        }
        
        errors = validate_token_structure(invalid_tokens)
        assert len(errors) > 0
        assert "must be a dictionary" in errors[0]
    
    def test_validate_token_structure_missing_value(self):
        """Test validation with missing value field"""
        invalid_tokens = {
            "colors": {
                "primary": {
                    "type": "color"
                    # Missing 'value' field
                }
            }
        }
        
        errors = validate_token_structure(invalid_tokens)
        assert len(errors) > 0
        assert "missing 'value' field" in errors[0]
    
    def test_merge_tokens(self):
        """Test merging multiple token dictionaries"""
        tokens1 = {
            "colors": {
                "primary": {"value": "#1A67B7", "type": "color"}
            }
        }
        
        tokens2 = {
            "colors": {
                "secondary": {"value": "#7C3AED", "type": "color"}
            },
            "spacing": {
                "base": {"value": "16px", "type": "dimension"}
            }
        }
        
        result = merge_tokens(tokens1, tokens2)
        
        assert "colors" in result
        assert "spacing" in result
        assert "primary" in result["colors"]
        assert "secondary" in result["colors"]
        assert "base" in result["spacing"]
    
    def test_format_token_name(self):
        """Test token name formatting"""
        assert _format_token_name("Primary Color") == "primaryColor"
        assert _format_token_name("base-spacing") == "baseSpacing"
        assert _format_token_name("LARGE_SIZE") == "largeSize"
        assert _format_token_name("simple") == "simple"
    
    def test_format_color_value(self):
        """Test color value formatting"""
        # Test RGB dict
        rgb_dict = {"r": 0.1, "g": 0.4, "b": 0.7, "a": 1.0}
        assert _format_color_value(rgb_dict) == "#1a67b2"
        
        # Test RGB dict with alpha
        rgba_dict = {"r": 0.1, "g": 0.4, "b": 0.7, "a": 0.5}
        assert _format_color_value(rgba_dict) == "rgba(25, 102, 178, 0.5)"
        
        # Test string value
        assert _format_color_value("#FF0000") == "#FF0000"
    
    def test_format_numeric_value(self):
        """Test numeric value formatting"""
        assert _format_numeric_value(16) == "16px"
        assert _format_numeric_value(24.5) == "24.5px"
        assert _format_numeric_value("16px") == "16px"