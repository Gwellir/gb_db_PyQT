import argparse
import json
from messenger.common.constants import SERVER_PORT, ENCODING, MAX_DATA_LENGTH
from messenger.common.decorators import Log


@Log()
def parse_cli_flags(args_list):
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', help='Server address', nargs='?', type=str)
    parser.add_argument('-p', '--port', help='Server port number', nargs='?', type=int, default=SERVER_PORT)
    parser.add_argument('-u', '--user', help='Username to use', nargs='?', type=str, default='Guest')

    return parser.parse_args(args_list)


@Log()
def send_message(message_obj, connection, logger):
    message_str = json.dumps(message_obj, ensure_ascii=False) + '\n'
    connection.send(message_str.encode(ENCODING))
    logger.info(f'-> Sent message to {connection.getpeername()}: '
                f'{message_obj}')


@Log(raiseable=True)
def receive_message(connection, logger):
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
