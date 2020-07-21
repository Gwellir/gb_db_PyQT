from enum import Enum

SERVER_ADDRESS = 'localhost'
SERVER_PORT = 7777
ENCODING = 'utf-8'
MAX_DATA_LENGTH = 1024
MIN_PORT_NUMBER = 1024
MAX_PORT_NUMBER = 65535
MAX_CLIENTS = 5
TIMEOUT_INTERVAL = 0.2


class Status:
    ONLINE = 'online'
    AFK = 'away'


class ServerCodes:
    OK = 200
    JSON_ERROR = 400
    AUTH_REQUIRED = 401
    AUTH_CREDS = 402
    AUTH_NOUSER = 404
    AUTH_DUPL = 409
    USER_OFFLINE = 410
    SERVER_ERROR = 500


CODE_MESSAGES = {
    ServerCodes.OK: 'OK',
    ServerCodes.JSON_ERROR: 'Incorrect request',
    ServerCodes.AUTH_REQUIRED: 'Authorization required',
    ServerCodes.AUTH_CREDS: 'Wrong password',
    ServerCodes.AUTH_NOUSER: 'User or chat doesn`t exist',
    ServerCodes.AUTH_DUPL: 'This user is already connected',
    ServerCodes.USER_OFFLINE: 'Target user is offline',
    ServerCodes.SERVER_ERROR: 'Server error',
}


class JIMFields:
    TIME = 'time'
    RESPONSE = 'response'
    ERROR = 'error'
    ALERT = 'alert'
    ACTION = 'action'
    USER = 'user'
    TYPE = 'type'
    TO = 'to'
    FROM = 'from'
    MESSAGE = 'message'
    ROOM = 'room'

    class ActionData:
        PRESENCE = 'presence'
        AUTH = 'authenticate'
        JOIN = 'join'
        MESSAGE = 'msg'
        PROBE = 'probe'

    class UserData:
        ACCOUNT_NAME = 'account_name'
        STATUS = 'status'
        PASSWORD = 'password'

    class TypeData:
        STATUS = 'status'


class Client:
    ACC_NAME = 'test'
    ACC_PASSWORD = '12345678'
    ACC_STATUS = Status.ONLINE
