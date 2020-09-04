import argparse
import json
from datetime import datetime

from common.constants import DEFAULT_PORT, ENCODING, MAX_DATA_LENGTH, JIM, CODE_MESSAGES, ResCodes
from common.decorators import Log


@Log()
def parse_cli_flags(args_list):
    """Generic CLI arguments parser."""

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', help='Server address', nargs='?', type=str)
    parser.add_argument('-p', '--port', help='Server port number', nargs='?', type=int, default=DEFAULT_PORT)
    parser.add_argument('-u', '--user', help='Username to use', nargs='?', type=str)

    return parser.parse_args(args_list)


@Log()
def send_message(message_obj, connection, logger):
    """Method for sending a message over a network connection."""

    message_str = json.dumps(message_obj, ensure_ascii=False) + '\n'
    connection.send(message_str.encode(ENCODING))
    logger.info(f'-> Sent message to {connection.getpeername()}: '
                f'{message_obj}')


@Log()
def receive_message(connection, logger):
    """Method for getting a message over a network connection."""

    data = connection.recv(MAX_DATA_LENGTH)
    message_str = data.decode(ENCODING)
    try:
        message_obj = json.loads(message_str)
    except json.JSONDecodeError as e:
        logger.error(f'Could not decode message: "{message_str}"')
        raise e
        # return None

    logger.info(f'<- Received message from {connection.getpeername()}: {message_obj}')
    return message_obj


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
    # SERVER_LOG.debug(f'Formed response: {response_obj}')

    return response_obj
