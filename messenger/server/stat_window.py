from PyQt5.QtWidgets import QDialog, QPushButton, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


class StatWindow(QDialog):
    """User statistics representation window class."""

    def __init__(self, database):
        super().__init__()

        self.database = database
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Client statistics')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.close_button = QPushButton('Close', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        self.stat_table = QTableView(self)
        self.stat_table.move(10, 10)
        self.stat_table.setFixedSize(580, 620)

        self.create_history_model()

    def create_history_model(self):
        """Statistics data filling method."""
        history_list = self.database.get_full_message_history()

        list = QStandardItemModel()
        list.setHorizontalHeaderLabels(
            ['User', 'Recipient', 'Time', 'Message text', ])
            # ['Client name', 'Last time logged in', 'Messages sent', 'Messages received'])
        for row in history_list:
            user, target, time_, text = row
            user = QStandardItem(user)
            user.setEditable(False)
            text = QStandardItem(str(text))
            text.setEditable(False)
            target = QStandardItem(str(target))
            target.setEditable(False)
            time_ = QStandardItem(str(time_.replace(microsecond=0)))
            time_.setEditable(False)
            list.appendRow([user, target, time_, text])
        self.stat_table.setModel(list)
        self.stat_table.resizeColumnsToContents()
        self.stat_table.resizeRowsToContents()
