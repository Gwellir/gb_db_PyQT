import socket
import sys
import time
from datetime import datetime
import json
import threading
from PyQt5.QtCore import pyqtSignal, QObject

from common.constants import JIM, ResCodes
from common.decorators import Log
from common.exceptions import ServerError
from common.utils import send_message, receive_message
from log.client_log_config import CLIENT_LOG

socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, db, username):
        """Initializes client-server network interface, connects and authenticates with the server.

        :type db: :class:`messenger.client.client_database.ClientBase`
        """

        threading.Thread.__init__(self)
        QObject.__init__(self)

        self._db = db
        self.username = username
        self._socket = None
        self.connection_init(port, ip_address)

        try:
            self.user_list_update()
            self.contact_list_update()
        except OSError as err:
            if err.errno:
                CLIENT_LOG.critical(f'Connection lost.')
                raise ServerError('Server connection lost!')
            CLIENT_LOG.error('Timed out while updating user lists!')
        except json.JSONDecodeError:
            CLIENT_LOG.critical(f'Connection lost.')
            raise ServerError('Server connection lost!')

        self.running = True

    def connection_init(self, port, ip):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._socket.settimeout(5)

        connected = False
        for i in range(5):
            CLIENT_LOG.info(f'Connecting - try #{i + 1}')
            try:
                self._socket.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            CLIENT_LOG.critical(
                f"Couldn't connect to the server ({ip}:{port}).")
            raise ServerError("Couldn't connect to the server!")

        CLIENT_LOG.debug(f'Connection with server {ip}:{port} established.')

        try:
            with socket_lock:
                send_message(
                    self.form_presence_message(),
                    self._socket,
                    CLIENT_LOG)
                self.process_server_answer(
                    receive_message(self._socket, CLIENT_LOG))
        except (OSError, json.JSONDecodeError):
            CLIENT_LOG.critical(f'Connection lost.')
            raise ServerError('Server connection lost!')

        CLIENT_LOG.info('Server received our presence message.')

    def form_contacts_request(self):
        req_obj = {
            JIM.ACTION: JIM.Actions.GET_CONTACTS,
            JIM.TIME: int(datetime.now().timestamp()),
            JIM.USER_LOGIN: self.username,
        }

        CLIENT_LOG.debug(f'Formed contacts request for "{self.username}"')
        return req_obj

    def form_users_request(self):
        req_obj = {
            JIM.ACTION: JIM.Actions.GET_USERS,
            JIM.TIME: int(datetime.now().timestamp()),
            JIM.USER_LOGIN: self.username,
        }

        CLIENT_LOG.debug(f'Formed users request for "{self.username}"')
        return req_obj

    def form_auth_message(self, acc_password):
        auth_obj = {
            JIM.ACTION: JIM.Actions.AUTH,
            JIM.TIME: int(datetime.now().timestamp()),
            JIM.USER: {
                JIM.UserData.ACCOUNT_NAME: self.username,
                JIM.UserData.PASSWORD: acc_password,
            }
        }

        CLIENT_LOG.debug(f'Formed AUTH for user "{self.username}"')
        return auth_obj

    def form_presence_message(self, status='Online'):
        presence_obj = {
            JIM.ACTION: JIM.Actions.PRESENCE,
            JIM.TIME: int(datetime.timestamp(datetime.now())),
            JIM.TYPE: JIM.TypeData.STATUS,
            JIM.USER: {
                JIM.UserData.ACCOUNT_NAME: self.username,
                JIM.UserData.STATUS: status,
            },
        }

        CLIENT_LOG.debug(f'Formed PRESENCE for user "{self.username}": ""')
        return presence_obj

    def form_join_message(self, chat):
        if chat[0] != '#':
            return None
        join_obj = {
            JIM.ACTION: JIM.Actions.JOIN,
            JIM.TIME: int(datetime.now().timestamp()),
            JIM.ROOM: chat,
        }

        CLIENT_LOG.debug(
            f'Formed JOIN for user "{self.username}" to chat "{chat}"')
        return join_obj

    def form_edit_contact_message(self, contact_name, op='/add'):
        op_value = JIM.Actions.ADD_CONTACT\
            if op == '/add'\
            else JIM.Actions.DEL_CONTACT
        edit_obj = {
            JIM.ACTION: op_value,
            JIM.TIME: int(datetime.now().timestamp()),
            JIM.USER_LOGIN: self.username,
            JIM.USER_ID: contact_name,
        }

        CLIENT_LOG.debug(
            f'Formed "{op_value}" message for "{contact_name}" from "{self.username}"')
        return edit_obj

    def form_exit_message(self):
        exit_obj = {
            JIM.ACTION: JIM.Actions.EXIT,
            JIM.TIME: int(datetime.now().timestamp()),
            JIM.UserData.ACCOUNT_NAME: self.username,
        }

        return exit_obj

    def form_text_message(self, destination, content):
        message_obj = {
            JIM.ACTION: JIM.Actions.MESSAGE,
            JIM.TIME: int(datetime.now().timestamp()),
            JIM.TO: destination,
            JIM.FROM: self.username,
            JIM.MESSAGE: content,
        }

        CLIENT_LOG.debug(
            f'Formed MESSAGE from user "{self.username}" to "{destination}": "{content}"')
        return message_obj

    def process_server_answer(self, message):
        CLIENT_LOG.debug(f'Parsing server message: {message}')

        if JIM.RESPONSE in message:
            if message[JIM.RESPONSE] == 200:
                return
            elif message[JIM.RESPONSE] == 400:
                raise ServerError(f'{message[JIM.ERROR]}')
            else:
                CLIENT_LOG.debug(
                    f'Unknown response code detected {message[JIM.RESPONSE]}')

        elif JIM.ACTION in message\
                and message[JIM.ACTION] == JIM.Actions.MESSAGE\
                and JIM.FROM in message\
                and JIM.TO in message \
                and JIM.MESSAGE in message\
                and message[JIM.TO] == self.username:
            CLIENT_LOG.debug(
                f'Got a message from user - {message[JIM.FROM]}:{message[JIM.MESSAGE]}')
            self._db.store_message(
                message[JIM.FROM], message[JIM.MESSAGE], outgoing=False)
            self.new_message.emit(message[JIM.FROM])

    def contact_list_update(self):
        CLIENT_LOG.debug(
            f'Requesting contact list for the user {self.username}')
        req = self.form_contacts_request()

        with socket_lock:
            send_message(req, self._socket, CLIENT_LOG)
            ans = receive_message(self._socket, CLIENT_LOG)

        if JIM.RESPONSE in ans\
                and ans[JIM.RESPONSE] == ResCodes.ACCEPTED:
            for contact in ans[JIM.DATA_LIST]:
                self._db.add_contact(contact)
        else:
            CLIENT_LOG.error('Failed to update a contact list!')

    def user_list_update(self):
        CLIENT_LOG.debug(
            f'Requesting a list of known users for {self.username}')
        req = self.form_users_request()

        with socket_lock:
            send_message(req, self._socket, CLIENT_LOG)
            ans = receive_message(self._socket, CLIENT_LOG)

        if JIM.RESPONSE in ans\
                and ans[JIM.RESPONSE] == ResCodes.ACCEPTED:
            self._db.add_known_users(ans[JIM.DATA_LIST])
        else:
            CLIENT_LOG.error('Failed to update a list of known users!')

    def add_contact(self, contact):
        CLIENT_LOG.debug(f'Adding a contact {contact}')
        req = self.form_edit_contact_message(contact, op='/add')

        with socket_lock:
            send_message(req, self._socket, CLIENT_LOG)
            self.process_server_answer(
                receive_message(
                    self._socket, CLIENT_LOG))

    def del_contact(self, contact):
        CLIENT_LOG.debug(f'Removing a contact {contact}')
        req = self.form_edit_contact_message(contact, op='/del')

        with socket_lock:
            send_message(req, self._socket, CLIENT_LOG)
            self.process_server_answer(
                receive_message(
                    self._socket, CLIENT_LOG))

    def transport_shutdown(self):
        self.running = False
        req = self.form_exit_message()

        with socket_lock:
            try:
                send_message(req, self._socket, CLIENT_LOG)
            except OSError:
                pass

        CLIENT_LOG.debug('Transport shutting down.')
        time.sleep(0.5)

    def send_message(self, to, content):
        req = self.form_text_message(to, content)

        with socket_lock:
            send_message(req, self._socket, CLIENT_LOG)
            self.process_server_answer(
                receive_message(
                    self._socket, CLIENT_LOG))
            CLIENT_LOG.info(f'Sent a message to the user {to}')

    def run(self):
        CLIENT_LOG.debug('Server message transport launched.')
        while self.running:
            time.sleep(1)
            with socket_lock:
                try:
                    self._socket.settimeout(0.5)
                    message = receive_message(self._socket, CLIENT_LOG)
                except OSError as err:
                    if err.errno:
                        CLIENT_LOG.critical(f'Lost connection to the server!')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionResetError, ConnectionAbortedError, json.JSONDecodeError, TypeError) as err:
                    CLIENT_LOG.critical('Lost connection to the server!')
                    self.running = False
                    self.connection_lost.emit()
                else:
                    CLIENT_LOG.debug(f'Got a message: {message}')
                    self.process_server_answer(message)
                finally:
                    self._socket.settimeout(5)
