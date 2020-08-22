import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler

SERVER_LOG = logging.getLogger('server')

CONSOLE_LOGGER = logging.StreamHandler(sys.stderr)
FORMATTER = logging.Formatter("%(asctime)s %(levelname)-8s [server] %(message)s")
CONSOLE_LOGGER.setFormatter(FORMATTER)
CONSOLE_LOGGER.setLevel(logging.ERROR)
SERVER_LOG.addHandler(CONSOLE_LOGGER)

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'server.log')
FILE_LOGGER = TimedRotatingFileHandler(path,
                                       when="d",
                                       interval=1)
FILE_LOGGER.setFormatter(FORMATTER)
FILE_LOGGER.setLevel(logging.DEBUG)
SERVER_LOG.addHandler(FILE_LOGGER)

SERVER_LOG.setLevel(logging.DEBUG)
