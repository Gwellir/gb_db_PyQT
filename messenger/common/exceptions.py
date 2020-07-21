class NoAddressGivenError(Exception):
    """Raised when no server or address is passed to the client script"""
    pass


class PortOutOfRangeError(Exception):
    """Raised when trying to set an incorrect port number through cli arguments"""
    pass
