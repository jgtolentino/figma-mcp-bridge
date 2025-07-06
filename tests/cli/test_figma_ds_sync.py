"""
Tests for Figma Design System Sync CLI
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, Mock, AsyncMock
from pathlib import Path
import json
import tempfile

# Import the CLI app - need to handle the import path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from cli.figma_ds_sync import app

runner = CliRunner()

class TestFigmaDSSync:
    
    def test_validate_command_valid_file(self, temp_token_file):
        """Test validate command with valid token file"""
        result = runner.invoke(app, ["validate", str(temp_token_file)])
        
        assert result.exit_code == 0
        assert "Token file is valid!" in result.stdout
    
    def test_validate_command_missing_file(self):
        """Test validate command with missing file"""
        result = runner.invoke(app, ["validate", "nonexistent.json"])
        
        assert result.exit_code == 1
        assert "File not found" in result.stdout
    
    def test_validate_command_invalid_json(self):
        """Test validate command with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            result = runner.invoke(app, ["validate", temp_file])
            assert result.exit_code == 1
            assert "Invalid JSON" in result.stdout
        finally:
            Path(temp_file).unlink()
    
    def test_merge_command(self, temp_token_file):
        """Test merge command with multiple files"""
        # Create second token file
        tokens2 = {
            "spacing": {
                "large": {"value": "32px", "type": "dimension"}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(tokens2, f)
            temp_file2 = f.name
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = Path(temp_dir) / "merged.json"
                
                result = runner.invoke(app, [
                    "merge",
                    str(temp_token_file),
                    temp_file2,
                    "--output", str(output_file)
                ])
                
                assert result.exit_code == 0
                assert "Merged 2 files" in result.stdout
                
                # Check merged content
                with open(output_file) as f:
                    merged = json.load(f)
                
                assert "colors" in merged
                assert "spacing" in merged
                assert "primary" in merged["colors"]
                assert "large" in merged["spacing"]
        finally:
            Path(temp_file2).unlink()
    
    @patch('cli.figma_ds_sync.FigmaClient')
    def test_pull_command_success(self, mock_client_class, mock_env_vars, sample_figma_tokens):
        """Test successful pull command"""
        # Mock the client
        mock_client = Mock()
        mock_client.get_file_variables = AsyncMock(return_value=sample_figma_tokens)
        mock_client_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "pulled_tokens.json"
            
            result = runner.invoke(app, [
                "pull",
                "--output", str(output_file),
                "--file-id", "test_file_id"
            ])
            
            assert result.exit_code == 0
            assert "Successfully pulled tokens" in result.stdout
            assert output_file.exists()
    
    @patch('cli.figma_ds_sync.FigmaClient')
    def test_push_command_success(self, mock_client_class, mock_env_vars, temp_token_file):
        """Test successful push command"""
        # Mock the client
        mock_client = Mock()
        mock_client.update_file_variables = AsyncMock(return_value={"updated_count": 2})
        mock_client_class.return_value = mock_client
        
        result = runner.invoke(app, [
            "push",
            "--input", str(temp_token_file),
            "--file-id", "test_file_id"
        ])
        
        assert result.exit_code == 0
        assert "Successfully pushed tokens" in result.stdout
    
    def test_push_command_missing_file(self, mock_env_vars):
        """Test push command with missing input file"""
        result = runner.invoke(app, [
            "push",
            "--input", "nonexistent.json"
        ])
        
        assert result.exit_code == 1
        assert "Token file not found" in result.stdout
    
    def test_init_command(self):
        """Test init command (interactive, so we'll test the start)"""
        # This test is limited since init is interactive
        # In a real scenario, you'd mock the input prompts
        with patch('typer.prompt') as mock_prompt, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('typer.confirm') as mock_confirm:
            
            mock_exists.return_value = False
            mock_prompt.side_effect = ["test_token", "test_file_id"]
            mock_confirm.return_value = True
            
            result = runner.invoke(app, ["init"])
            
            # The command should start successfully
            assert "Initializing Figma Design System Sync" in result.stdout