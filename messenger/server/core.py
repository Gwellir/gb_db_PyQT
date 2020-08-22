import threading
import select
import socket
import json
import hmac
import binascii
import os
from datetime import datetime

from common.constants import JIM, MAX_CLIENTS, ResCodes, CODE_MESSAGES
from common.descr import PortNumber
# from common.constants import
from log.server_log_config import SERVER_LOG
from common.utils import send_message, receive_message
from common.decorators import login_required, Log


class MessageProcessor(threading.Thread):
    """Main server class."""

    port = PortNumber()

    def __init__(self, address, port, db):
        """Init main server class.

        :type db: :class:`server.server_database.ServerBase`"""
        # receiving server parameters
        self.addr = address
        self.port = port
        self.db = db

        # runtime class fields initialization
        # bound server socket
        self.sock = None
        # connected clients (sockets) list
        self.clients = []
        self.listen_sockets = None
        self.error_sockets = None
        # used to control thread status
        self.running = True
        # names -> sockets dict
        self.names = dict()

        super().__init__()

    def run(self):
        """Main server cycle."""

        self.init_socket()

        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOG.info(f'Established connection with {client_address}')
                client.settimeout(5)
                self.clients.append(client)

            recv_data_list = []
            send_data_list = []
            error_list = []

            try:
                if self.clients:
                    recv_data_list, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                SERVER_LOG.error(f'Socket error: {err.errno}')

            if recv_data_list:
                for client_with_message in recv_data_list:
                    try:
                        self.process_client_message(
                            receive_message(client_with_message), client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        SERVER_LOG.debug(f'Exception when receiving data from client.', exc_info=err)
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        SERVER_LOG.info(f'Client {client.getpeername()} has disconnected.')
        # todo optimize
        for name in self.names:
            if self.names[name] == client:
                self.db.on_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        SERVER_LOG.info(f'Server started, address: {self.addr}:{self.port}')
        # socket setup
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen(MAX_CLIENTS)

    @staticmethod
    @Log()
    def form_response(code=ResCodes.OK):
        """Returns response object for the given code."""

        response_obj = {
            JIM.RESPONSE: code,
            JIM.TIME: int(datetime.now().timestamp()),
        }

        if code < 400 or code > 500:
            response_obj[JIM.ALERT] = CODE_MESSAGES[code]
        else:
            response_obj[JIM.ERROR] = CODE_MESSAGES[code]
        SERVER_LOG.debug(f'Formed response: {response_obj}')

        return response_obj

    def send_userlist(self, sock):
        res = {
            JIM.RESPONSE: ResCodes.ACCEPTED,
            JIM.TIME: int(datetime.now().timestamp()),
            JIM.DATA_LIST: [item[0] for item in self.db.users_list()],
        }

        send_message(res, sock, SERVER_LOG)

    @Log()
    def send_contacts(self, sock):
        res = {
            JIM.RESPONSE: ResCodes.ACCEPTED,
            JIM.TIME: int(datetime.now().timestamp()),
            JIM.DATA_LIST: self.db.get_contacts(self._users[sock].username)
        }

        send_message(res, sock, SERVER_LOG)

    def process_message(self, message):
        if message[JIM.TO] in self.names and self.names[message[JIM.TO]] in self.listen_sockets:
            try:
                send_message(message, self.names[message[JIM.TO]], SERVER_LOG)
                SERVER_LOG.info(f'Sent a message to {message[JIM.TO]} from {message[JIM.FROM]}.')
            # if send_message failed, then the target has disconnected
            except OSError:
                self.remove_client(message[JIM.TO])
        elif message[JIM.TO] in self.names and self.names[message[JIM.TO]] not in self.listen_sockets:
            SERVER_LOG.error(f'Lost connection to {message[JIM.TO]}, dropping from the active clients list')
            self.remove_client(self.names[message[JIM.TO]])
        else:
            SERVER_LOG.error(f'User {message[JIM.TO]} is not registered, cannot deliver the message.')

    @login_required
    def process_inc_message(self, message, client):
        SERVER_LOG.debug(f'Parsing client message: {message}')
        # presence message case
        if      JIM.ACTION in message\
                and message[JIM.ACTION] == JIM.Actions.PRESENCE\
                and JIM.TIME in message\
                and JIM.USER in message:
            self.authorize_user(message, client)

        # text message case
        elif    JIM.ACTION in message\
                and message[JIM.ACTION] == JIM.Actions.MESSAGE\
                and JIM.TO in message\
                and JIM.TIME in message\
                and JIM.FROM in message\
                and JIM.MESSAGE in message\
                and self.names[message[JIM.FROM]] == client:
            if message[JIM.TO] in self.names:
                self.db.store_message(message[JIM.FROM], message[JIM.TO], message[JIM.MESSAGE])
                self.process_message(message)
                try:
                    send_message(self.form_response(), client, SERVER_LOG)
                except OSError:
                    self.remove_client(client)
            else:
                try:
                    send_message(client, self.form_response(ResCodes.AUTH_NOUSER))
                except OSError:
                    pass
            return

        # exit
        elif    JIM.ACTION in message\
                and message[JIM.ACTION] == JIM.Actions.EXIT\
                and JIM.ACCOUNT_NAME in message\
                and self.names[message[JIM.ACCOUNT_NAME]] == client:
            self.remove_client(client)

        # get_contacts
        elif    JIM.ACTION in message\
                and message[JIM.ACTION] == JIM.Actions.GET_CONTACTS\
                and JIM.USER in message\
                and self.names[message[JIM.USER]] == client:
            try:
                self.send_contacts(client)
            except OSError:
                self.remove_client(client)

        # add_contact
        elif    JIM.ACTION in message\
                and message[JIM.ACTION] == JIM.Actions.ADD_CONTACT\
                and JIM.USER in message\
                and self.names[message[JIM.USER]] == client:
            self.db.add_contact(message[JIM.USER], message[JIM.USER_ID])
            try:
                send_message(self.form_response(), client, SERVER_LOG)
            except OSError:
                self.remove_client(client)

        # del_contact
        elif    JIM.ACTION in message\
                and message[JIM.ACTION] == JIM.Actions.DEL_CONTACT\
                and JIM.USER in message\
                and self.names[message[JIM.USER]] == client:
            self.db.del_contact(message[JIM.USER], message[JIM.USER_ID])
            try:
                send_message(self.form_response(), client, SERVER_LOG)
            except OSError:
                self.remove_client(client)

        # get_users
        elif    JIM.ACTION in message\
                and message[JIM.ACTION] == JIM.Actions.GET_USERS\
                and JIM.USER in message\
                and self.names[message[JIM.USER]] == client:
            try:
                res = self.form_response(ResCodes.ACCEPTED)
                res[JIM.DATA_LIST] = [item[0] for item in self.db.users_list()]
                send_message(res, client, SERVER_LOG)
            except OSError:
                self.remove_client(client)

        # public_key_request
        elif    JIM.ACTION in message\
                and message[JIM.ACTION] == JIM.Actions.PUBLIC_KEY_REQUEST\
                and JIM.USER in message:
            pubkey = self.db.get_pubkey(message[JIM.USER])
            if pubkey:
                try:
                    res = self.form_response(ResCodes.AUTH_PROCESS)
                    res[JIM.DATA] = pubkey
                    send_message(res, client, SERVER_LOG)
                except OSError:
                    self.remove_client(client)
            else:
                res = self.form_response(ResCodes.JSON_ERROR)
                res[JIM.ERROR] = 'No public key for the user'
                send_message(res, client, SERVER_LOG)

        # unknown request -> responding with error
        else:
            res = self.form_response(ResCodes.JSON_ERROR)
            try:
                send_message(res, client, SERVER_LOG)
            except OSError:
                self.remove_client(client)

    def authorize_user(self, message, sock):
        SERVER_LOG.debug(f'Started authentication process for {message[JIM.USER]}')
        # if name taken -> error
        if message[JIM.USER][JIM.UserData.ACCOUNT_NAME] in self.names.keys():
            res = self.form_response(ResCodes.JSON_ERROR)
            res[JIM.ERROR] = 'user name taken'
            SERVER_LOG.debug(f'username {message[JIM.USER][JIM.UserData.ACCOUNT_NAME]} is already taken')
            try:
                send_message(res, sock, SERVER_LOG)
            except OSError:
                SERVER_LOG.error('Socket error')
                pass
            self.clients.remove(sock)
            sock.close()
        # if not registered
        elif not self.db.check_user(message[JIM.USER][JIM.UserData.ACCOUNT_NAME]):
            res = self.form_response(ResCodes.JSON_ERROR)
            res[JIM.ERROR] = 'user is not registered'
            SERVER_LOG.debug(f'Username not recognized {message[JIM.USER][JIM.UserData.ACCOUNT_NAME]}')
            try:
                send_message(res, sock, SERVER_LOG)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            SERVER_LOG.debug('Checking password')
            auth = self.form_response(ResCodes.AUTH_PROCESS)
            rand_str = binascii.hexlify(os.urandom(64))
            auth[JIM.DATA] = rand_str.decode('ascii')

            hash = hmac.new(self.db.get_hash(message[JIM.USER][JIM.UserData.ACCOUNT_NAME]), rand_str, 'MD5')
            digest = hash.digest()
            SERVER_LOG.debug(f'Auth ready: {auth}')
            try:
                send_message(auth, sock, SERVER_LOG)
                ans = receive_message(sock, SERVER_LOG)
            except OSError as err:
                SERVER_LOG.debug('Error during authentication: ', exc_info=err)
                self.clients.remove(sock)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[JIM.DATA])
            # if the answer if correct, then add user to the active user list
            if      JIM.RESPONSE in ans\
                    and ans[JIM.RESPONSE] == ResCodes.AUTH_PROCESS\
                    and hmac.compare_digest(digest, client_digest):
                self.names[message[JIM.USER][JIM.UserData.ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(self.form_response(), sock, SERVER_LOG)
                except OSError:
                    self.remove_client(message[JIM.USER][JIM.UserData.ACCOUNT_NAME])
                # update db entries
                self.db.on_login(
                    message[JIM.USER][JIM.UserData.ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[JIM.USER][JIM.UserData.PUBLIC_KEY])
            else:
                res = self.form_response(ResCodes.JSON_ERROR)
                res[JIM.ERROR] = 'Wrong password'
                try:
                    send_message(res, sock, SERVER_LOG)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        """Method for sending response 205 (update user lists) to all clients."""
        res = self.form_response(205)
        for client in self.names:
            try:
                send_message(res, self.names[client], SERVER_LOG)
            except OSError:
                self.remove_client(self.names[client])