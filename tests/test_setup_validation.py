"""Validation tests to verify the testing infrastructure is properly set up."""
import sys
from pathlib import Path

import pytest


def test_python_version():
    """Verify Python version is compatible."""
    assert sys.version_info >= (3, 8), "Python 3.8 or higher is required"


def test_project_structure():
    """Verify the project structure is correctly set up."""
    root = Path(__file__).parent.parent
    
    # Check main directories exist
    assert root.exists()
    assert (root / "tests").exists()
    assert (root / "tests" / "unit").exists()
    assert (root / "tests" / "integration").exists()
    
    # Check __init__.py files exist
    assert (root / "tests" / "__init__.py").exists()
    assert (root / "tests" / "unit" / "__init__.py").exists()
    assert (root / "tests" / "integration" / "__init__.py").exists()
    
    # Check configuration files
    assert (root / "pyproject.toml").exists()
    assert (root / ".gitignore").exists()


def test_imports():
    """Verify all main modules can be imported."""
    try:
        import core
        import nbdler
    except ImportError as e:
        pytest.fail(f"Failed to import module: {e}")
    
    # GUI and handler modules require wxPython which is not available on Linux CI
    import sys
    if sys.platform != "linux":
        try:
            import handler
            import gui
        except ImportError as e:
            pytest.fail(f"Failed to import module: {e}")


def test_fixtures_available(temp_dir, mock_config, mock_video_info):
    """Verify pytest fixtures are available and working."""
    # Test temp_dir fixture
    assert temp_dir.exists()
    assert temp_dir.is_dir()
    
    # Test mock_config fixture
    assert isinstance(mock_config, dict)
    assert "download_path" in mock_config
    assert "max_threads" in mock_config
    
    # Test mock_video_info fixture
    assert isinstance(mock_video_info, dict)
    assert "title" in mock_video_info
    assert "url" in mock_video_info


def test_markers_registered():
    """Verify custom markers are registered."""
    # This test will pass if markers are properly configured
    @pytest.mark.unit
    def dummy_unit_test():
        pass
    
    @pytest.mark.integration
    def dummy_integration_test():
        pass
    
    @pytest.mark.slow
    def dummy_slow_test():
        pass


def test_coverage_configured():
    """Verify coverage is properly configured."""
    import coverage
    
    # Coverage should be importable
    assert coverage.__version__


class TestMockingCapabilities:
    """Test that mocking capabilities are working."""
    
    def test_mock_available(self):
        """Verify unittest.mock is available."""
        from unittest.mock import Mock, patch
        
        mock_obj = Mock()
        mock_obj.test_method.return_value = "test"
        assert mock_obj.test_method() == "test"
    
    def test_pytest_mock_available(self, mocker):
        """Verify pytest-mock is available and working."""
        mock_func = mocker.Mock(return_value=42)
        assert mock_func() == 42
    
    def test_patch_decorator(self):
        """Verify patching with decorators works."""
        from unittest.mock import patch
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            import os
            assert os.path.exists("/fake/path") is True


def test_file_system_fixture(mock_file_system):
    """Test the mock file system fixture."""
    # Create a test file
    test_file = mock_file_system["create_file"]("test.txt", "Hello, World!")
    assert test_file.exists()
    assert test_file.read_text() == "Hello, World!"
    
    # Create a test directory
    test_dir = mock_file_system["create_directory"]("test_dir")
    assert test_dir.exists()
    assert test_dir.is_dir()


def test_logging_fixture(capture_logs):
    """Test the logging capture fixture."""
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Test log message")
    
    log_output = capture_logs.getvalue()
    assert "Test log message" in log_output


@pytest.mark.parametrize("value,expected", [
    (1, 1),
    (2, 2),
    (3, 3),
])
def test_parametrize_working(value, expected):
    """Verify pytest parametrize is working."""
    assert value == expected


def test_pytest_commands_configured():
    """Verify pytest commands are properly configured in pyproject.toml."""
    root = Path(__file__).parent.parent
    pyproject_path = root / "pyproject.toml"
    
    content = pyproject_path.read_text()
    
    # Check that test commands are configured
    assert "[tool.poetry.scripts]" in content
    assert 'test = "pytest:main"' in content
    assert 'tests = "pytest:main"' in content
    
    # Check pytest configuration
    assert "[tool.pytest.ini_options]" in content
    assert "--cov=" in content
    assert "--cov-fail-under=0" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])