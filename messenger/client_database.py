from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime, UniqueConstraint, \
    or_, Boolean
from sqlalchemy.orm import mapper, sessionmaker, aliased
from datetime import datetime
from pprint import pprint
from messenger.common.constants import CLIENT_DB_PREFIX


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

    def __init__(self, username):
        """Client storage initialization."""

        self.engine = create_engine(f'{CLIENT_DB_PREFIX}_{username}.db3', echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})
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

        self.metadata.create_all(self.engine)

        mapper(self.Contacts, contacts)
        mapper(self.MessageHistory, message_history)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_contact(self, contact_name):
        if self.session.query(self.Contacts).filter_by(user=contact_name).count():
            return False

        user_contact_entry = self.Contacts(contact_name)
        self.session.add(user_contact_entry)
        self.session.commit()

    def del_contact(self, contact_name):
        self.session.query(self.Contacts)\
            .filter_by(user=contact_name)\
            .delete()
        self.session.commit()

    def get_contacts(self):
        contact_list = self.session.query(self.Contacts).all()

        print(contact_list)
        return [contact.user for contact in contact_list]

    def store_message(self, target_name, content, outgoing=True):
        message_entry = self.MessageHistory(target_name, content, outgoing)
        self.session.add(message_entry)
        self.session.commit()

    def get_message_history_for_target(self, target_name):
        message_list = self.session.query(self.MessageHistory)\
            .filter_by(target=target_name).all()
        messages = [
            {
                'target': entry.target,
                'time': entry.date_time,
                'message': entry.content,
            } for entry in message_list]

        return messages