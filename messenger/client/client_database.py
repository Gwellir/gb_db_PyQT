from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime, UniqueConstraint,\
    or_, Boolean
from sqlalchemy.orm import mapper, sessionmaker, aliased
from datetime import datetime
from common.constants import CLIENT_DB_PREFIX


class ClientBase:
    """Client database for the messenger."""

    class Contacts:
        """User contacts representation class."""

        def __init__(self, user):
            self.id = None
            self.user = user

    class MessageHistory:
        """Client-side message history representation class."""

        def __init__(self, target, content, outgoing):
            self.id = None
            self.target = target
            self.content = content
            self.date_time = datetime.now()
            self.outgoing = outgoing

    class KnownUsers:
        """Client-side list of known users representation class."""

        def __init__(self, user):
            self.id = None
            self.user = user

    def __init__(self, username):
        """Client storage initialization."""

        self.engine = create_engine(
            f'sqlite:///{CLIENT_DB_PREFIX}_{username}.db3',
            echo=False,
            pool_recycle=7200,
            connect_args={
                'check_same_thread': False})
        self.metadata = MetaData()

        contacts = Table('contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', String, unique=True))

        message_history = Table('message_history', self.metadata,
                                Column('id', Integer, primary_key=True),
                                Column('target', String),
                                Column('content', String),
                                Column('date_time', DateTime),
                                Column('outgoing', Boolean))

        known_users = Table('known_users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('user', String, unique=True))

        self.metadata.create_all(self.engine)

        mapper(self.Contacts, contacts)
        mapper(self.MessageHistory, message_history)
        mapper(self.KnownUsers, known_users)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact_name):
        """Method for adding a contact to the client database."""

        if self.session.query(
                self.Contacts).filter_by(
                user=contact_name).count():
            return False

        user_contact_entry = self.Contacts(contact_name)
        self.session.add(user_contact_entry)
        self.session.commit()

    def del_contact(self, contact_name):
        """Method for removing a contact from the client database."""

        self.session.query(self.Contacts)\
            .filter_by(user=contact_name)\
            .delete()
        self.session.commit()

    def get_contacts(self):
        """Method for retrieving a full list of contacts from the client database."""

        contact_list = self.session.query(self.Contacts).all()

        print(contact_list)
        return [contact.user for contact in contact_list]

    def get_known_users(self):
        """Method for retrieving a full list of known users from the client database."""

        users_list = self.session.query(self.KnownUsers.user).all()

        return [user[0] for user in users_list]

    def add_known_users(self, user_list):
        """Method for reinitializing a list of known users."""

        self.session.query(self.KnownUsers).delete()
        for user in user_list:
            user_entry = self.KnownUsers(user)
            self.session.add(user_entry)
        self.session.commit()

    def check_user_is_known(self, user):
        """Method for checking whether a user is a known entity."""

        if self.session.query(self.KnownUsers).filter_by(user=user).count():
            return True
        else:
            return False

    def check_user_is_contact(self, user):
        """Method for checking whether a user is in contacts list."""

        if self.session.query(self.Contacts).filter_by(user=user).count():
            return True
        else:
            return False

    def store_message(self, target_name, content, outgoing=True):
        """Method for storing a message in a client history database table."""

        message_entry = self.MessageHistory(target_name, content, outgoing)
        self.session.add(message_entry)
        self.session.commit()

    def get_message_history(self, target_name):
        """Method for retrieving a client-side history for a user."""

        message_list = self.session.query(self.MessageHistory)\
            .filter_by(target=target_name).all()
        messages = [
            {
                'target': entry.target,
                'time': entry.date_time,
                'message': entry.content,
                'out': entry.outgoing,
            } for entry in message_list]

        return messages
