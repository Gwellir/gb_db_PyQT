import logging
import sys

CLIENT_LOG = logging.getLogger('client')

CONSOLE_LOGGER = logging.StreamHandler(sys.stderr)
FORMATTER = logging.Formatter("%(asctime)s %(levelname)-8s [client] %(message)s")
CONSOLE_LOGGER.setFormatter(FORMATTER)
CONSOLE_LOGGER.setLevel(logging.ERROR)
CLIENT_LOG.addHandler(CONSOLE_LOGGER)

FILE_LOGGER = logging.FileHandler('log/client.log', encoding='utf-8')
FILE_LOGGER.setFormatter(FORMATTER)
FILE_LOGGER.setLevel(logging.DEBUG)
CLIENT_LOG.addHandler(FILE_LOGGER)

CLIENT_LOG.setLevel(logging.DEBUG)
