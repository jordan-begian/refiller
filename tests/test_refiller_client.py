"""Tests for refiller_client module"""

import pytest
import aiohttp
from unittest.mock import AsyncMock, MagicMock
from src.refiller_client import RefillerClient


def create_async_cm(return_value):
    """Helper to create an async context manager"""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=return_value)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


@pytest.fixture
def base_url():
    """Fixture for base URL"""
    return "http://localhost:8000"


@pytest.fixture
def mock_session():
    """Fixture for mocked session"""
    session = MagicMock()
    session.close = AsyncMock()
    return session


class TestRefillerClientLogin:
    """Test cases for login functionality"""

    async def test_login_success(self, base_url):
        """Test successful login with valid credentials"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.headers = {"Set-Cookie": "session_id=abc123"}
        mock_response.raise_for_status = MagicMock()

        # Create async context manager for post response
        async_cm = create_async_cm(mock_response)

        # Create mock session with async close
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=async_cm)
        mock_session.close = AsyncMock()

        client = RefillerClient(base_url=base_url)
        client.client = mock_session

        cookie = await client.login("user", "pass", "office1")

        assert cookie == "session_id=abc123"
        mock_session.post.assert_called_once()
        await client.close()
        mock_session.close.assert_called_once()

    async def test_login_no_cookie(self, base_url, mock_session):
        """Test login failure when Set-Cookie header is missing"""
        # Mock response without Set-Cookie header
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        async_cm = create_async_cm(mock_response)
        mock_session.post = MagicMock(return_value=async_cm)

        client = RefillerClient(base_url=base_url)
        client.client = mock_session

        with pytest.raises(
            ValueError, match="Login failed: No session cookie received"
        ):
            await client.login("user", "pass", "office1")

        await client.close()

    async def test_login_http_error(self, base_url, mock_session):
        """Test login failure when HTTP error occurs"""
        # Mock response that raises HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = aiohttp.ClientError(
            "401 Unauthorized"
        )

        async_cm = create_async_cm(mock_response)
        mock_session.post = MagicMock(return_value=async_cm)

        client = RefillerClient(base_url=base_url)
        client.client = mock_session

        with pytest.raises(aiohttp.ClientError):
            await client.login("user", "wrongpass", "office1")

        await client.close()

    async def test_login_correct_url_and_payload(self, base_url, mock_session):
        """Test that login sends correct URL and payload"""
        mock_response = MagicMock()
        mock_response.headers = {"Set-Cookie": "session_id=abc123"}
        mock_response.raise_for_status = MagicMock()

        async_cm = create_async_cm(mock_response)
        mock_session.post = MagicMock(return_value=async_cm)

        client = RefillerClient(base_url=base_url)
        client.client = mock_session

        await client.login("john_doe", "secret123", "office_A")

        # Verify the POST request was made with correct parameters
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "http://localhost:8000/login"
        assert call_args[1]["data"] == {
            "office": "office_A",
            "username": "john_doe",
            "password": "secret123",
        }
        assert (
            call_args[1]["headers"]["Content-Type"]
            == "application/x-www-form-urlencoded"
        )
        assert call_args[1]["allow_redirects"] is False

        await client.close()

    async def test_login_with_special_characters(self, base_url):
        """Test login with special characters in credentials"""
        mock_response = MagicMock()
        mock_response.headers = {"Set-Cookie": "session_id=xyz789"}
        mock_response.raise_for_status = MagicMock()

        async_cm = create_async_cm(mock_response)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=async_cm)
        mock_session.close = AsyncMock()

        client = RefillerClient(base_url=base_url)
        client.client = mock_session
        special_pass = "p@ssw0rd!#$%"
        cookie = await client.login("user@domain.com", special_pass, "office_1")

        assert cookie == "session_id=xyz789"
        call_args = mock_session.post.call_args
        assert call_args[1]["data"]["password"] == special_pass

        await client.close()


class TestRefillerClientRequestRefill:
    """Test cases for request_refill functionality"""

    async def test_request_refill_success(self, base_url):
        """Test successful refill request"""
        # Mock successful response (status 200)
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()

        async_cm = create_async_cm(mock_response)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=async_cm)
        mock_session.close = AsyncMock()

        client = RefillerClient(base_url=base_url)
        client.client = mock_session
        result = await client.request_refill("session_id=abc123", "aspirin")

        assert result is True
        await client.close()

    async def test_request_refill_non_200_status(self, base_url):
        """Test refill request with non-200 status code"""
        # Mock response with non-200 status
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.raise_for_status = MagicMock()

        async_cm = create_async_cm(mock_response)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=async_cm)
        mock_session.close = AsyncMock()

        client = RefillerClient(base_url=base_url)
        client.client = mock_session
        result = await client.request_refill("session_id=abc123", "aspirin")

        assert result is False
        await client.close()

    async def test_request_refill_various_non_200_statuses(self, base_url):
        """Test refill request with various non-200 status codes"""
        for status_code in [201, 301, 400, 401, 403, 404, 500, 502, 503]:
            mock_response = MagicMock()
            mock_response.status = status_code
            mock_response.raise_for_status = MagicMock()

            async_cm = create_async_cm(mock_response)

            mock_session = MagicMock()
            mock_session.post = MagicMock(return_value=async_cm)
            mock_session.close = AsyncMock()

            client = RefillerClient(base_url=base_url)
            client.client = mock_session
            result = await client.request_refill("session_id=abc123", "aspirin")

            assert result is False
            await client.close()

    async def test_request_refill_http_error(self, base_url):
        """Test refill request failure due to HTTP error"""
        # Mock response that raises HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = aiohttp.ClientError(
            "500 Server Error"
        )

        async_cm = create_async_cm(mock_response)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=async_cm)
        mock_session.close = AsyncMock()

        client = RefillerClient(base_url=base_url)
        client.client = mock_session

        with pytest.raises(aiohttp.ClientError):
            await client.request_refill("session_id=abc123", "aspirin")

        await client.close()

    async def test_request_refill_correct_url_and_payload(self, base_url):
        """Test that refill request sends correct URL and payload"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()

        async_cm = create_async_cm(mock_response)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=async_cm)
        mock_session.close = AsyncMock()

        client = RefillerClient(base_url=base_url)
        client.client = mock_session
        await client.request_refill("session_id=abc123", "ibuprofen")

        # Verify the POST request was made with correct parameters
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "http://localhost:8000/msgs/newmsg"
        assert call_args[1]["data"] == {
            "meds": "ibuprofen",
            "subject": "R",
            "reply": "",
            "type": "R",
            "msg": "",
        }
        assert (
            call_args[1]["headers"]["Content-Type"]
            == "application/x-www-form-urlencoded"
        )
        assert call_args[1]["headers"]["Cookie"] == "session_id=abc123"

        await client.close()

    async def test_request_refill_different_medications(self, base_url):
        """Test refill request with different medication names"""
        medications = ["aspirin", "ibuprofen", "amoxicillin", "med-123"]

        for med in medications:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.raise_for_status = MagicMock()

            async_cm = create_async_cm(mock_response)

            mock_session = MagicMock()
            mock_session.post = MagicMock(return_value=async_cm)
            mock_session.close = AsyncMock()

            client = RefillerClient(base_url=base_url)
            client.client = mock_session
            result = await client.request_refill("session_id=abc123", med)

            assert result is True
            call_args = mock_session.post.call_args
            assert call_args[1]["data"]["meds"] == med

            await client.close()


class TestRefillerClientClose:
    """Test cases for close functionality"""

    async def test_close_session(self, base_url):
        """Test that close method properly closes the session"""
        mock_session = MagicMock()
        mock_session.close = AsyncMock()

        client = RefillerClient(base_url=base_url)
        client.client = mock_session
        await client.close()

        mock_session.close.assert_called_once()


class TestRefillerClientInitialization:
    """Test cases for client initialization"""

    async def test_initialization(self, base_url):
        """Test client initialization with base_url"""
        client = RefillerClient(base_url=base_url)
        assert client.base_url == base_url
        assert client.client is not None
        await client.close()

    async def test_initialization_with_different_base_urls(self):
        """Test client initialization with different base URLs"""
        urls = [
            "http://api.example.com",
            "https://secure.example.com:8443",
            "http://localhost:3000",
            "https://192.168.1.1:9000",
        ]

        for url in urls:
            client = RefillerClient(base_url=url)
            assert client.base_url == url
            await client.close()

    async def test_client_session_factory(self):
        """Test that ClientSession is created via factory"""
        client = RefillerClient(base_url="http://localhost:8000")

        # ClientSession should be created when client is instantiated
        assert client.client is not None
        assert isinstance(client.client, aiohttp.ClientSession)
        await client.close()


class TestRefillerClientIntegration:
    """Integration tests combining multiple operations"""

    async def test_full_workflow(self, base_url):
        """Test complete workflow: login -> request refill -> close"""
        # Mock login response
        login_response = MagicMock()
        login_response.headers = {"Set-Cookie": "session_id=xyz789"}
        login_response.raise_for_status = MagicMock()

        # Mock refill response
        refill_response = MagicMock()
        refill_response.status = 200
        refill_response.raise_for_status = MagicMock()

        login_cm = create_async_cm(login_response)
        refill_cm = create_async_cm(refill_response)

        mock_session = MagicMock()
        # Set up mock to return different responses for different calls
        mock_session.post.side_effect = [login_cm, refill_cm]
        mock_session.close = AsyncMock()

        client = RefillerClient(base_url=base_url)
        client.client = mock_session

        # Login
        cookie = await client.login("user", "pass", "office1")
        assert cookie == "session_id=xyz789"

        # Request refill
        result = await client.request_refill(cookie, "medicine")
        assert result is True

        # Close
        await client.close()
        mock_session.close.assert_called_once()

    async def test_multiple_refill_requests(self, base_url):
        """Test making multiple refill requests with same session"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()

        async_cm = create_async_cm(mock_response)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=async_cm)
        mock_session.close = AsyncMock()

        client = RefillerClient(base_url=base_url)
        client.client = mock_session
        cookie = "session_id=xyz789"

        # Make multiple refill requests
        medications = ["aspirin", "ibuprofen", "tylenol"]
        for med in medications:
            result = await client.request_refill(cookie, med)
            assert result is True

        await client.close()
