import socket
import unittest
from unittest.mock import MagicMock, patch

from cmdbroker.discovery import Discovery, DiscoveryBrowser


class TestDiscovery(unittest.TestCase):
    @patch("zeroconf.Zeroconf.register_service")
    def test_register(self, mock_register):
        discovery = Discovery()
        discovery.register("test-server", 8889)
        self.assertTrue(mock_register.called)
        discovery.unregister()

    @patch("zeroconf.ServiceBrowser")
    def test_browser(self, mock_browser):
        callback = MagicMock()
        browser = DiscoveryBrowser(callback)

        mock_zeroconf = MagicMock()
        mock_info = MagicMock()
        mock_info.addresses = [socket.inet_aton("127.0.0.1")]
        mock_info.port = 8889
        mock_info.properties = {}
        mock_zeroconf.get_service_info.return_value = mock_info

        browser.add_service(mock_zeroconf, "_cmdbroker._tcp.local.", "test._cmdbroker._tcp.local.")
        callback.assert_called()
        self.assertIn("test._cmdbroker._tcp.local.", browser.services)

        browser.remove_service(
            mock_zeroconf, "_cmdbroker._tcp.local.", "test._cmdbroker._tcp.local."
        )
        self.assertNotIn("test._cmdbroker._tcp.local.", browser.services)

        browser.close()


if __name__ == "__main__":
    unittest.main()
