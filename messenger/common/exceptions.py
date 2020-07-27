from messenger.common.constants import MIN_PORT_NUMBER, MAX_PORT_NUMBER


class NoAddressGivenError(Exception):
    """Raised when no server host or address is passed to the client script."""

    pass


class ServerError(Exception):
    """Raised when the server answers with ERROR message."""

    def __init__(self, err):
        self.err = err

    def __str__(self):
        return f'Server returned an error: {self.err}'


class PortOutOfRangeError(Exception):
    """Raised when trying to set an incorrect port number through cli arguments."""

    def __init__(self, port_number):
        self.port_number = port_number

    def __str__(self):
        return f'Trying to use an incorrect port number: {self.port_number}\n' \
               f'Please use port numbers between {MIN_PORT_NUMBER} and {MAX_PORT_NUMBER}'


class InvalidIPAddress(Exception):
    """Raised when trying to start a server on malformed ip address."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f'Trying to use a malformed ip address: {self.value}'
