from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton
from PyQt5.QtCore import Qt

from log.client_log_config import CLIENT_LOG


class AddContactDialog(QDialog):
    """Client class representing a window for adding a new contact to the contact list."""

    def __init__(self, transport, db):
        """AddContactDialog window initialization and description method.

        :type transport: `client.transport.ClientTransport`
        :type db: `client.client_database.ClientBase`"""
        super().__init__()
        self.transport = transport
        self.database = db

        self.setFixedSize(350, 120)
        self.setWindowTitle('Choose a contact')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Choose a contact to add:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_refresh = QPushButton('Refresh client list', self)
        self.btn_refresh.setFixedSize(100, 30)
        self.btn_refresh.move(60, 60)

        self.btn_ok = QPushButton('Add', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.list_possible_contacts()

        self.btn_refresh.clicked.connect(self.update_possible_contacts)

    def list_possible_contacts(self):
        """Method for filling a list with possible new contacts.

        Fills selector field with a difference between a complete user list and added contacts
        (also excludes current user name)."""
        self.selector.clear()

        contact_list = set(self.database.get_contacts())
        users_list = set(self.database.get_known_users())

        users_list.remove(self.transport.username)

        self.selector.addItems(users_list - contact_list)

    def update_possible_contacts(self):
        """Method for updating a complete user list from the server."""
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            CLIENT_LOG.debug('Updated userlist from the server')
            self.list_possible_contacts()
