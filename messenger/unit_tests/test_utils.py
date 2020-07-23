import json
from unittest import TestCase

from messenger.unit_tests.loopback import ConnLoopback
from messenger.common.utils import parse_cli_flags, send_message, receive_message


class TestUtils(TestCase):
    """Test cases for common utility functions of the messenger."""

    def test_parse_cli_flags(self):
        """
        Tests for argument parser.

        Parser receives a list of flags, returns a parsed settings object.
        """
        settings = parse_cli_flags(''.split())
        self.assertIsNone(settings.address)
        settings = parse_cli_flags('localhost'.split())
        self.assertEqual(settings.address, 'localhost')
        self.assertEqual(settings.port, 7777)
        settings = parse_cli_flags('test.test 8765'.split())
        self.assertEqual(settings.address, 'test.test')
        self.assertEqual(settings.port, 8765)

    def test_send_message(self):
        """
        Test for message sending function.

        Gets a dict and sends it as encoded json string to a socket.
        """
        loopback = ConnLoopback('localhost', 7777)
        test_obj = {
            'action': 'presence',
            'time': 1593605102,
            'type': 'status',
            'user': {
                'account_name': 'Guest',
                'status': 'Я на месте!'
            }
        }
        send_message(test_obj, loopback.client_connection)
        data = loopback.server_get_data(1024)
        check_obj = json.loads(data.decode('UTF-8'))
        self.assertEqual(test_obj, check_obj)
        loopback.close()

    def test_receive_message(self):
        """
        Tests for message receiving function.

        Gets json data from connection, returns a dict or None when object is malformed.
        """
        loopback = ConnLoopback('localhost', 7777)

        # Receiving a proper json object should yield the same dict as one that was sent
        test_obj = {
            'action': 'msg',
            'time': 1593605102,
            'to': '#room',
            'from': 'Guest',
            'message': 'Проверка!',
        }
        loopback.server_send_data(json.dumps(test_obj).encode('UTF-8'))
        check_obj = receive_message(loopback.client_connection)
        self.assertEqual(test_obj, check_obj)

        # Receiving a malformed json object should yield None
        malformed_test_str = '{"action": }'
        loopback.server_send_data(malformed_test_str.encode('UTF-8'))
        check_obj = receive_message(loopback.client_connection)
        self.assertIsNone(check_obj)

        loopback.close()
