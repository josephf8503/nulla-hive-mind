from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from network.transport import UDPTransportServer


class TransportBindContractsTests(unittest.TestCase):
    def test_udp_bind_conflict_raises_helpful_error_without_retry_loop(self) -> None:
        bind_error = OSError(10048, "Only one usage of each socket address")
        bind_error.winerror = 10048
        mock_sock = Mock()
        mock_sock.bind.side_effect = bind_error

        with patch("network.transport.socket.socket", return_value=mock_sock):
            server = UDPTransportServer(host="127.0.0.1", port=49152)
            with self.assertRaises(OSError) as raised:
                server.start()

        self.assertIn("port already in use", str(raised.exception))
        self.assertEqual(mock_sock.bind.call_count, 1)
        mock_sock.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
