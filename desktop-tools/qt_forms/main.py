# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_forms/main.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(396, 239)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.left_file_label = QtWidgets.QLabel(self.centralwidget)
        self.left_file_label.setText("")
        self.left_file_label.setWordWrap(True)
        self.left_file_label.setObjectName("left_file_label")
        self.verticalLayout_2.addWidget(self.left_file_label)
        self.play_left = QtWidgets.QPushButton(self.centralwidget)
        self.play_left.setObjectName("play_left")
        self.verticalLayout_2.addWidget(self.play_left)
        self.radio_left = QtWidgets.QRadioButton(self.centralwidget)
        self.radio_left.setObjectName("radio_left")
        self.verticalLayout_2.addWidget(self.radio_left)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout_2.addWidget(self.line)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.right_file_label = QtWidgets.QLabel(self.centralwidget)
        self.right_file_label.setText("")
        self.right_file_label.setWordWrap(True)
        self.right_file_label.setObjectName("right_file_label")
        self.verticalLayout_3.addWidget(self.right_file_label)
        self.play_right = QtWidgets.QPushButton(self.centralwidget)
        self.play_right.setObjectName("play_right")
        self.verticalLayout_3.addWidget(self.play_right)
        self.radio_right = QtWidgets.QRadioButton(self.centralwidget)
        self.radio_right.setObjectName("radio_right")
        self.verticalLayout_3.addWidget(self.radio_right)
        self.horizontalLayout_2.addLayout(self.verticalLayout_3)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.submit = QtWidgets.QPushButton(self.centralwidget)
        self.submit.setObjectName("submit")
        self.horizontalLayout_3.addWidget(self.submit)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.verticalLayout_4.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 396, 26))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuSettings = QtWidgets.QMenu(self.menubar)
        self.menuSettings.setObjectName("menuSettings")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionFile = QtWidgets.QAction(MainWindow)
        self.actionFile.setObjectName("actionFile")
        self.actionQuit = QtWidgets.QAction(MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.actionChange_round = QtWidgets.QAction(MainWindow)
        self.actionChange_round.setObjectName("actionChange_round")
        self.actionPreferences = QtWidgets.QAction(MainWindow)
        self.actionPreferences.setObjectName("actionPreferences")
        self.actionView_output = QtWidgets.QAction(MainWindow)
        self.actionView_output.setObjectName("actionView_output")
        self.menuFile.addAction(self.actionView_output)
        self.menuFile.addAction(self.actionQuit)
        self.menuSettings.addAction(self.actionPreferences)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuSettings.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):    
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Pairwise comparisons"))
        self.play_left.setText(_translate("MainWindow", "Play left video"))
        self.radio_left.setText(_translate("MainWindow", "Select left video"))
        self.radio_left.setShortcut(_translate("MainWindow", "A"))
        self.play_right.setText(_translate("MainWindow", "Play right video"))
        self.radio_right.setText(_translate("MainWindow", "Select right video"))
        self.radio_right.setShortcut(_translate("MainWindow", "B"))
        self.submit.setText(_translate("MainWindow", "Submit judgement"))
        self.submit.setShortcut(_translate("MainWindow", "Return"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuSettings.setTitle(_translate("MainWindow", "Settings"))
        self.actionFile.setText(_translate("MainWindow", "File"))
        self.actionQuit.setText(_translate("MainWindow", "Quit"))
        self.actionChange_round.setText(_translate("MainWindow", "Change round..."))
        self.actionPreferences.setText(_translate("MainWindow", "Preferences..."))
        self.actionView_output.setText(_translate("MainWindow", "View output"))
