import argparse
import io
import json
import sys
from argparse import Namespace
from contextlib import redirect_stderr
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cmdbroker import cli


@pytest.mark.asyncio
@patch("os.path.exists", return_value=True)
@patch("cmdbroker.server.Server.run", new_callable=AsyncMock)
@patch("cmdbroker.client.Client.run", new_callable=AsyncMock)
async def test_main_initializes_server_when_server_arg_provided(
    mock_client, mock_server, mock_exists
):
    args = Namespace(
        server=True,
        address="localhost",
        port=8889,
        command=None,
        broker_cert="test-cert.pem",
        broker_key="test-key.pem",
        cert_country="US",
        cert_state="CA",
        cert_locality="San Francisco",
        cert_org="Test Organization",
        cert_days=15,
        generate_cert_and_key=False,
        password="test-password",
    )

    await cli.main(args)

    assert mock_exists.call_count == 2
    mock_exists.assert_any_call("test-cert.pem")
    mock_exists.assert_any_call("test-key.pem")
    mock_server.assert_awaited_once()
    mock_client.assert_not_called()


@pytest.mark.asyncio
@patch("cmdbroker.server.Server.run", new_callable=AsyncMock)
@patch("cmdbroker.client.Client.run", new_callable=AsyncMock)
async def test_main_initializes_client_when_server_arg_not_provided(mock_client, mock_server):
    args = Namespace(
        server=False,
        address="localhost",
        port=8889,
        command="test_command",
        broker_cert="test-cert.pem",
    )

    await cli.main(args)

    mock_server.assert_not_called()
    mock_client.assert_awaited_once()


@pytest.mark.asyncio
@patch("os.path.exists", return_value=True)
@patch("cmdbroker.cli.main")
async def test_run_server_mode_with_config(mock_main, mock_exists, mock_argv):
    # Command-line arguments for server mode
    sys.argv = [
        "cmdbroker",
        "--config",
        "test-config.json",
        "--server",
        "--address",
        "127.0.0.1",
        "--generate-cert-and-key",
    ]
    parser = argparse.ArgumentParser(prog="cmdbroker", description="Run as server or client.")
    config_contents = json.dumps(
        {
            "broker-cert": "diff-cert.pem",
            "address": "localhost",
            "cert-country": "US",
            "cert-state": "AZ",
            "cert-locality": "Phoenix",
            "cert-org": "Vandalay Industries",
            "cert-days": 30,
        }
    )

    mock_open = MagicMock(return_value=io.StringIO(config_contents))
    with patch("argparse.ArgumentParser", return_value=parser):
        with patch("builtins.open", mock_open):
            # Call the run method
            await cli.run()

    # Assertions
    mock_exists.assert_called_with("test-config.json")
    mock_open.assert_called_once_with("test-config.json", "r")
    mock_main.assert_awaited_once_with(
        Namespace(
            config="test-config.json",
            server=True,
            address="127.0.0.1",
            port=8889,
            command=None,
            broker_cert="diff-cert.pem",
            broker_key="broker-key.pem",
            cert_country="US",
            cert_state="AZ",
            cert_locality="Phoenix",
            cert_org="Vandalay Industries",
            cert_days=30,
            generate_cert_and_key=True,
            password=None,
        )
    )


@pytest.mark.asyncio
@patch("cmdbroker.cli.main")
async def test_run_server_mode_without_address(mock_main, mock_argv):
    # Command-line arguments for server mode
    sys.argv = ["cmdbroker", "--server", "--config", "test-config.json"]

    # Call the run method
    with io.StringIO() as buf, redirect_stderr(buf):
        with pytest.raises(SystemExit):
            await cli.run()

        assert buf.getvalue().endswith("the following arguments are required: --address\n")


@pytest.mark.asyncio
@patch("cmdbroker.cli.main")
async def test_run_server_mode_with_missing_key_file(mock_main, mock_argv):
    # Command-line arguments for server mode
    sys.argv = [
        "cmdbroker",
        "--config",
        "test-config.json",
        "--server",
        "--address",
        "127.0.0.1",
        "--broker-key",
        "test-key.pem",
    ]

    # Call the run method
    with io.StringIO() as buf, redirect_stderr(buf):
        with pytest.raises(SystemExit):
            await cli.run()

        assert buf.getvalue().endswith("Broker key file not found\n")


@pytest.mark.asyncio
@patch("cmdbroker.cli.main")
async def test_run_client_mode_with_command(mock_main, mock_argv):
    # Command-line arguments for server mode
    sys.argv = ["cmdbroker", '"ls -la"', "--config", "test-config.json", "--address", "127.0.0.1"]

    # Call the run method
    await cli.run()

    # Assertions
    mock_main.assert_awaited_once_with(
        Namespace(
            config="test-config.json",
            command='"ls -la"',
            server=False,
            address="127.0.0.1",
            port=8889,
            broker_cert="broker-cert.pem",
            broker_key="broker-key.pem",
            cert_country=None,
            cert_state=None,
            cert_locality=None,
            cert_org=None,
            cert_days=365,
            generate_cert_and_key=False,
            password=None,
        )
    )


@pytest.mark.asyncio
@patch("cmdbroker.cli.main")
async def test_run_client_mode_without_command(mock_main, mock_argv):
    # Command-line arguments for client mode
    sys.argv = ["cmdbroker", "--config", "test-config.json", "--address", "127.0.0.1"]

    # Call the run method
    with io.StringIO() as buf, redirect_stderr(buf):
        with pytest.raises(SystemExit):
            await cli.run()

        assert buf.getvalue().endswith("You must provide a command when running in client mode\n")


@pytest.mark.asyncio
@patch("cmdbroker.cli.main")
async def test_run_client_mode_with_missing_cert_file(mock_main, mock_argv):
    # Command-line arguments for client mode
    sys.argv = [
        "cmdbroker",
        '"ls -la"',
        "--config",
        "test-config.json",
        "--address",
        "127.0.0.1",
        "--broker-cert",
        "test-cert.pem",
    ]

    # Call the run method
    with io.StringIO() as buf, redirect_stderr(buf):
        with pytest.raises(SystemExit):
            await cli.run()

        assert buf.getvalue().endswith("Broker certificate file not found\n")
