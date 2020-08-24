from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, Qt

from common.exceptions import ServerError
from log.client_log_config import CLIENT_LOG
from client.client_gui_designer import Ui_MainWindow
from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog


class ClientMainWindow(QMainWindow):
    def __init__(self, db, transport):
        """Initialize client main window with db and transport connections.

        Connect actions to ui template from designer.
        :param db: Client database instance
        :type db: `messenger.client.client_database.ClientBase`"""
        super().__init__()
        self.db = db
        self.transport = transport

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
        self.ui.message_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.message_list.setWordWrap(True)

        self.ui.contact_list.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.disable_input()
        self.show()

    def disable_input(self):
        self.ui.warn_label.setText('Double click a contact to start messaging')
        self.ui.msg_field.clear()
        if self.history_model:
            self.history_model.clear()

        self.ui.send_btn.setDisabled(True)
        self.ui.msg_field.setDisabled(True)

    def update_message_list(self):
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
        self.current_chat = self.ui.contact_list.currentIndex().data()
        self.set_active_user()

    def set_active_user(self):
        self.ui.warn_label.setText(f'Input a message for {self.current_chat}:')
        self.ui.send_btn.setDisabled(False)
        self.ui.msg_field.setDisabled(False)

        self.update_message_list()

    def clients_list_update(self):
        contacts_list = self.db.get_contacts()
        self.contacts_model = QStandardItemModel()
        for contact in sorted(contacts_list):
            item = QStandardItem(contact)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.contact_list.setModel(self.contacts_model)

    def add_contact_window(self):
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.db)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
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
        global remove_dialog
        remove_dialog = DelContactDialog(self.db)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
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
        message_text = self.ui.msg_field.toPlainText()
        self.ui.msg_field.clear()
        if not message_text:
            return
        try:
            self.transport.send_message(self.current_chat, message_text)
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

    # New message receiver slot
    @pyqtSlot(str)
    def message(self, sender):
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

    # Lost connection event receiver slot
    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Connection error', 'Lost connection to server!')
        self.close()

    def make_connection(self, transport):
        transport.new_message.connect(self.message)
        transport.connection_lost.connect(self.connection_lost)
