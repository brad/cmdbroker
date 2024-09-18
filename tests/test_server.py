import asyncio
import io
import os
import signal
import ssl
from contextlib import redirect_stdout
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography import x509

from cmdbroker.server import Server


def test_server_init(server_args):
    server = Server(server_args)

    assert server.address == "127.0.0.1"
    assert server.port == 8080


def test_server_stop_not_started(server_args):
    server = Server(server_args)

    with io.StringIO() as buf, redirect_stdout(buf):
        server.stop()

        assert buf.getvalue() == "There is no server running.\n"


@patch("getpass.getpass", return_value="test-password")
def test_server_init_without_password(mock_getpass, server_args):
    args = server_args
    args.password = None

    server = Server(args)

    mock_getpass.assert_called_once_with("Enter password for key: ")
    assert server.password == "test-password"


@patch("getpass.getpass", side_effect=KeyboardInterrupt)
def test_server_init_without_password_keyboard_interrupt(mock_getpass, server_args):
    args = server_args
    args.password = None

    with pytest.raises(SystemExit):
        Server(args)


@patch("getpass.getpass", return_value="")
def test_server_init_without_password_empty_password(mock_getpass, server_args):
    args = server_args
    args.password = None

    with io.StringIO() as buf, redirect_stdout(buf):
        with pytest.raises(SystemExit):
            Server(args)
        assert buf.getvalue().startswith("Password cannot be empty.")


def test_try_to_create_server_without_cert_and_key(server_args, ssl_files):
    os.remove(ssl_files[0])
    os.remove(ssl_files[1])

    with pytest.raises(ValueError) as err:
        Server(server_args)

    assert str(err.value).startswith("SSL files do not exist.")


@pytest.mark.asyncio
@patch("cryptography.x509.random_serial_number", return_value=1234567890)
async def test_server_generate_cert_and_key(mock_random_serial_number, server_args):
    args = server_args
    args.generate_cert_and_key = True

    with io.StringIO() as buf, redirect_stdout(buf):
        Server(args)

        assert buf.getvalue().startswith("Generated certificate")

    # Assert that the certificate has the expected properties
    mock_random_serial_number.assert_called_once()
    with open(args.broker_cert, "r") as cert_file:
        cert = x509.load_pem_x509_certificate(cert_file.read().encode())

        assert (
            cert.subject.rfc4514_string()
            == "CN=127.0.0.1,O=Test Organization,L=San Francisco,ST=CA,C=US"
        )
        assert cert.serial_number == 1234567890
        assert cert.issuer == cert.subject
        assert isinstance(cert.extensions[0].value[0], x509.IPAddress)


@pytest.mark.asyncio
@patch("builtins.input", side_effect=("US", "NM", "Santa Fe", "Test Org2"))
async def test_server_generate_cert_and_key_not_ip(mock_input, server_args):
    args = server_args
    args.address = "cmdbroker.example.com"
    args.generate_cert_and_key = True
    args.cert_country = None
    args.cert_state = None
    args.cert_locality = None
    args.cert_org = None

    with io.StringIO() as buf, redirect_stdout(buf):
        Server(args)

        assert mock_input.call_count == 4
        mock_input.assert_any_call("Enter the country for the certificate: ")
        mock_input.assert_any_call("Enter the state for the certificate: ")
        mock_input.assert_any_call("Enter the locality for the certificate: ")
        mock_input.assert_any_call("Enter the organization for the certificate: ")
        assert buf.getvalue().startswith("Generated certificate")

    # Assert that the certificate has the expected properties
    with open(args.broker_cert, "r") as cert_file:
        cert = x509.load_pem_x509_certificate(cert_file.read().encode())

        assert (
            cert.subject.rfc4514_string()
            == "CN=cmdbroker.example.com,O=Test Org2,L=Santa Fe,ST=NM,C=US"
        )
        assert cert.issuer == cert.subject
        assert isinstance(cert.extensions[0].value[0], x509.DNSName)


@pytest.mark.asyncio
@patch("ssl.create_default_context")
async def test_server_run_start_server(mock_ssl_create_default_context, server_args, mock_server):
    ssl_context = MagicMock()
    mock_ssl_create_default_context.return_value = ssl_context
    with patch(
        "asyncio.start_server", new_callable=AsyncMock, return_value=mock_server
    ) as mock_start_server:
        with io.StringIO() as buf, redirect_stdout(buf):
            server = Server(server_args)

            await server.run()

            mock_start_server.assert_called_once_with(
                server.handle_request, server_args.address, server_args.port, ssl=ssl_context
            )
            mock_server.serve_forever.assert_awaited_once_with()
            assert buf.getvalue().startswith(
                f"Server listening on {server_args.address}:{server_args.port}."
            )
            assert buf.getvalue().endswith("Press Ctrl+C to stop.\n")


@pytest.mark.asyncio
@patch("ssl.create_default_context")
async def test_server_run_start_server_bad_pass(
    mock_ssl_create_default_context, server_args, mock_server
):
    ssl_context = MagicMock()
    mock_ssl_create_default_context.return_value = ssl_context
    ssl_context.load_cert_chain.side_effect = ssl.SSLError
    with io.StringIO() as buf, redirect_stdout(buf):
        server = Server(server_args)

        with pytest.raises(SystemExit):
            await server.run()


def test_server_stop(server_args):
    server = Server(server_args)
    mock_server = MagicMock()
    server.server = mock_server

    with io.StringIO() as buf, redirect_stdout(buf):
        server.stop()

        mock_server.close.assert_called_once()
        assert buf.getvalue().endswith("Server stopped by user.\n")


@pytest.mark.asyncio
@patch("ssl.create_default_context")
@patch("asyncio.get_running_loop")
async def test_server_run_handle_keyboard_interrupt(
    mock_get_running_loop, mock_ssl_create_default_context, server_args, mock_server
):
    mock_loop = MagicMock()
    mock_get_running_loop.return_value = mock_loop
    ssl_context = MagicMock()
    mock_ssl_create_default_context.return_value = ssl_context
    mock_server.close = MagicMock()
    mock_server.serve_forever.side_effect = asyncio.exceptions.CancelledError
    with patch("asyncio.start_server", return_value=mock_server):
        with io.StringIO() as buf, redirect_stdout(buf):
            server = Server(server_args)

            await server.run()

            mock_loop.add_signal_handler.assert_called_once_with(signal.SIGINT, server.stop)


@pytest.mark.asyncio
@patch(
    "cmdbroker.message.Message.json",
    return_value={"method": "process", "parameters": {"command": "echo 'Hello World'"}},
)
async def test_handle_valid_process_request(mock_message, server):
    # Dummy data, since we are mocking the json method
    reader = AsyncMock()
    reader.read = AsyncMock(side_effect=[b"0019", b'{"fake":"response"}'])
    writer = AsyncMock()
    writer.write = MagicMock()
    writer.close = MagicMock()

    await server.handle_request(reader, writer)

    writer.write.assert_called_once_with(b"Hello World\n")


@pytest.mark.asyncio
@patch(
    "cmdbroker.message.Message.json",
    return_value={"method": "bogus"},
)
async def test_handle_invalid_method_request(mock_message, server):
    # Dummy data, since we are mocking the json method
    reader = AsyncMock()
    reader.read = AsyncMock(side_effect=[b"0019", b'{"fake":"response"}'])
    writer = AsyncMock()

    with pytest.raises(ValueError):
        await server.handle_request(reader, writer)


@pytest.mark.asyncio
@patch(
    "cmdbroker.message.Message.json",
    return_value={
        "method": "process",
        "stdin": "Hello World",
        "parameters": {"command": "grep Hello"},
    },
)
async def test_handle_valid_process_request_with_stdin(mock_message, server):
    # Dummy data, since we are mocking the json method
    reader = AsyncMock()
    reader.read = AsyncMock(side_effect=[b"0019", b'{"fake":"response"}'])
    writer = AsyncMock()
    writer.write = MagicMock()
    writer.close = MagicMock()

    await server.handle_request(reader, writer)

    writer.write.assert_called_once_with(b"Hello World\n")
