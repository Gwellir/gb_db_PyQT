import sys

from PyQt5.QtWidgets import QApplication

from client.client_database import ClientBase
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
from common.constants import (Client, MIN_PORT_NUMBER, MAX_PORT_NUMBER, JIM)
from common.exceptions import NoAddressGivenError, PortOutOfRangeError, ServerError
from common.utils import parse_cli_flags, send_message, receive_message
from log.client_log_config import CLIENT_LOG
from common.decorators import Log


@Log(raiseable=True)
def check_settings(args):
    settings = parse_cli_flags(args)
    if not settings.address:
        CLIENT_LOG.error('Server address should be specified (-a option).')
        raise NoAddressGivenError
    if settings.port < MIN_PORT_NUMBER or settings.port > MAX_PORT_NUMBER:
        CLIENT_LOG.error(f'Please use port number (-p option) between {MIN_PORT_NUMBER} and {MAX_PORT_NUMBER} '
                         f'(got {settings.port})')
        raise PortOutOfRangeError

    return settings.address, settings.port, settings.user


if __name__ == '__main__':
    address, port, username = check_settings(sys.argv[1:])

    app = QApplication(sys.argv)

    if not username:
        init_dialog = UserNameDialog()
        app.exec_()
        if init_dialog.ok_pressed:
            username = init_dialog.client_name.text()
            del init_dialog
        else:
            exit(0)

    CLIENT_LOG.info(f'Started a client, params: {address}:{port} (@{username})')

    db = ClientBase(username)

    try:
        transport = ClientTransport(port, address, db, username)
    except ServerError as err:
        print(err)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    window = ClientMainWindow(db, transport)
    window.make_connection(transport)
    window.statusBar().showMessage('Connected to TEST server')
    app.exec_()

    transport.transport_shutdown()
    transport.join()
