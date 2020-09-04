# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'client.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    """Main client window visual representation class"""

    def setupUi(self, MainWindow):
        """Method for initializing a client main window elements setup."""

        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(803, 600)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.msg_field = QtWidgets.QTextEdit(self.centralwidget)
        self.msg_field.setGeometry(QtCore.QRect(200, 500, 461, 51))
        self.msg_field.setObjectName("msg_field")
        self.send_btn = QtWidgets.QPushButton(self.centralwidget)
        self.send_btn.setGeometry(QtCore.QRect(680, 500, 101, 51))
        self.send_btn.setObjectName("send_btn")
        self.add_btn = QtWidgets.QPushButton(self.centralwidget)
        self.add_btn.setGeometry(QtCore.QRect(30, 480, 121, 31))
        self.add_btn.setObjectName("add_btn")
        self.del_btn = QtWidgets.QPushButton(self.centralwidget)
        self.del_btn.setGeometry(QtCore.QRect(30, 520, 121, 31))
        self.del_btn.setObjectName("del_btn")
        self.cl_label = QtWidgets.QLabel(self.centralwidget)
        self.cl_label.setGeometry(QtCore.QRect(20, 10, 81, 16))
        self.cl_label.setObjectName("cl_label")
        self.mh_label = QtWidgets.QLabel(self.centralwidget)
        self.mh_label.setGeometry(QtCore.QRect(200, 10, 61, 16))
        self.mh_label.setObjectName("mh_label")
        self.warn_label = QtWidgets.QLabel(self.centralwidget)
        self.warn_label.setGeometry(QtCore.QRect(210, 480, 230, 16))
        self.warn_label.setObjectName("warn_label")
        self.contact_list = QtWidgets.QListView(self.centralwidget)
        self.contact_list.setGeometry(QtCore.QRect(10, 30, 171, 441))
        self.contact_list.setObjectName("contact_list")
        self.message_list = QtWidgets.QListView(self.centralwidget)
        self.message_list.setGeometry(QtCore.QRect(200, 30, 581, 441))
        self.message_list.setObjectName("message_list")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 803, 20))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuContacts = QtWidgets.QMenu(self.menubar)
        self.menuContacts.setObjectName("menuContacts")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionAdd_contact = QtWidgets.QAction(MainWindow)
        self.actionAdd_contact.setObjectName("actionAdd_contact")
        self.actionRemove_contact = QtWidgets.QAction(MainWindow)
        self.actionRemove_contact.setObjectName("actionRemove_contact")
        self.menuFile.addAction(self.actionExit)
        self.menuContacts.addAction(self.actionAdd_contact)
        self.menuContacts.addAction(self.actionRemove_contact)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuContacts.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Messenger client"))
        self.send_btn.setText(_translate("MainWindow", "Send"))
        self.add_btn.setText(_translate("MainWindow", "Add contact"))
        self.del_btn.setText(_translate("MainWindow", "Remove contact"))
        self.cl_label.setText(_translate("MainWindow", "Contact List"))
        self.mh_label.setText(_translate("MainWindow", "Messages"))
        self.warn_label.setText(_translate("MainWindow", "Double click a contact to start messaging"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuContacts.setTitle(_translate("MainWindow", "Contacts"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.actionAdd_contact.setText(_translate("MainWindow", "Add contact"))
        self.actionRemove_contact.setText(_translate("MainWindow", "Remove contact"))
