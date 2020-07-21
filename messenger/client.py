import sys
from datetime import datetime
from time import sleep
from socket import SOCK_STREAM, socket
from threading import Thread
from queue import Queue

from messenger.common.constants import (Client, MIN_PORT_NUMBER, MAX_PORT_NUMBER, JIMFields)
from messenger.common.exceptions import NoAddressGivenError, PortOutOfRangeError
from messenger.common.utils import parse_cli_flags, send_message, receive_message
from messenger.log.client_log_config import CLIENT_LOG
from messenger.common.decorators import Log


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


@Log()
def form_auth_message(acc_name, acc_password):
    auth_obj = {
        JIMFields.ACTION: JIMFields.ActionData.AUTH,
        JIMFields.TIME: int(datetime.now().timestamp()),
        JIMFields.USER: {
            JIMFields.UserData.ACCOUNT_NAME: acc_name,
            JIMFields.UserData.PASSWORD: acc_password,
        }
    }

    CLIENT_LOG.debug(f'Formed AUTH for user "{acc_name}"')
    return auth_obj


@Log()
def form_presence_message(acc_name, status_message):
    presence_obj = {
        JIMFields.ACTION: JIMFields.ActionData.PRESENCE,
        JIMFields.TIME: int(datetime.timestamp(datetime.now())),
        JIMFields.TYPE: JIMFields.TypeData.STATUS,
        JIMFields.USER: {
            JIMFields.UserData.ACCOUNT_NAME: acc_name,
            JIMFields.UserData.STATUS: status_message,
        },
    }

    CLIENT_LOG.debug(f'Formed PRESENCE for user "{acc_name}": "{status_message}"')
    return presence_obj


@Log()
def form_text_message(from_user, destination, content):
    message_obj = {
        JIMFields.ACTION: JIMFields.ActionData.MESSAGE,
        JIMFields.TIME: int(datetime.now().timestamp()),
        JIMFields.TO: destination,
        JIMFields.FROM: from_user,
        JIMFields.MESSAGE: content,
    }

    CLIENT_LOG.debug(f'Formed MESSAGE from user "{from_user}" to "{destination}": "{content}"')
    return message_obj


@Log()
def form_join_message(from_user, chat):
    if chat[0] != '#':
        return None
    join_obj = {
        JIMFields.ACTION: JIMFields.ActionData.JOIN,
        JIMFields.TIME: int(datetime.now().timestamp()),
        JIMFields.ROOM: chat,
    }

    CLIENT_LOG.debug(f'Formed JOIN for user "{from_user}" to chat "{chat}"')
    return join_obj


@Log()
def parse_message(message_obj):
    """
    Message content parser.

    Placeholder for future logic
    """
    key_list = message_obj.keys()
    sender = 'SERVER'
    info = None
    if JIMFields.TIME in key_list:
        msg_time = datetime.fromtimestamp(message_obj[JIMFields.TIME])
        if JIMFields.RESPONSE in key_list:
            if JIMFields.ERROR in key_list:
                CLIENT_LOG.error(f'Got ERROR from server: "{message_obj[JIMFields.ERROR]}"')
                info = f'Error: {message_obj[JIMFields.ERROR]}'
            elif JIMFields.ALERT in key_list:
                CLIENT_LOG.info(f'Got ALERT from server: "{message_obj[JIMFields.ALERT]}"')
                info = f'Alert: {message_obj[JIMFields.ALERT]}'
        elif JIMFields.ACTION in key_list:
            if message_obj[JIMFields.ACTION] == JIMFields.ActionData.PROBE:
                CLIENT_LOG.info(f'Got PROBE from server at {msg_time}"')
                info = f'Probe received at {msg_time}'
                # send_message(presence, conn, CLIENT_LOG)
            elif message_obj[JIMFields.ACTION] == JIMFields.ActionData.MESSAGE:
                CLIENT_LOG.info(f'Got MESSAGE from server: "{message_obj[JIMFields.MESSAGE]}"')
                info = f'{datetime.fromtimestamp(message_obj[JIMFields.TIME]).time()} @{message_obj[JIMFields.FROM]}:' \
                       f' {message_obj[JIMFields.MESSAGE]}'
                sender = message_obj[JIMFields.FROM]

    return sender, info


def parse_input(msg):
    default_recv = '#test'
    if msg.startswith('@'):
        parts = msg[1:].split(' ', 1)
        return parts[0], parts[1]
    else:
        return default_recv, msg


def await_input(username, conn, CLIENT_LOG):
    while True:
        msg = input('> ')
        if msg.startswith('/exit'):
            return
        to, text = parse_input(msg)
        send_message(form_text_message(username, to, text), conn, CLIENT_LOG)
        sleep(0.5)


def await_message(username, conn, CLIENT_LOG):
    while True:
        sender, answer = parse_message(receive_message(conn, CLIENT_LOG))
        if sender != 'SERVER':
            print(answer)
        elif sender != username:
            print('> ', end='')
        if answer is None:
            conn.close()
            return


if __name__ == '__main__':
    address, port, username = check_settings(sys.argv[1:])

    conn = socket(type=SOCK_STREAM)
    print(f'Client name is {username}.\n\n'
          f'Controls:\n- type any text to send message to every client\n'
          f'- type "@user message" to send message to client "user"\n'
          f'- type "/exit" to close this client')
    CLIENT_LOG.info(f'CONNECTING to server: {address}:{port}')
    conn.connect((address, port))

    presence = form_presence_message(username, Client.ACC_STATUS)
    send_message(presence, conn, CLIENT_LOG)
    sender, answer = parse_message(receive_message(conn, CLIENT_LOG))
    print(f'{sender} answered with "{answer}"')

    ui_thread = Thread(target=await_input, args=(username, conn, CLIENT_LOG,))
    server_thread = Thread(target=await_message, args=(username, conn, CLIENT_LOG,))

    ui_thread.daemon = server_thread.daemon = True

    ui_thread.start()
    server_thread.start()

    ui_thread.join()
    conn.close()
