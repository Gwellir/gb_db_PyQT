import os
import sys
import argparse

from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox

from client.client_database import ClientBase
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
from common.constants import (Client, MIN_PORT_NUMBER, MAX_PORT_NUMBER, JIM, DEFAULT_ADDRESS, DEFAULT_PORT)
from common.exceptions import NoAddressGivenError, PortOutOfRangeError, ServerError
from common.utils import parse_cli_flags, send_message, receive_message
from log.client_log_config import CLIENT_LOG
from common.decorators import Log


def arg_parser():
    """ CLI parameters parser.
    Returns address, port (validated), username, password for user
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    if not 1023 < server_port < 65536:
        CLIENT_LOG.critical(
            f'Unusable port number provided: {server_port}. Use ports between {MIN_PORT_NUMBER} and {MAX_PORT_NUMBER}.')
        exit(1)

    return server_address, server_port, client_name, client_passwd


if __name__ == '__main__':
    address, port, username, password = arg_parser()

    app = QApplication(sys.argv)

    init_dialog = UserNameDialog()
    if not username or not password:
        app.exec_()
        if init_dialog.ok_pressed:
            username = init_dialog.client_name.text()
            password = init_dialog.client_passwd.text()
            CLIENT_LOG.debug(f'Using name = {username}, pw = {password}')
        else:
            exit(0)

    CLIENT_LOG.info(f'Started a client, params: {address}:{port} (@{username})')

    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{username}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key_f:
            key_f.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key_f:
            keys = RSA.import_key(key_f.read())

    CLIENT_LOG.debug('Keys loaded')

    db = ClientBase(username)

    try:
        transport = ClientTransport(port, address, db, username, password, keys)
    except ServerError as err:
        message = QMessageBox()
        message.critical(init_dialog, 'Server Error', str(err))
        exit(1)
    transport.setDaemon(True)
    transport.start()

    del init_dialog

    window = ClientMainWindow(db, transport)
    window.make_connection(transport)
    window.statusBar().showMessage('Connected to TEST server')
    app.exec_()

    transport.transport_shutdown()
    transport.join()
