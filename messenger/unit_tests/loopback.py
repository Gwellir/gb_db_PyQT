from socket import SOCK_STREAM, socket


class ConnLoopback:
    def __init__(self, interface, port):
        self._s_conn = socket(type=SOCK_STREAM)
        self._s_conn.bind(('', port))
        self._s_conn.listen(1)

        self.c_conn = socket(type=SOCK_STREAM)
        self.c_conn.connect((interface, port))
        self.client, self.addr = self._s_conn.accept()

    def close(self):
        self.client.close()
        self.c_conn.close()
        self._s_conn.close()

    @property
    def client_connection(self):
        return self.c_conn

    def server_get_data(self, size):
        return self.client.recv(size)

    def server_send_data(self, data):
        self.client.send(data)

    def client_get_data(self, size):
        return self.c_conn.recv(size)
