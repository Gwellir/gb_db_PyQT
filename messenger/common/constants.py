DEFAULT_ADDRESS = 'localhost'
DEFAULT_PORT = 7777
SERVER_DB_PATH = 'db/'
SERVER_DB_FILE = 'server_base.db3'
CLIENT_DB_PREFIX = 'db/client_base'
ENCODING = 'utf-8'
MAX_DATA_LENGTH = 1024
MIN_PORT_NUMBER = 1024
MAX_PORT_NUMBER = 65535
MAX_CLIENTS = 5
TIMEOUT_INTERVAL = 0.2


class Status:
    """Status messages list."""

    ONLINE = 'online'
    AFK = 'away'


class ResCodes:
    """Response numeric codes list."""

    OK = 200
    ACCEPTED = 202
    LIST_UPDATE = 205
    JSON_ERROR = 400
    AUTH_REQUIRED = 401
    AUTH_CREDS = 402
    AUTH_NOUSER = 404
    AUTH_DUPL = 409
    USER_OFFLINE = 410
    SERVER_ERROR = 500
    AUTH_PROCESS = 511


CODE_MESSAGES = {
    ResCodes.OK: 'OK',
    ResCodes.ACCEPTED: 'Request accepted',
    ResCodes.LIST_UPDATE: 'Update client lists',
    ResCodes.JSON_ERROR: 'Incorrect request',
    ResCodes.AUTH_REQUIRED: 'Authorization required',
    ResCodes.AUTH_CREDS: 'Wrong password',
    ResCodes.AUTH_NOUSER: 'User or chat doesn`t exist',
    ResCodes.AUTH_DUPL: 'This user is already connected',
    ResCodes.USER_OFFLINE: 'Target user is offline',
    ResCodes.SERVER_ERROR: 'Server error',
    ResCodes.AUTH_PROCESS: 'Auth process message'
}


class JIM:
    """Main JIM protocol json field list."""

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
    USER_LOGIN = 'user_login'
    USER_ID = 'user_id'
    DATA_LIST = 'data_list'
    DATA = 'bin'

    class Actions:
        """Sublist of actions for ACTION field."""

        PRESENCE = 'presence'
        AUTH = 'authenticate'
        JOIN = 'join'
        MESSAGE = 'msg'
        PROBE = 'probe'
        EXIT = 'exit'
        GET_CONTACTS = 'get_contacts'
        ADD_CONTACT = 'add_contact'
        DEL_CONTACT = 'del_contact'
        GET_USERS = 'get_users'
        PUBLIC_KEY_REQUEST = 'pubkey_need'

    class UserData:
        # todo simplify
        """Sublist of fields for a possible dict contained in a USER field."""

        STATUS = 'status'
        PASSWORD = 'password'
        ACCOUNT_NAME = 'account_name'
        PUBLIC_KEY = 'pubkey'

    class TypeData:
        STATUS = 'status'
