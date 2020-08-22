import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # exit btn
        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(qApp.quit)

        # refresh btn
        self.refresh_btn = QAction('Update clients', self)

        # configuration button
        self.config_btn = QAction('Server config', self)

        # show history button
        self.show_history_btn = QAction('Client history', self)

        # Status bar
        self.statusBar()

        # toolbar
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(exitAction)
        self.toolbar.addAction(self.refresh_btn)
        self.toolbar.addAction(self.show_history_btn)
        self.toolbar.addAction(self.config_btn)

        # main window geometry parameters
        self.setFixedSize(800, 600)
        self.setWindowTitle('Python messenger project')

        # client list label
        self.label = QLabel('List of connected clients:', self)
        self.label.setFixedSize(240, 15)
        self.label.move(10, 25)

        # client list element
        self.clients_table = QTableView(self)
        self.clients_table.setFixedSize(780, 400)
        self.clients_table.move(10, 45)

        self.show()


class HistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # window config
        self.setWindowTitle('Clients history')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # close button
        self.close_btn = QPushButton('Close', self)
        self.close_btn.move(250, 650)
        self.close_btn.clicked.connect(self.close)

        # history list
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Server configuration')
        self.setFixedSize(365, 260)

        self.db_path_label = QLabel('Path to DB file:', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        self.db_path = QLineEdit(self)
        self.db_path.move(10, 30)
        self.db_path.setFixedSize(250, 20)
        self.db_path.setReadOnly(True)

        self.db_path_select = QPushButton('Browse...', self)
        self.db_path_select.move(275, 28)

        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        self.db_file_label = QLabel('DB file name:', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        self.port_label = QLabel('Port number for incoming connections:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(150, 20)

        self.ip_label = QLabel('IP address to bind to:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        self.ip_label_note = QLabel(' leave this field blank to bind server\nto all available addresses')
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        self.save_btn = QPushButton('Save', self)
        self.save_btn.move(190, 220)

        self.close_btn = QPushButton('Close', self)
        self.close_btn.move(275, 220)
        self.close_btn.clicked.connect(self.close)

        self.show()


def gui_create_model(db):
    """Creates a QStandardItemModel table based on active clients.

    :param db: ServerBase instance
    :type db: :class:`messenger.server_database.ServerBase`
    :return: QStandardItemModel instance
    :rtype: QStandardItemModel
    """

    userlist = db.active_users_list()
    list_model = QStandardItemModel()
    list_model.setHorizontalHeaderLabels(['Username', 'IP Address', 'Port', 'Connection time'])
    for row in userlist:
        user, ip, port, time = row
        user = QStandardItem(user)
        user.setEditable(False)
        ip = QStandardItem(ip)
        ip.setEditable(False)
        port = QStandardItem(str(port))
        port.setEditable(False)
        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)
        list_model.appendRow([user, ip, port, time])

    return list_model


def create_history_model(db):
    """Creates a QStandardItemModel table based on message history contents.

    :param db: ServerBase instance
    :type db: :class:`messenger.server_database.ServerBase`
    :return: QStandardItemModel instance
    :rtype: QStandardItemModel
    """

    history_list = db.get_full_message_history()

    history_model = QStandardItemModel()
    history_model.setHorizontalHeaderLabels(['From', 'To', 'Time', 'Message'])
    for row in history_list:
        sender, receiver, time, msg = row
        sender = QStandardItem(sender)
        sender.setEditable(False)
        receiver = QStandardItem(receiver)
        receiver.setEditable(False)
        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)
        msg = QStandardItem(msg)
        msg.setEditable(False)
        history_model.appendRow([sender, receiver, time, msg])

    return history_model
