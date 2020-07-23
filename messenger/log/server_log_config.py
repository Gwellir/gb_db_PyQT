import logging
import sys
from logging.handlers import TimedRotatingFileHandler

SERVER_LOG = logging.getLogger('server')

CONSOLE_LOGGER = logging.StreamHandler(sys.stderr)
FORMATTER = logging.Formatter("%(asctime)s %(levelname)-8s [server] %(message)s")
CONSOLE_LOGGER.setFormatter(FORMATTER)
CONSOLE_LOGGER.setLevel(logging.ERROR)
SERVER_LOG.addHandler(CONSOLE_LOGGER)

FILE_LOGGER = TimedRotatingFileHandler('log/server.log',
                                       when="d",
                                       interval=1)
FILE_LOGGER.setFormatter(FORMATTER)
FILE_LOGGER.setLevel(logging.DEBUG)
SERVER_LOG.addHandler(FILE_LOGGER)

SERVER_LOG.setLevel(logging.DEBUG)
