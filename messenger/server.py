import configparser
import select
import sys
import os
from collections import defaultdict
from json import JSONDecodeError
from socket import SOCK_STREAM, socket, AF_INET
from datetime import datetime
from threading import Thread, Lock
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

from common.constants import (ResCodes, CODE_MESSAGES, JIM, MAX_CLIENTS,
                              TIMEOUT_INTERVAL, SERVER_PORT)
from common.utils import parse_cli_flags, send_message, receive_message
from log.server_log_config import SERVER_LOG
from common.decorators import Log
from common.descr import PortNumber, IPAddress
from meta import ServerWatcher
from server.server_database import ServerBase
from server_gui import MainWindow, gui_create_model, create_history_model, HistoryWindow, ConfigWindow

conn_change = False
conflag_lock = Lock()


class User:
    """User representation (to be moved into SQLAlchemy format)."""

    def __init__(self, client, address, username, status, last_online):
        self.client = client
        self.address = address
        self.username = username
        self.status = status
        self.last_online = last_online

    def __repr__(self):
        return f'"{self.username}"' \
               f'\nconnected from: {self.address}' \
               f'\nlast online: {self.last_online.strftime("%H:%M:%S")} with status "{self.status}"'


class Server(Thread, metaclass=ServerWatcher):
    # """Server class, coordinates user connections, identification and message exchange."""

    _address = IPAddress()
    _port = PortNumber()

    def __init__(self, server_address, server_port, db):
        """Initializes server class instance with params.

        :type db: :class:`messenger.server_database.ServerBase`"""
        self._address = server_address
        self._port = server_port
        self._sock = None

        self._db = db
        self._clients = []

        self._users = {}
        super().__init__()

    def init_socket(self):
        """Prepares a socket for incoming connections."""

        s = socket(AF_INET, SOCK_STREAM)
        s.bind((str(self._address), self._port))
        s.settimeout(TIMEOUT_INTERVAL)

        self._sock = s
        # self._sock.connect(address, port)
        self._sock.listen(MAX_CLIENTS)

        SERVER_LOG.info(f'Listening on "{self._address}":{self._port}')

    def run(self):
        """Main cycle, takes new connections, processes closed ones and operates data exchange for existing clients."""
        global conn_change
        self.init_socket()

        while True:
            try:
                client, addr = self._sock.accept()
            except OSError as e:
                pass
            else:
                # print(f'Got connection from {addr}')
                try:
                    presence_obj = receive_message(client, SERVER_LOG)
                    if self.check_presence(presence_obj):
                        user = User(client, addr, presence_obj[JIM.USER][JIM.UserData.ACCOUNT_NAME],
                                    presence_obj[JIM.USER][JIM.UserData.STATUS],
                                    datetime.fromtimestamp(presence_obj[JIM.TIME]))
                        self._db.on_login(user.username, user.address[0], user.address[1])
                        self.send_response(presence_obj, client)
                        self._users[client] = user
                        self._clients.append(client)
                        with conflag_lock:
                            conn_change = True
                        SERVER_LOG.info(f'New CLIENT: "{user.username}" from {user.address}')
                        print(f'Client connected: {user}')
                    else:
                        self.terminate_connection(client, ResCodes.JSON_ERROR)
                        continue
                except JSONDecodeError:
                    self.terminate_connection(client, ResCodes.JSON_ERROR)
                    continue
                except ConnectionResetError:
                    with conflag_lock:
                        conn_change = True
                    SERVER_LOG.info(f'Connection with {client.getpeername()} was reset')
                    continue
                # clients.append(client)
            finally:
                wait = 0
                r = []
                w = []
            try:
                r, w, e = select.select(self._clients, self._clients, [], wait)
            except:
                pass

            responses = self.read_requests(r, w)
            self.write_responses(responses, w)
            self._clients = list(self._users.keys())

    # @Log()
    def read_requests(self, r_clients, w_clients):
        """Reads incoming data from connections which have been active on this tick.

        Returns a dict of lists of responses."""

        global conn_change
        responses = defaultdict(list)
        # a dict for reversed mapping (username -> socket)
        user_dict = {self._users[user].username: user for user in self._users}

        for sock in r_clients:
            try:
                data = receive_message(sock, SERVER_LOG)
                try:
                    # if we get a message
                    if data[JIM.ACTION] == JIM.Actions.MESSAGE:
                        # send to the specified user
                        if data[JIM.TO] in user_dict:
                            self._db.store_message(self._users[sock].username,
                                                   data[JIM.TO],
                                                   data[JIM.MESSAGE])
                            responses[user_dict[data[JIM.TO]]].append(data)
                            send_message(self.form_response(), sock, SERVER_LOG)
                        # send to all users through pseudo-chat "test"
                        elif data[JIM.TO] == '#test':
                            for user in user_dict:
                                responses[user_dict[user]].append(data)
                                send_message(self.form_response(), sock, SERVER_LOG)
                        # except if the target is offline
                        else:
                            responses[user_dict[data[JIM.FROM]]] \
                                .append(self.form_response(ResCodes.USER_OFFLINE))
                    # sending user list to the client upon GET_USERS request
                    elif data[JIM.ACTION] == JIM.Actions.GET_USERS:
                        if data[JIM.USER_LOGIN] == self._users[sock].username:
                            self.send_userlist(sock)
                    # sending contacts to the client upon GET_CONTACTS request
                    elif data[JIM.ACTION] == JIM.Actions.GET_CONTACTS:
                        if data[JIM.USER_LOGIN] == self._users[sock].username:
                            self.send_contacts(sock)
                    elif data[JIM.ACTION] == JIM.Actions.DEL_CONTACT:
                        if self._db.del_contact(self._users[sock].username,
                                                data[JIM.USER_ID]):
                            send_message(self.form_response(code=ResCodes.OK), sock, SERVER_LOG)
                        else:
                            send_message(self.form_response(code=ResCodes.AUTH_NOUSER), sock, SERVER_LOG)
                    elif data[JIM.ACTION] == JIM.Actions.ADD_CONTACT:
                        if self._db.add_contact(self._users[sock].username, data[JIM.USER_ID]):
                            send_message(self.form_response(code=ResCodes.OK), sock, SERVER_LOG)
                        else:
                            send_message(self.form_response(code=ResCodes.AUTH_NOUSER), sock, SERVER_LOG)
                    # disconnect upon receiving "exit" command
                    elif data[JIM.ACTION] == JIM.Actions.EXIT:
                        print(f'Client {self._users[sock].username} has disconnected.')
                        SERVER_LOG.info(f'Client {self._users[sock].username} has disconnected.')
                        self._db.on_logout(self._users[sock].username)
                        with conflag_lock:
                            conn_change = True
                        self._users.pop(sock)
                        w_clients.remove(sock)
                except KeyError as ex:
                    pass
            # drop client from active lists upon remote disconnection
            except Exception as e:
                print(e)
                print(f'client {sock.fileno()} {sock.getpeername()} disconnected')
                SERVER_LOG.info(f'Connection with {sock.getpeername()} was reset')
                self._db.on_logout(self._users[sock].username)
                with conflag_lock:
                    conn_change = True
                self._users.pop(sock)
                w_clients.remove(sock)

        return responses

    # @Log()
    def write_responses(self, responses, w_clients):
        """Sends prepared responses to the corresponding clients."""

        for sock in w_clients:
            for data in responses[sock]:
                try:
                    send_message(data, sock, SERVER_LOG)
                except:
                    print(f'client {sock.fileno()} {sock.getpeername()} disconnected')
                    SERVER_LOG.info(f'Connection with {sock.getpeername()} was reset')
                    self._db.on_logout(self._users[sock].username)
                    sock.close()
                    self._users.pop(self._users[sock])

    @staticmethod
    @Log(raiseable=True)
    def check_presence(presence_obj):
        """Checks whether an object is a valid presence object."""
        if not presence_obj:
            return False
        else:
            try:
                if presence_obj[JIM.ACTION] == JIM.Actions.PRESENCE \
                        and presence_obj[JIM.TYPE] == JIM.TypeData.STATUS \
                        and presence_obj[JIM.USER][JIM.UserData.ACCOUNT_NAME] \
                        and presence_obj[JIM.USER][JIM.UserData.STATUS]:
                    return True
            # if some fields are missing
            except KeyError as e:
                SERVER_LOG.error(f'Could not parse PRESENCE message: {presence_obj}')
                raise e
                # return False

    @Log()
    def send_contacts(self, sock):
        res = {
            JIM.RESPONSE: ResCodes.ACCEPTED,
            JIM.TIME: int(datetime.now().timestamp()),
            JIM.DATA_LIST: self._db.get_contacts(self._users[sock].username)
        }

        send_message(res, sock, SERVER_LOG)

    @Log()
    def send_userlist(self, sock):
        res = {
            JIM.RESPONSE: ResCodes.ACCEPTED,
            JIM.TIME: int(datetime.now().timestamp()),
            JIM.DATA_LIST: [item[0] for item in self._db.users_list()],
        }

        send_message(res, sock, SERVER_LOG)

    @Log()
    def send_response(self, message_obj, client, code=ResCodes.OK, user=None):
        """Sends a message with matching response object."""

        key_list = message_obj.keys()
        if JIM.TIME in key_list:
            msg_time = datetime.fromtimestamp(message_obj[JIM.TIME])
            if JIM.ACTION in key_list:
                code = self.process_action(message_obj)
                send_message(self.form_response(code), client, SERVER_LOG)

    @Log()
    def terminate_connection(self, client, code):
        """Terminates connection after sending an error response."""

        send_message(self.form_response(code), client, SERVER_LOG)
        client.close()
        # SERVER_LOG.info(f'Client {client.getpeername()} disconnected: {CODE_MESSAGES[code]}')

    @staticmethod
    @Log()
    def form_response(code=ResCodes.OK):
        """Returns response object for the given code."""

        response_obj = {
            JIM.RESPONSE: code,
            JIM.TIME: int(datetime.now().timestamp()),
        }

        if code < 400:
            response_obj[JIM.ALERT] = CODE_MESSAGES[code]
        else:
            response_obj[JIM.ERROR] = CODE_MESSAGES[code]
        SERVER_LOG.debug(f'Formed response: {response_obj}')

        return response_obj

    @staticmethod
    @Log()
    def process_action(message_obj):
        """Simple placeholder for checking of action-bound logic."""

        if message_obj[JIM.ACTION] == JIM.Actions.PRESENCE:
            code = ResCodes.OK
        elif message_obj[JIM.ACTION] == JIM.Actions.AUTH:
            code = ResCodes.AUTH_CREDS
        elif message_obj[JIM.ACTION] == JIM.Actions.JOIN:
            code = ResCodes.AUTH_NOUSER
        elif message_obj[JIM.ACTION] == JIM.Actions.MESSAGE:
            code = ResCodes.USER_OFFLINE
        else:
            code = ResCodes.SERVER_ERROR

        return code

    @staticmethod
    @Log(raiseable=True)
    def check_settings(def_port, def_address):
        """Parse and check server settings."""

        settings = parse_cli_flags(sys.argv[1:])
        if not settings.address:
            return def_address, int(def_port)  # doesn't work now as address descriptor blocks empty address field

        return settings.address, settings.port


# @Log
def config_load():
    '''Config file parser.'''
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f'{dir_path}/{"server.ini"}')

    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(SERVER_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def main():
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_history_model(db))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def list_update():
        global conn_change
        if conn_change:
            main_window.clients_table.setModel(gui_create_model(db))
            main_window.clients_table.resizeColumnsToContents()
            main_window.clients_table.resizeRowsToContents()
            with conflag_lock:
                conn_change = False

    def server_config():
        global config_window

        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['database_path'])
        config_window.db_file.insert(config['SETTINGS']['database_file'])
        config_window.port.insert(config['SETTINGS']['default_port'])
        config_window.ip.insert(config['SETTINGS']['listen_address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['database_path'] = config_window.db_path.text()
        config['SETTINGS']['database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Error', 'Port number should be an integer!')
        else:
            config['SETTINGS']['listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['default_port'] = str(port)
                # print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'Done', 'New settings applied!')
            else:
                message.warning(config_window, 'Error', 'Enter a valid port number (1024 - 65535)!')

    config = config_load()

    address, port = Server.check_settings(
        config['SETTINGS']['default_port'], config['SETTINGS']['listen_address'])
    db = ServerBase(os.path.join(
        config['SETTINGS']['database_path'], config['SETTINGS']['database_file']))
    server = Server(address, port, db)
    server.daemon = True
    server.start()

    # print_help()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # main_window init
    main_window.statusBar().showMessage('Server is online')
    main_window.clients_table.setModel(gui_create_model(db))
    main_window.clients_table.resizeColumnsToContents()
    main_window.clients_table.resizeRowsToContents()

    # binding buttons to functions
    main_window.refresh_btn.triggered.connect(list_update)
    main_window.show_history_btn.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # GUI start
    server_app.exec_()


if __name__ == '__main__':
    main()