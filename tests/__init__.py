# Tests for refiller project
import os
import tempfile

# Set up CONFIG_PATH before any test modules import config
_config_content = """
    username = "testuser"
    password = "testpass"
    base_url = "http://localhost:8000"
    med_id = "med123"
    office = "office_A"
"""
with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
    f.write(_config_content)
    _temp_config_path = f.name

os.environ["CONFIG_PATH"] = _temp_config_path
