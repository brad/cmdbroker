import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import flet as ft
from cmdbroker.gui.client_view import ClientView
from cmdbroker.gui.server_view import ServerView
from cmdbroker.gui.config import Config

class TestGUIComponents(unittest.TestCase):
    def setUp(self):
        self.page = MagicMock(spec=ft.Page)
        self.config = MagicMock(spec=Config)
        self.config.remotes = []

    def test_client_view_init(self):
        view = ClientView(self.page, self.config)
        self.assertIsInstance(view, ft.Column)

    def test_server_view_init(self):
        view = ServerView(self.page, self.config)
        self.assertIsInstance(view, ft.Column)

    @patch('cmdbroker.gui.client_view.DiscoveryBrowser')
    def test_client_discovery_update(self, mock_browser):
        view = ClientView(self.page, self.config)
        view.on_discovery_update({"test": {"address": "1.2.3.4", "port": 8889, "name": "test"}})
        self.assertIn("test", view.discovered_services)
        self.assertEqual(len(view.discovered_list.controls), 1)

    @patch('cmdbroker.gui.client_view.Client')
    def test_add_remote(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.request_certificate = AsyncMock(return_value=b"cert-data")

        view = ClientView(self.page, self.config)
        info = {"name": "test", "address": "1.2.3.4", "port": 8889}

        # We need to run the async task
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(view.request_cert_and_add(info))

        self.config.save.assert_called()
        self.page.update.assert_called()

    @patch('cmdbroker.gui.server_view.Server')
    @patch('cmdbroker.gui.server_view.Discovery')
    def test_start_server(self, mock_discovery_cls, mock_server_cls):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        mock_server = mock_server_cls.return_value
        # Use a Future that we can control to keep the server "running"
        server_run_future = loop.create_future()
        mock_server.run = MagicMock(return_value=server_run_future)
        self.config.get_password.return_value = "password"
        view = ServerView(self.page, self.config)

        # Start the server logic in a task
        task = loop.create_task(view.run_server_logic("test", 8889, "cert.pem", "key.pem", "password"))

        # Run the loop until the server is registered
        async def check_registered():
            while "test" not in view.running_servers:
                await asyncio.sleep(0.01)

        loop.run_until_complete(check_registered())

        self.assertIn("test", view.running_servers)
        self.assertTrue(view.running_servers["test"]["running"])

        # Toggle server off
        view.toggle_server("test")
        self.assertFalse(view.running_servers["test"]["running"])

        # Clean up
        server_run_future.set_result(None)
        loop.run_until_complete(task)

    def test_select_remote(self):
        view = ClientView(self.page, self.config)
        remote = {"name": "test", "address": "1.2.3.4", "port": 8889, "cert": "cert.pem"}
        view.select_remote(remote)
        self.assertEqual(view.selected_remote, remote)
        self.page.update.assert_called()

    @patch('cmdbroker.gui.client_view.Client')
    def test_run_command(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_response = MagicMock()
        mock_response.text = b"output"
        mock_client.relay_to_server = AsyncMock(return_value=mock_response)

        view = ClientView(self.page, self.config)
        view.selected_remote = {"name": "test", "address": "1.2.3.4", "port": 8889, "cert": "cert.pem"}
        view.command_input.value = "ls"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(view.run_command(None))

        self.assertIn("output", view.output_text.value)
        self.page.update.assert_called()

if __name__ == '__main__':
    unittest.main()
