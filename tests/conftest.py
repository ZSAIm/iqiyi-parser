"""Shared pytest fixtures and configuration for all tests."""
import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_config():
    """Provide a mock configuration object."""
    return {
        "download_path": "/tmp/downloads",
        "cookies_path": "/tmp/cookies",
        "max_threads": 4,
        "timeout": 30,
        "retry_attempts": 3,
        "chunk_size": 1024 * 1024,
        "user_agent": "TestAgent/1.0",
    }


@pytest.fixture
def mock_video_info():
    """Provide mock video information."""
    return {
        "title": "Test Video",
        "url": "https://example.com/video.mp4",
        "duration": 300,
        "size": 104857600,  # 100MB
        "format": "mp4",
        "resolution": "1080p",
        "site": "example",
    }


@pytest.fixture
def mock_download_info():
    """Provide mock download information."""
    return {
        "url": "https://example.com/video.mp4",
        "file_path": "/tmp/downloads/test_video.mp4",
        "size": 104857600,
        "downloaded": 0,
        "status": "pending",
        "speed": 0,
        "eta": 0,
        "threads": 4,
    }


@pytest.fixture
def mock_cookies():
    """Provide mock cookies for testing."""
    return {
        "bilibili": {
            "SESSDATA": "test_session_data",
            "bili_jct": "test_csrf_token",
        },
        "iqiyi": {
            "P00001": "test_auth_token",
            "P00003": "test_user_id",
        },
        "tencent": {
            "vqq_access_token": "test_access_token",
            "vqq_appid": "test_app_id",
        },
    }


@pytest.fixture
def mock_http_response():
    """Provide a mock HTTP response."""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.text = '{"status": "ok", "data": []}'
    mock_resp.json.return_value = {"status": "ok", "data": []}
    mock_resp.content = b'{"status": "ok", "data": []}'
    return mock_resp


@pytest.fixture
def mock_requests(mock_http_response):
    """Mock the requests library."""
    with patch("requests.get") as mock_get, \
         patch("requests.post") as mock_post, \
         patch("requests.Session") as mock_session:
        
        mock_get.return_value = mock_http_response
        mock_post.return_value = mock_http_response
        
        session_instance = Mock()
        session_instance.get.return_value = mock_http_response
        session_instance.post.return_value = mock_http_response
        mock_session.return_value = session_instance
        
        yield {
            "get": mock_get,
            "post": mock_post,
            "session": mock_session,
            "session_instance": session_instance,
        }


@pytest.fixture
def sample_m3u8_content():
    """Provide sample M3U8 playlist content."""
    return """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:10.0,
segment0.ts
#EXTINF:10.0,
segment1.ts
#EXTINF:10.0,
segment2.ts
#EXT-X-ENDLIST"""


@pytest.fixture
def sample_html_content():
    """Provide sample HTML content for parsing tests."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Test Video Page</title>
</head>
<body>
    <div class="video-container">
        <video src="https://example.com/video.mp4" data-vid="12345"></video>
        <h1 class="video-title">Test Video Title</h1>
        <div class="video-info">
            <span class="duration">05:00</span>
            <span class="views">1,000,000</span>
        </div>
    </div>
</body>
</html>"""


@pytest.fixture
def mock_file_system(temp_dir):
    """Mock file system operations."""
    def create_file(path, content=""):
        file_path = temp_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path
    
    def create_directory(path):
        dir_path = temp_dir / path
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    return {
        "root": temp_dir,
        "create_file": create_file,
        "create_directory": create_directory,
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def capture_logs():
    """Capture log messages during tests."""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    logger = logging.getLogger()
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    yield log_capture
    
    logger.removeHandler(handler)
    logger.setLevel(original_level)


@pytest.fixture
def mock_threading():
    """Mock threading operations for testing."""
    with patch("threading.Thread") as mock_thread_class:
        threads = []
        
        def mock_thread_init(target=None, args=None, kwargs=None, **other_kwargs):
            thread = Mock()
            thread.target = target
            thread.args = args or ()
            thread.kwargs = kwargs or {}
            thread.is_alive.return_value = False
            thread.start.side_effect = lambda: target(*thread.args, **thread.kwargs)
            threads.append(thread)
            return thread
        
        mock_thread_class.side_effect = mock_thread_init
        
        yield {"Thread": mock_thread_class, "threads": threads}


def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )
    config.addinivalue_line(
        "markers", "gui: mark test as requiring GUI components"
    )