from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from datetime import datetime
from pprint import pprint
from messenger.common.constants import SERVER_DB_FILE


class ServerBase:
    """Server database for the messenger."""

    class Users:
        """User table representation class."""

        def __init__(self, username):
            self.name = username
            self.last_login = datetime.now()
            self.id = None

    class ActiveUsers:
        """Class for currently active users."""

        def __init__(self, user_id, ip_address, port, login_time):
            self.id = None
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time

    class LoginHistory:
        """User login history representation class."""

        def __init__(self, user, login_time, ip, port):
            self.id = None
            self.user = user
            self.login_time = login_time
            self.ip = ip
            self.port = port

    def __init__(self):
        """Storage initialization and connection."""

        self.engine = create_engine(f'{SERVER_DB_FILE}?check_same_thread=False', echo=False, pool_recycle=7200)
        self.metadata = MetaData()

        users_table = Table('users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
                            )

        active_users_table = Table('active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('users.id')),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        login_history = Table('login_history', self.metadata,
                              Column('id', Integer, primary_key=True),
                              Column('user', ForeignKey('users.id')),
                              Column('login_time', DateTime),
                              Column('ip', String),
                              Column('port', Integer)
                              )

        self.metadata.create_all(self.engine)

        mapper(self.Users, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, login_history)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def on_login(self, username, ip_address, port):
        """Stores relevant data for user login.

        Adds a new user into Users or finds an existing user and puts them into ActiveUsers.
        Also adds a LoginHistory entry."""

        print(username, ip_address, port)

        res = self.session.query(self.Users).filter_by(name=username)
        if res.count():
            user = res.first()
            user.last_login = datetime.now()
        else:
            user = self.Users(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUsers(user.id, ip_address, port, datetime.now())
        self.session.add(new_active_user)

        history_entry = self.LoginHistory(user.id, datetime.now(), ip_address, port)
        self.session.add(history_entry)

        self.session.commit()

    def on_logout(self, username):
        """Remove user from ActiveUsers on logout."""

        user_leaving = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user_leaving.id).delete()

        self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.Users.name,
            self.Users.last_login,
        )

        return query.all()

    def active_users_list(self):
        query = self.session.query(
            self.Users.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time,
        ).join(self.Users)

        return query.all()

    def login_history(self, username=None):
        query = self.session.query(
            self.Users.name,
            self.LoginHistory.login_time,
            self.LoginHistory.ip,
            self.LoginHistory.port,
        ).join(self.Users)

        if username:
            query = query.filter(self.Users.name == username)

        return query.all()


if __name__ == '__main__':
    test_db = ServerBase()

    test_db.on_login('cli1', '192.168.0.5', 1234)
    test_db.on_login('cli2', '192.168.1.23', 7777)

    pprint(test_db.active_users_list())
    test_db.on_logout('cli2')
    pprint(test_db.active_users_list())

    pprint(test_db.login_history('cli2'))
    pprint(test_db.users_list())
