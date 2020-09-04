import base64
import json

from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, Qt

from common.constants import JIM
from common.exceptions import ServerError
from log.client_log_config import CLIENT_LOG
from client.client_gui_designer import Ui_MainWindow
from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog


class ClientMainWindow(QMainWindow):
    """Main client window logic description class."""

    def __init__(self, db, transport, keys):
        """Method for initializing a client main window with db and transport connections.

        Connect actions to ui template from designer.
        :param db: Client database instance
        :type db: `client.client_database.ClientBase`
        :type transport: `client.transport.ClientTransport`"""
        super().__init__()
        self.db = db
        self.transport = transport

        self.decrypter = PKCS1_OAEP.new(keys)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.actionExit.triggered.connect(qApp.exit)

        self.ui.send_btn.clicked.connect(self.send_message)

        self.ui.add_btn.clicked.connect(self.add_contact_window)
        self.ui.actionAdd_contact.triggered.connect(self.add_contact_window)

        self.ui.del_btn.clicked.connect(self.delete_contact_window)
        self.ui.actionRemove_contact.triggered.connect(self.delete_contact_window)

        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None
        self.ui.message_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.message_list.setWordWrap(True)

        self.ui.contact_list.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.disable_input()
        self.show()

    def disable_input(self):
        """Method for disabling message input form when no user is selected."""

        self.ui.warn_label.setText('Double click a contact to start messaging')
        self.ui.msg_field.clear()
        if self.history_model:
            self.history_model.clear()

        self.ui.send_btn.setDisabled(True)
        self.ui.msg_field.setDisabled(True)

    def update_message_list(self):
        """Method for updating view of a message history for current user.

        Get last 20 messages, sorts them by time and adds to the corresponding field
        as QStandardItems while also applying simple set of styles."""

        list = sorted(self.db.get_message_history(self.current_chat), key=lambda item: item['time'])
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.message_list.setModel(self.history_model)
        self.history_model.clear()

        show_list = list[-20:]
        for item in show_list:
            if item['out'] is False:
                msg = QStandardItem(f'Incoming [{item["time"].replace(microsecond=0)}]:\n'
                                    f' {item["message"]}')
                msg.setEditable(False)
                msg.setBackground(QBrush(QColor(255, 213, 213)))
                msg.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(msg)
            else:
                msg = QStandardItem(f'Outgoing [{item["time"].replace(microsecond=0)}]:\n'
                                    f' {item["message"]}')
                msg.setEditable(False)
                msg.setBackground(QBrush(QColor(204, 255, 204)))
                msg.setTextAlignment(Qt.AlignRight)
                self.history_model.appendRow(msg)
        self.ui.message_list.scrollToBottom()

    def select_active_user(self):
        """Method for selecting a current user from the user list in UI."""

        self.current_chat = self.ui.contact_list.currentIndex().data()
        self.set_active_user()

    def set_active_user(self):
        """Method for preparing message input fields for the new selected user."""

        try:
            self.current_chat_key = self.transport.make_key_request(
                self.current_chat)
            CLIENT_LOG.debug(f'Loaded a public key for {self.current_chat}')
            if self.current_chat_key:
                self.encryptor = PKCS1_OAEP.new(
                    RSA.import_key(self.current_chat_key))
        except (OSError, json.JSONDecodeError):
            self.current_chat_key = None
            self.encryptor = None
            CLIENT_LOG.debug(f"Couldn't retrieve a key for user {self.current_chat}")

        # Если ключа нет то ошибка, что не удалось начать чат с пользователем
        if not self.current_chat_key:
            self.messages.warning(
                self, 'Error', 'No encryption key for selected user.')
            return

        self.ui.warn_label.setText(f'Input a message for {self.current_chat}:')
        self.ui.send_btn.setDisabled(False)
        self.ui.msg_field.setDisabled(False)

        self.update_message_list()

    def clients_list_update(self):
        """Method for updating a client list view in UI."""

        contacts_list = self.db.get_contacts()
        self.contacts_model = QStandardItemModel()
        for contact in sorted(contacts_list):
            item = QStandardItem(contact)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.contact_list.setModel(self.contacts_model)

    def add_contact_window(self):
        """Method for creating and binding an AddContactDialog instance."""

        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.db)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        """Action for selecting a new contact to add via AddContactDialog."""

        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        """Method for adding a new contact to both server and client databases."""

        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Server Error', str(err))
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Connection lost!')
                self.close()
            self.messages.critical(self, 'Error', 'Connection timed out!')
        else:
            self.db.add_contact(new_contact)
            new_contact_item = QStandardItem(new_contact)
            new_contact_item.setEditable(False)
            self.contacts_model.appendRow(new_contact_item)
            CLIENT_LOG.info(f'Contact added: {new_contact}')
            self.messages.information(self, 'Success', 'Contact added.')

    def delete_contact_window(self):
        """Method for creating a binding a DelContactDialog instance."""

        global remove_dialog
        remove_dialog = DelContactDialog(self.db)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        """Method for selecting a contact to remove via a DelContactDialog and then removing it both for the server and
        the client."""

        selected = item.selector.currentText()
        try:
            self.transport.del_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Server Error', err)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Connection lost!')
                self.close()
            self.messages.critical(self, 'Connection timed out!')
        else:
            self.db.del_contact(selected)
            self.clients_list_update()
            CLIENT_LOG.info(f'Contact removed: {selected}')
            self.messages.information(self, 'Success', 'Contact removed.')
            item.close()
            if selected == self.current_chat:
                self.current_chat = None
                self.disable_input()

    def send_message(self):
        """Method for getting message content from UI and sending it to the server."""

        message_text = self.ui.msg_field.toPlainText()
        self.ui.msg_field.clear()
        if not message_text:
            return

        encrypted_text = self.encryptor.encrypt(message_text.encode('utf8'))
        encrypted_text_b64 = base64.b64encode(encrypted_text)

        try:
            self.transport.send_message(
                self.current_chat,
                encrypted_text_b64.decode('ascii'))
            pass
        except ServerError as err:
            self.messages.critical(self, 'Server Error', err)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Connection lost!')
                self.close()
            self.messages.critical(self, 'Error', 'Connection timed out!')
        except (ConnectionAbortedError, ConnectionResetError):
            self.messages.critical(self, 'Error', 'Connection to server lost!')
            self.close()
        else:
            self.db.store_message(self.current_chat, message_text, outgoing=True)
            CLIENT_LOG.debug(f'Sent a message to {self.current_chat}: {message_text}')
            self.update_message_list()

    @pyqtSlot(dict)
    def message(self, message):
        """Method for processing a new incoming message signal.

        Performs decrypting a message, stores it in the DB
        and asks user to switch to a new chat in case it's needed."""
        encrypted_msg = base64.b64decode(message[JIM.MESSAGE])
        try:
            decrypted_msg = self.decrypter.decrypt(encrypted_msg)
        except (ValueError, TypeError):
            self.messages.warning(self, 'Warning!', 'Can not decode the incoming message')
            return

        self.db.store_message(message[JIM.FROM], decrypted_msg.decode('utf8'), outgoing=False)

        sender = message[JIM.FROM]
        if sender == self.current_chat:
            self.update_message_list()
        else:
            if self.db.check_user_is_contact(sender):
                if self.messages.question(self, 'New message!', f'Got new message from {sender}, open the chat?',
                                          QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()

            else:
                if self.messages.question(self, 'New message!', f'Got new message from {sender}.\n'
                                                f'Add as contact and open chat?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        """Method for processing an event of losing server connection."""

        self.messages.warning(self, 'Connection error', 'Lost connection to server!')
        self.close()

    def make_connection(self, transport):
        """Method for binding custom signals to their processors."""

        transport.new_message.connect(self.message)
        transport.connection_lost.connect(self.connection_lost)
