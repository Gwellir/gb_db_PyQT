
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QLabel, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer
from server.history_window import HistoryWindow
from server.config_window import ConfigWindow
from server.add_user import RegisterUser
from server.remove_user import DelUserDialog


class MainWindow(QMainWindow):
    """Main server window."""

    def __init__(self, database, server, config):
        super().__init__()

        # Server DB
        self.db = database

        self.server_thread = server
        self.config = config

        # Exit button
        self.exitAction = QAction('Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        # List refresh button
        self.refresh_button = QAction('Update list', self)

        # Server config button
        self.config_btn = QAction('Server config', self)

        # user registration button
        self.register_btn = QAction('Register new user', self)

        # user removal button
        self.remove_btn = QAction('Remove user', self)

        # Show history button
        self.show_history_button = QAction('Client history', self)

        self.statusBar()
        self.statusBar().showMessage('Server Working')

        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_btn)
        self.toolbar.addAction(self.register_btn)
        self.toolbar.addAction(self.remove_btn)

        self.setFixedSize(800, 600)
        self.setWindowTitle('Messaging Server alpha release')

        self.label = QLabel('Connected clients list:', self)
        self.label.setFixedSize(240, 15)
        self.label.move(10, 25)

        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 45)
        self.active_clients_table.setFixedSize(780, 400)

        # Client list update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.create_users_model)
        self.timer.start(1000)

        # Binding methods to buttons
        self.refresh_button.triggered.connect(self.create_users_model)
        self.show_history_button.triggered.connect(self.show_statistics)
        self.config_btn.triggered.connect(self.server_config)
        self.register_btn.triggered.connect(self.reg_user)
        self.remove_btn.triggered.connect(self.rem_user)

        self.show()

    def create_users_model(self):
        """Active users table filling method."""

        list_users = self.db.active_users_list()
        list = QStandardItemModel()
        list.setHorizontalHeaderLabels(
            ['Client name', 'IP Address', 'Port', 'Connection time'])
        for row in list_users:
            user, ip, port, time = row
            user = QStandardItem(user)
            user.setEditable(False)
            ip = QStandardItem(ip)
            ip.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            time = QStandardItem(str(time.replace(microsecond=0)))
            time.setEditable(False)
            list.appendRow([user, ip, port, time])
        self.active_clients_table.setModel(list)
        self.active_clients_table.resizeColumnsToContents()
        self.active_clients_table.resizeRowsToContents()

    def show_statistics(self):
        """Client statistics window creator method."""

        global stat_window
        stat_window = HistoryWindow(self.db)
        stat_window.show()

    def server_config(self):
        """Server preferences window creator method."""

        global config_window
        # initializing window with current parameters
        config_window = ConfigWindow(self.config)

    def reg_user(self):
        """User registration window creator method."""

        global reg_window
        reg_window = RegisterUser(self.db, self.server_thread)
        reg_window.show()

    def rem_user(self):
        """User removal window creator method."""

        global rem_window
        rem_window = DelUserDialog(self.db, self.server_thread)
        rem_window.show()
