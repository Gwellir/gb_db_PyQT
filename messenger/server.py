import configparser
import select
import sys
import os
import argparse
from collections import defaultdict
from json import JSONDecodeError
from socket import SOCK_STREAM, socket, AF_INET
from datetime import datetime
from threading import Thread, Lock
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer

from common.constants import (ResCodes, CODE_MESSAGES, JIM, MAX_CLIENTS,
                              TIMEOUT_INTERVAL, DEFAULT_PORT)
from common.utils import send_message, receive_message, form_response
from log.server_log_config import SERVER_LOG
from common.decorators import Log
from common.descr import PortNumber
from meta import ServerWatcher
from server.core import MessageProcessor
from server.server_database import ServerBase
# from server.server_gui import MainWindow, gui_create_model, create_history_model, HistoryWindow, ConfigWindow
from server.main_window import MainWindow

conn_change = False
conflag_lock = Lock()

# @log
def arg_parser(default_port, default_address):
    """Server CLI arguments parser."""
    SERVER_LOG.debug(
        f'Parsing CLI arguments: {sys.argv}')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    gui_flag = namespace.no_gui
    SERVER_LOG.debug('Arguments parsed successfully.')
    return listen_address, listen_port, gui_flag


# @Log
def config_load():
    """Config file parser."""
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f'{dir_path}/{"server.ini"}')

    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def main():

    config = config_load()

    address, port, gui_flag = arg_parser(
        config['SETTINGS']['default_port'], config['SETTINGS']['listen_address'])
    db = ServerBase(os.path.join(
        config['SETTINGS']['database_path'], config['SETTINGS']['database_file']))
    server = MessageProcessor(address, port, db)
    server.daemon = True
    server.start()

    # print_help()
    if gui_flag:
        while True:
            command = input('Type "exit" to stop the server...')
            if command == 'exit':
                server.running = False
                server.join()
                break
    else:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(db, server, config)

        # main_window init
        # main_window.statusBar().showMessage('Server is online')
        # main_window.clients_table.setModel(gui_create_model(db))
        # main_window.clients_table.resizeColumnsToContents()
        # main_window.clients_table.resizeRowsToContents()
        #
        # # binding buttons to functions
        # main_window.refresh_btn.triggered.connect(list_update)
        # main_window.show_history_btn.triggered.connect(show_statistics)
        # main_window.config_btn.triggered.connect(server_config)
        #
        # timer = QTimer()
        # timer.timeout.connect(list_update)
        # timer.start(1000)

        # GUI start
        server_app.exec_()
        server.running = False


if __name__ == '__main__':
    main()