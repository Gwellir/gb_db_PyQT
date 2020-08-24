from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime, UniqueConstraint, \
    or_, Text
from sqlalchemy.orm import mapper, sessionmaker, aliased
from datetime import datetime
from pprint import pprint


class ServerBase:
    """Server database for the messenger."""

    class Users:
        """User table representation class."""

        def __init__(self, username, passwd_hash):
            self.name = username
            self.last_login = datetime.now()
            self.passwd_hash = passwd_hash
            self.pubkey = None
            self.id = None

    class ActiveUsers:
        """Class for representing currently active users."""

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

    class UserContacts:
        """User contacts representation class."""

        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class MessageHistory:
        """Message history storage representation class."""

        def __init__(self, user, recipient, message):
            self.id = None
            self.user = user
            self.message = message
            self.recipient = recipient
            self.date_time = datetime.now()

    def __init__(self, db_path):
        """Storage initialization and connection."""

        self.engine = create_engine(f'sqlite:///{db_path}', echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})
        self.metadata = MetaData()

        users_table = Table('users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime),
                            Column('passwd_hash', String),
                            Column('pubkey', Text),
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

        users_contacts = Table('users_contacts', self.metadata,
                               Column('id', Integer, primary_key=True),
                               Column('user', ForeignKey('users.id')),
                               Column('contact', ForeignKey('users.id')),

                               UniqueConstraint('user', 'contact', name='contact_un'),
                               )

        message_history = Table('message_history', self.metadata,
                                Column('id', Integer, primary_key=True),
                                Column('user', ForeignKey('users.id')),
                                Column('message', String),
                                Column('recipient', ForeignKey('users.id')),
                                Column('date_time', DateTime)
                                )

        self.metadata.create_all(self.engine)

        mapper(self.Users, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, login_history)
        mapper(self.UserContacts, users_contacts)
        mapper(self.MessageHistory, message_history)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def on_login(self, username, ip_address, port, key):
        """Stores relevant data for user login.

        Adds a new user into Users or finds an existing user and puts them into ActiveUsers.
        Also adds a LoginHistory entry."""

        res = self.session.query(self.Users).filter_by(name=username)
        if res.count():
            user = res.first()
            user.last_login = datetime.now()
            if user.pubkey != key:
                user.pubkey = key
        else:
            raise ValueError(f'User "{username}" is not registered')

        new_active_user = self.ActiveUsers(user.id, ip_address, port, datetime.now())
        self.session.add(new_active_user)

        history_entry = self.LoginHistory(user.id, datetime.now(), ip_address, port)
        self.session.add(history_entry)

        self.session.commit()

    def on_logout(self, username):
        """Removes user from ActiveUsers on logout."""

        user_leaving = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user_leaving.id).delete()

        self.session.commit()

    def get_hash(self, name):
        user = self.session.query(self.Users).filter_by(name=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        user = self.session.query(self.Users).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        return self.session.query(self.Users).filter_by(name=name).count()

    def add_user(self, name, passwd_hash):
        """
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        """
        user_row = self.Users(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        # history_row = self.MessageHistory(user_row.id)
        # self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        """Метод удаляющий пользователя из базы."""
        user = self.session.query(self.Users).filter_by(name=name).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(user=user.id).delete()
        self.session.query(self.UserContacts).filter_by(user=user.id).delete()
        self.session.query(
            self.UserContacts).filter_by(
            contact=user.id).delete()
        self.session.query(self.MessageHistory).filter_by(user=user.id).delete()
        self.session.query(self.Users).filter_by(name=name).delete()
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

    def add_contact(self, user_name, contact_name):
        user = self.session.query(self.Users).filter_by(name=user_name).first()
        contact = self.session.query(self.Users).filter_by(name=contact_name).first()

        if not contact\
            or self.session.query(self.UserContacts).filter_by(user=user.id, contact=contact.id).count():
            return False

        user_contact_entry = self.UserContacts(user.id, contact.id)
        self.session.add(user_contact_entry)
        self.session.commit()

        return True

    def del_contact(self, user_name, contact_name):
        user = self.session.query(self.Users).filter_by(name=user_name).first()
        contact = self.session.query(self.Users).filter_by(name=contact_name).first()

        if not contact:
            return False

        self.session.query(self.UserContacts)\
            .filter_by(user=user.id, contact=contact.id)\
            .delete()
        self.session.commit()

        return True

    def get_contacts(self, user_name):
        user = self.session.query(self.Users).filter_by(name=user_name).one()

        contact_list = self.session.query(self.Users.name) \
            .join(self.UserContacts, self.UserContacts.contact == self.Users.id)\
            .filter(self.UserContacts.user == user.id)\
            .all()

        return [contact[0] for contact in contact_list]

    def store_message(self, sender_name, recipient_name, content):
        sender = self.session.query(self.Users).filter_by(name=sender_name).first()
        recipient = self.session.query(self.Users).filter_by(name=recipient_name).first()

        if recipient:
            message_entry = self.MessageHistory(sender.id, recipient.id, content)
            self.session.add(message_entry)
            self.session.commit()

    def get_user_message_history(self, user_name):
        user = self.session.query(self.Users).filter_by(name=user_name).first()

        senders = aliased(self.Users)
        recipients = aliased(self.Users)
        message_list = self.session.query(
                senders.name,
                recipients.name,
                self.MessageHistory.date_time,
                self.MessageHistory.message,) \
            .join(senders, self.MessageHistory.user == senders.id)\
            .join(recipients, self.MessageHistory.recipient == recipients.id)\
            .filter(
                or_(
                    self.MessageHistory.user == user.id,
                    self.MessageHistory.recipient == user.id))\
            .all()
        messages = [
            {
                'user': entry[0],
                'to': entry[1],
                'time': int(entry[2].timestamp()),
                'message': entry[3],
            } for entry in message_list]

        return messages

    def get_full_message_history(self):
        senders = aliased(self.Users)
        recipients = aliased(self.Users)
        message_list = self.session.query(
                senders.name,
                recipients.name,
                self.MessageHistory.date_time,
                self.MessageHistory.message,) \
            .join(senders, self.MessageHistory.user == senders.id)\
            .join(recipients, self.MessageHistory.recipient == recipients.id)\
            .all()
        # messages = [
        #     {
        #         'user': entry[0],
        #         'to': entry[1],
        #         'time': int(entry[2].timestamp()),
        #         'message': entry[3],
        #     } for entry in message_list]

        return message_list


if __name__ == '__main__':
    test_db = ServerBase('../db/server_base.db3')

    test_db.on_login('cli1', '192.168.0.5', 1234)
    test_db.on_login('cli2', '192.168.1.23', 7777)

    pprint(test_db.active_users_list())
    test_db.on_logout('cli2')
    pprint(test_db.active_users_list())

    pprint(test_db.login_history('cli2'))
    pprint(test_db.users_list())

    test_db.add_contact('user1', 'user0')
    test_db.add_contact('user0', 'user1')
    print(test_db.get_contacts('user1'))
    test_db.store_message('user1', 'user0', 'hello!')
    test_db.store_message('user1', 'user0', 'how are you!')
    test_db.store_message('user0', 'user1', "hey! I'm fine!")
    pprint(test_db.get_user_message_history('user1'))