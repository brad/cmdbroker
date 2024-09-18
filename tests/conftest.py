import argparse
import os
import shutil
import sys
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from cmdbroker.client import Client
from cmdbroker.server import Server


@pytest.fixture
def mock_argv():
    original_argv = sys.argv
    yield
    sys.argv = original_argv


@pytest.fixture
def client_args() -> argparse.Namespace:
    return argparse.Namespace(
        command="test_command", address="127.0.0.1", port=8080, broker_cert="test-cert.pem"
    )


@pytest.fixture
def client_ssl_context():
    ssl_context = MagicMock()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = MagicMock()
    ssl_context.load_verify_locations = MagicMock()
    return ssl_context


@pytest.fixture
def client(client_args):
    return Client(client_args)


@pytest.fixture
def sample_message():
    return {"method": "process", "parameters": {"param1": "value1", "param2": "value2"}}


@pytest.fixture
def mock_server():
    server = AsyncMock()
    server.sockets = [MagicMock()]
    server.sockets[0].getsockname.return_value = ("127.0.0.1", 8080)
    return server


@pytest.fixture
def ssl_files():
    temp_dir = tempfile.mkdtemp()
    cert_file = os.path.join(temp_dir, "test-cert.pem")
    key_file = os.path.join(temp_dir, "test-key.pem")
    os.close(os.open(cert_file, os.O_CREAT))
    os.close(os.open(key_file, os.O_CREAT))

    yield cert_file, key_file

    shutil.rmtree(temp_dir)


@pytest.fixture
def server_args(ssl_files):
    return argparse.Namespace(
        address="127.0.0.1",
        port=8080,
        broker_cert=ssl_files[0],
        broker_key=ssl_files[1],
        cert_country="US",
        cert_state="CA",
        cert_locality="San Francisco",
        cert_org="Test Organization",
        cert_days=15,
        generate_cert_and_key=False,
        password="test-password",
    )


@pytest.fixture
def server(server_args):
    return Server(server_args)
