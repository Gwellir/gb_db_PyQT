from ipaddress import ip_address

from log.server_log_config import SERVER_LOG
from log.client_log_config import CLIENT_LOG
from common.constants import MIN_PORT_NUMBER, MAX_PORT_NUMBER
from common.exceptions import PortOutOfRangeError, InvalidIPAddress


class PortNumber:
    """Descriptor for valid server port numbers."""

    def __set__(self, instance, value):
        """Check whether a port number lies within range of publicly accessible port numbers."""
        # print(instance)
        logger = SERVER_LOG
        if not MIN_PORT_NUMBER <= value <= MAX_PORT_NUMBER:
            logger.critical(f'Trying to launch a server using an invalid port number: {value}\n')
            raise PortOutOfRangeError(value)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class IPAddress:
    """Descriptor for valid server ip address."""

    def __set__(self, instance, value):
        logger = SERVER_LOG
        try:
            ip_addr = ip_address(value)
            instance.__dict__[self.name] = ip_addr
        except ValueError:
            logger.critical(f'Trying to bind server to an incorrect IP: {value}')
            raise InvalidIPAddress(value)

    def __set_name__(self, owner, name):
        self.name = name
