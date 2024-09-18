import importlib
import os
from importlib.util import module_from_spec, spec_from_loader
from unittest.mock import AsyncMock, patch


@patch("cmdbroker.cli.run", new_callable=AsyncMock)
def test_cli_server_mode(mock_run):
    loader = importlib.machinery.SourceFileLoader(
        "cmdbroker.__main__", os.path.join("cmdbroker", "__main__.py")
    )
    spec = spec_from_loader(loader.name, loader)
    mod = module_from_spec(spec)

    loader.exec_module(mod)

    mock_run.assert_awaited_once_with()
