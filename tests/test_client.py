import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cmdbroker.client import Client


def test_client_initialization(client_args):
    client = Client(client_args)

    assert client.command == "test_command"
    assert client.address == "127.0.0.1"
    assert client.port == 8080


@pytest.mark.asyncio
@patch("cmdbroker.message.Message.build")
@patch("select.select", return_value=[False])
@patch("cmdbroker.client.Client.relay_to_server", new_callable=AsyncMock)
async def test_run_without_stdin(mock_relay_to_server, mock_select, mock_build, client):
    mock_relay_to_server.return_value = MagicMock()

    await client.run()

    mock_select.assert_called_once()
    mock_build.assert_called_once()
    assert "stdin" not in mock_build.call_args[0][0]
    mock_relay_to_server.assert_awaited_once()
    mock_relay_to_server.return_value.write.assert_called_once_with(sys.stdout.buffer)


@pytest.mark.asyncio
@patch("cmdbroker.message.Message.build")
@patch("asyncio.to_thread", new_callable=AsyncMock, return_value="test_stdin")
@patch("select.select", return_value=[True])
@patch("cmdbroker.client.Client.relay_to_server", new_callable=AsyncMock)
async def test_run_with_stdin(mock_relay_to_server, mock_select, mock_asyncio, mock_build, client):
    mock_relay_to_server.return_value = MagicMock()

    await client.run()

    mock_select.assert_called_once()
    mock_asyncio.assert_awaited_once()
    mock_build.assert_called_once()
    assert "stdin" in mock_build.call_args[0][0]
    mock_relay_to_server.assert_awaited_once()
    mock_relay_to_server.return_value.write.assert_called_once_with(sys.stdout.buffer)


@pytest.mark.asyncio
@patch("asyncio.open_connection", new_callable=AsyncMock)
@patch("ssl.create_default_context")
async def test_relay_to_server(
    mock_ssl_create_default_context, mock_open_connection, client_ssl_context, client
):
    mock_reader = AsyncMock()
    mock_reader.read = AsyncMock(side_effect=[b"0019", b'{"fake":"response"}'])
    mock_writer = MagicMock()
    mock_writer.wait_closed = AsyncMock()
    mock_open_connection.return_value = (mock_reader, mock_writer)
    mock_ssl_create_default_context.return_value = client_ssl_context

    await client.relay_to_server(AsyncMock())

    mock_open_connection.assert_awaited_with("127.0.0.1", 8080, ssl=client_ssl_context)
    mock_writer.close.assert_called_once()
    mock_writer.wait_closed.assert_awaited_once()
