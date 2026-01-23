"""Tests for config module"""

import pytest
import os
import tempfile
from src.config import Config


@pytest.fixture
def valid_config_content():
    """Fixture providing valid config content"""
    return """
        username = "testuser"
        password = "testpass"
        base_url = "http://localhost:8000"
        med_id = "aspirin"
        office = "office_A"
    """


@pytest.fixture
def temp_config_file(valid_config_content):
    """Fixture creating a temporary config file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(valid_config_content)
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


class TestConfigInitialization:
    """Test Config dataclass initialization"""

    def test_config_creation(self):
        """Test creating Config instance with valid values"""
        config = Config(
            username="john_doe",
            password="secret123",
            base_url="http://api.example.com",
            med_id="med123",
            office="office_B",
        )
        assert config.username == "john_doe"
        assert config.password == "secret123"
        assert config.base_url == "http://api.example.com"
        assert config.med_id == "med123"
        assert config.office == "office_B"

    def test_config_with_special_characters(self):
        """Test Config with special characters in values"""
        config = Config(
            username="user@example.com",
            password="p@ssw0rd!#$",
            base_url="https://secure.example.com:8443",
            med_id="MED-123-ABC",
            office="office_123",
        )
        assert config.username == "user@example.com"
        assert config.password == "p@ssw0rd!#$"
        assert config.med_id == "MED-123-ABC"


class TestConfigFromToml:
    """Test Config.from_toml method"""

    def test_from_toml_success(self, temp_config_file):
        """Test successful loading from TOML file"""
        os.environ["CONFIG_PATH"] = temp_config_file
        config = Config.from_toml(temp_config_file)

        assert config.username == "testuser"
        assert config.password == "testpass"
        assert config.base_url == "http://localhost:8000"
        assert config.med_id == "aspirin"
        assert config.office == "office_A"

    def test_from_toml_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist"""
        non_existent_path = "/tmp/non_existent_config_xyz.toml"
        os.environ["CONFIG_PATH"] = non_existent_path

        with pytest.raises(FileNotFoundError, match="Config file not found"):
            Config.from_toml(non_existent_path)

    def test_from_toml_missing_required_field(self):
        """Test ValueError when required field is missing"""
        incomplete_config = """
            username = "testuser"
            password = "testpass"
            base_url = "http://localhost:8000"
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(incomplete_config)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Missing or empty required fields"):
                Config.from_toml(temp_path)
        finally:
            os.remove(temp_path)

    def test_from_toml_empty_required_field(self):
        """Test ValueError when required field is empty"""
        empty_field_config = """
            username = "testuser"
            password = ""
            base_url = "http://localhost:8000"
            med_id = "aspirin"
            office = "office_A"
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(empty_field_config)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Missing or empty required fields"):
                Config.from_toml(temp_path)
        finally:
            os.remove(temp_path)

    def test_from_toml_all_required_fields_present(self, temp_config_file):
        """Test that all required fields must be present"""
        os.environ["CONFIG_PATH"] = temp_config_file
        config = Config.from_toml(temp_config_file)

        # Verify all required fields
        required_fields = ["username", "password", "base_url", "med_id", "office"]
        for field in required_fields:
            assert hasattr(config, field)
            assert getattr(config, field) is not None

    def test_from_toml_extra_fields_ignored(self):
        """Test that extra fields in config are ignored"""
        config_with_extras = """
            username = "testuser"
            password = "testpass"
            base_url = "http://localhost:8000"
            med_id = "aspirin"
            office = "office_A"
            extra_field = "should be ignored"
            another_extra = "also ignored"
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_with_extras)
            temp_path = f.name

        try:
            os.environ["CONFIG_PATH"] = temp_path
            config = Config.from_toml(temp_path)
            assert config.username == "testuser"
            # Extra fields should not raise errors
            assert not hasattr(config, "extra_field")
        finally:
            os.remove(temp_path)

    def test_from_toml_with_environment_variable(self, temp_config_file):
        """Test using CONFIG_PATH environment variable"""
        # The conftest.py fixture sets CONFIG_PATH automatically
        # This test verifies that from_toml() works with the env var set
        config = Config.from_toml()

        assert config.username == "testuser"

    def test_from_toml_invalid_toml_syntax(self):
        """Test ValueError with invalid TOML syntax"""
        invalid_toml = """
            username = "testuser
            password = "testpass"
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(invalid_toml)
            temp_path = f.name

        try:
            with pytest.raises(Exception):  # tomllib raises various exceptions
                Config.from_toml(temp_path)
        finally:
            os.remove(temp_path)

    def test_from_toml_type_validation(self):
        """Test that config values are properly loaded as strings"""
        config_with_types = """
            username = "testuser"
            password = "testpass"
            base_url = "http://localhost:8000"
            med_id = "123"
            office = "office_A"
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_with_types)
            temp_path = f.name

        try:
            os.environ["CONFIG_PATH"] = temp_path
            config = Config.from_toml(temp_path)
            assert isinstance(config.username, str)
            assert isinstance(config.med_id, str)
        finally:
            os.remove(temp_path)


class TestConfigIntegration:
    """Integration tests for Config"""

    def test_config_roundtrip(self, temp_config_file):
        """Test loading config and using it"""
        os.environ["CONFIG_PATH"] = temp_config_file
        config = Config.from_toml(temp_config_file)

        # Verify config can be used in typical workflow
        assert config.username
        assert config.password
        assert config.base_url.startswith("http")
        assert config.med_id
        assert config.office
