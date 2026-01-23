"""Tests for main module"""

import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from main import main


@pytest.fixture
def mock_config():
    """Fixture providing mock config"""
    config = MagicMock()
    config.username = "testuser"
    config.password = "testpass"
    config.base_url = "http://localhost:8000"
    config.med_id = "med123"
    config.office = "office_A"
    return config


class TestMainExecution:
    """Test cases for main function execution"""

    async def test_main_successful_flow(self, mock_config):
        """Test main function with successful login and refill"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            mock_config_class.from_toml.return_value = mock_config

            # Mock client
            mock_client = AsyncMock()
            mock_client.login = AsyncMock(return_value="session_id=xyz789")
            mock_client.request_refill = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            await main()

            # Verify config was loaded
            mock_config_class.from_toml.assert_called_once()

            # Verify client was created with correct base_url
            mock_client_class.assert_called_once_with(mock_config.base_url)

            # Verify login was called with correct credentials
            mock_client.login.assert_called_once_with(
                mock_config.username, mock_config.password, mock_config.office
            )

            # Verify refill was called with correct medication
            mock_client.request_refill.assert_called_once_with(
                "session_id=xyz789", mock_config.med_id
            )

            # Verify client was closed
            mock_client.close.assert_called_once()

    async def test_main_failed_login(self, mock_config):
        """Test main function when login fails"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            mock_config_class.from_toml.return_value = mock_config

            # Mock client with failed login
            mock_client = AsyncMock()
            mock_client.login = AsyncMock(side_effect=Exception("Login failed"))
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            # Main should handle the exception and return
            await main()

            # Verify login was attempted
            mock_client.login.assert_called_once()

            # Verify refill was NOT called
            mock_client.request_refill.assert_not_called()

            # Verify client was still closed
            mock_client.close.assert_called_once()

    async def test_main_failed_refill(self, mock_config):
        """Test main function when refill request fails"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            mock_config_class.from_toml.return_value = mock_config

            # Mock client with successful login but failed refill
            mock_client = AsyncMock()
            mock_client.login = AsyncMock(return_value="session_id=xyz789")
            mock_client.request_refill = AsyncMock(
                side_effect=Exception("Refill failed")
            )
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            await main()

            # Verify login was successful
            mock_client.login.assert_called_once()

            # Verify refill was attempted
            mock_client.request_refill.assert_called_once()

            # Verify client was still closed
            mock_client.close.assert_called_once()

    async def test_main_refill_returns_false(self, mock_config):
        """Test main function when refill request returns False"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            mock_config_class.from_toml.return_value = mock_config

            # Mock client
            mock_client = AsyncMock()
            mock_client.login = AsyncMock(return_value="session_id=xyz789")
            mock_client.request_refill = AsyncMock(return_value=False)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            await main()

            # Even though refill returned False, execution should complete
            mock_client.close.assert_called_once()

    async def test_main_config_loading_exception(self):
        """Test main function when config loading fails"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            # Config loading fails
            mock_config_class.from_toml.side_effect = FileNotFoundError(
                "Config not found"
            )

            # Main should handle the exception
            with pytest.raises(FileNotFoundError):
                await main()

            # Client should not be created
            mock_client_class.assert_not_called()

    async def test_main_client_close_called_on_error(self, mock_config):
        """Test that client.close() is always called even on error"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            mock_config_class.from_toml.return_value = mock_config

            # Mock client
            mock_client = AsyncMock()
            mock_client.login = AsyncMock(side_effect=RuntimeError("Network error"))
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            await main()

            # Verify close was called in finally block
            mock_client.close.assert_called_once()


class TestMainLogging:
    """Test cases for logging behavior"""

    async def test_main_logs_startup(self, mock_config, caplog):
        """Test that main logs startup message"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            mock_config_class.from_toml.return_value = mock_config

            mock_client = AsyncMock()
            mock_client.login = AsyncMock(return_value="session_id=xyz789")
            mock_client.request_refill = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            with caplog.at_level(logging.INFO):
                await main()

            # Check for startup log message
            assert any(
                "Starting refiller service" in record.message
                for record in caplog.records
            )

    async def test_main_logs_login_attempt(self, mock_config, caplog):
        """Test that main logs login attempt"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            mock_config_class.from_toml.return_value = mock_config

            mock_client = AsyncMock()
            mock_client.login = AsyncMock(return_value="session_id=xyz789")
            mock_client.request_refill = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            with caplog.at_level(logging.INFO):
                await main()

            # Check for login log message
            assert any("Logging in" in record.message for record in caplog.records)

    async def test_main_logs_success(self, mock_config, caplog):
        """Test that main logs success message"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            mock_config_class.from_toml.return_value = mock_config

            mock_client = AsyncMock()
            mock_client.login = AsyncMock(return_value="session_id=xyz789")
            mock_client.request_refill = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            with caplog.at_level(logging.INFO):
                await main()

            # Check for success log message
            assert any(
                "successful" in record.message.lower() for record in caplog.records
            )

    async def test_main_logs_error_on_failure(self, mock_config, caplog):
        """Test that main logs error on failure"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            mock_config_class.from_toml.return_value = mock_config

            mock_client = AsyncMock()
            mock_client.login = AsyncMock(side_effect=Exception("Auth failed"))
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            with caplog.at_level(logging.ERROR):
                await main()

            # Check for error log message
            assert any(record.levelname == "ERROR" for record in caplog.records)


class TestMainIntegration:
    """Integration tests for main function"""

    async def test_main_with_different_config_values(self):
        """Test main with various config values"""
        configs = [
            {
                "username": "user1",
                "password": "pass1",
                "base_url": "http://localhost:8000",
                "med_id": "med1",
                "office": "office1",
            },
            {
                "username": "user2@domain.com",
                "password": "p@ss!",
                "base_url": "https://api.example.com",
                "med_id": "MED-123",
                "office": "office_2",
            },
        ]

        for config_data in configs:
            with (
                patch("main.Config") as mock_config_class,
                patch("main.RefillerClient") as mock_client_class,
            ):
                mock_config = MagicMock()
                for key, value in config_data.items():
                    setattr(mock_config, key, value)
                mock_config_class.from_toml.return_value = mock_config

                mock_client = AsyncMock()
                mock_client.login = AsyncMock(return_value="session_id=xyz789")
                mock_client.request_refill = AsyncMock(return_value=True)
                mock_client.close = AsyncMock()
                mock_client_class.return_value = mock_client

                await main()

                # Verify correct config was used
                mock_client_class.assert_called_once_with(config_data["base_url"])
                mock_client.login.assert_called_once_with(
                    config_data["username"],
                    config_data["password"],
                    config_data["office"],
                )

    async def test_main_cleanup_on_success(self, mock_config):
        """Test that resources are cleaned up on success"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            mock_config_class.from_toml.return_value = mock_config

            mock_client = AsyncMock()
            mock_client.login = AsyncMock(return_value="session_id=xyz789")
            mock_client.request_refill = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            await main()

            # Verify cleanup
            mock_client.close.assert_called_once()

    async def test_main_cleanup_on_exception(self, mock_config):
        """Test that resources are cleaned up on exception"""
        with (
            patch("main.Config") as mock_config_class,
            patch("main.RefillerClient") as mock_client_class,
        ):
            mock_config_class.from_toml.return_value = mock_config

            mock_client = AsyncMock()
            mock_client.login = AsyncMock(side_effect=Exception("Network error"))
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            await main()

            # Verify cleanup even on exception
            mock_client.close.assert_called_once()
