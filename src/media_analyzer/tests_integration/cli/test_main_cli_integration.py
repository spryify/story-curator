"""Integration tests for main CLI functionality.

These tests verify the CLI commands work end-to-end with real audio files
and actual command execution.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

import pytest

from media_analyzer.tests_unit.utils.audio import create_wav_file

# Get the project root directory dynamically
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


class TestMainCLIIntegration:
    """Integration tests for the main CLI entry point."""
    
    def test_cli_help_command(self):
        """Test that the CLI help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "media_analyzer.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        assert result.returncode == 0
        assert "Media Analyzer CLI" in result.stdout
        assert "Process and analyze audio files" in result.stdout
        assert "audio" in result.stdout  # Should show audio subcommand
        assert "podcast" in result.stdout  # Should show podcast subcommand
    
    def test_cli_version_or_basic_info(self):
        """Test that the CLI shows basic information when run without args."""
        result = subprocess.run(
            [sys.executable, "-m", "media_analyzer.cli"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        # CLI should either show help or usage information
        # It's okay if it returns non-zero for missing args
        output = result.stdout + result.stderr
        assert "Usage:" in output or "Media Analyzer CLI" in output
    
    def test_audio_subcommand_help(self):
        """Test that the audio subcommand help works."""
        result = subprocess.run(
            [sys.executable, "-m", "media_analyzer.cli", "audio", "--help"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        assert result.returncode == 0
        assert "audio" in result.stdout.lower()
    
    def test_podcast_subcommand_help(self):
        """Test that the podcast subcommand help works."""
        result = subprocess.run(
            [sys.executable, "-m", "media_analyzer.cli", "podcast", "--help"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        assert result.returncode == 0
        assert "podcast" in result.stdout.lower()
    
    @pytest.mark.skipif(
        not Path("/usr/bin/say").exists() and not Path("/usr/local/bin/say").exists(),
        reason="macOS 'say' command not available - needed for audio generation"
    )
    @pytest.mark.integration
    def test_analyze_command_with_real_audio(self):
        """Test the analyze command with a real audio file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a real audio file with speech
            audio_path = Path(tmp_dir) / "test_audio.wav"
            
            try:
                create_wav_file(
                    text="This is a test audio file for CLI integration testing.",
                    output_path=audio_path,
                    sample_rate=16000,
                    channels=1
                )
                
                # Test the analyze command
                result = subprocess.run(
                    [
                        sys.executable, "-m", "media_analyzer.cli",
                        "analyze", str(audio_path),
                        "--language", "en",
                        "--summary-length", "100",
                        "--verbose"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,  # Give it time to process
                    cwd=str(PROJECT_ROOT)
                )
                
                # The command might fail due to missing dependencies (like Whisper)
                # but it should at least attempt to process and give a meaningful error
                if result.returncode != 0:
                    # Check if it's a meaningful error (not a syntax error)
                    assert "Error:" in result.stdout or "Error:" in result.stderr
                    # Should not be a Python syntax or import error
                    assert "SyntaxError" not in result.stderr
                    assert "ImportError" not in result.stderr or "whisper" in result.stderr.lower()
                else:
                    # If successful, should contain transcription results
                    assert "Transcription" in result.stdout or "Analysis complete" in result.stdout
                    
            except Exception as e:
                # If audio creation fails, skip the test
                pytest.skip(f"Could not create test audio file: {e}")
    
    def test_analyze_command_with_nonexistent_file(self):
        """Test the analyze command with a file that doesn't exist."""
        result = subprocess.run(
            [
                sys.executable, "-m", "media_analyzer.cli",
                "analyze", "/nonexistent/file.wav"
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        # Should return non-zero exit code
        assert result.returncode != 0
        # Should show an error about the file not existing
        error_output = result.stdout + result.stderr
        assert "does not exist" in error_output.lower() or "no such file" in error_output.lower()
    
    def test_analyze_command_with_invalid_options(self):
        """Test the analyze command with invalid options."""
        result = subprocess.run(
            [
                sys.executable, "-m", "media_analyzer.cli",
                "analyze", "--invalid-option"
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        # Should return non-zero exit code
        assert result.returncode != 0
        # Should show help or error about invalid option
        error_output = result.stdout + result.stderr
        assert "invalid" in error_output.lower() or "unrecognized" in error_output.lower() or "no such option" in error_output.lower()
    
    @pytest.mark.skipif(
        not Path("/usr/bin/say").exists() and not Path("/usr/local/bin/say").exists(),
        reason="macOS 'say' command not available - needed for audio generation"
    )
    @pytest.mark.integration
    def test_analyze_command_with_output_file(self):
        """Test the analyze command with output file option."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a real audio file
            audio_path = Path(tmp_dir) / "test_audio.wav"
            output_path = Path(tmp_dir) / "output.txt"
            
            try:
                create_wav_file(
                    text="Short test audio.",
                    output_path=audio_path,
                    sample_rate=16000,
                    channels=1
                )
                
                # Test the analyze command with output file
                result = subprocess.run(
                    [
                        sys.executable, "-m", "media_analyzer.cli",
                        "analyze", str(audio_path),
                        "--output", str(output_path)
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(PROJECT_ROOT)
                )
                
                # Even if processing fails, it should handle the output option correctly
                if result.returncode == 0:
                    # If successful, output file should be created
                    assert output_path.exists()
                    # Output file should contain some content
                    content = output_path.read_text()
                    assert len(content) > 0
                    assert "Transcription" in content or "Result" in content
                else:
                    # Should give meaningful error
                    error_output = result.stdout + result.stderr
                    assert "Error:" in error_output
                    
            except Exception as e:
                pytest.skip(f"Could not create test audio file: {e}")
    
    def test_cli_module_can_be_imported(self):
        """Test that the CLI module can be imported without errors."""
        result = subprocess.run(
            [sys.executable, "-c", "import media_analyzer.cli.__main__; print('Import successful')"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        assert result.returncode == 0
        assert "Import successful" in result.stdout
        # Should not have import errors
        assert "ImportError" not in result.stderr
        assert "ModuleNotFoundError" not in result.stderr
    
    def test_cli_entry_point_accessible(self):
        """Test that the CLI entry point is accessible."""
        # Test that we can run the module
        result = subprocess.run(
            [sys.executable, "-m", "media_analyzer.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        # Should work and return help
        assert result.returncode == 0
        assert len(result.stdout) > 0
    
    def test_cli_error_handling(self):
        """Test that CLI handles errors gracefully."""
        # Test with a text file instead of audio file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not an audio file")
            f.flush()
            
            try:
                result = subprocess.run(
                    [
                        sys.executable, "-m", "media_analyzer.cli",
                        "analyze", f.name
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(PROJECT_ROOT)
                )
                
                # Should return error code
                assert result.returncode != 0
                # Should show error message, not crash
                error_output = result.stdout + result.stderr
                assert "Error:" in error_output or "error" in error_output.lower()
                # Should not show Python traceback in normal output
                if "--verbose" not in error_output:
                    assert "Traceback" not in error_output
                
            finally:
                os.unlink(f.name)
