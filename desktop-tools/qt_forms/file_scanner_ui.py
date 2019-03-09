# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_forms/uploader2.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(437, 525)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.sign_in_section = QtWidgets.QHBoxLayout()
        self.sign_in_section.setObjectName("sign_in_section")
        self.verticalLayout.addLayout(self.sign_in_section)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.file_types_label = QtWidgets.QLabel(Form)
        self.file_types_label.setObjectName("file_types_label")
        self.horizontalLayout_9.addWidget(self.file_types_label)
        self.file_types = QtWidgets.QLineEdit(Form)
        self.file_types.setObjectName("file_types")
        self.horizontalLayout_9.addWidget(self.file_types)
        self.videos_radio = QtWidgets.QRadioButton(Form)
        self.videos_radio.setObjectName("videos_radio")
        self.horizontalLayout_9.addWidget(self.videos_radio)
        self.pdfs_radio = QtWidgets.QRadioButton(Form)
        self.pdfs_radio.setObjectName("pdfs_radio")
        self.horizontalLayout_9.addWidget(self.pdfs_radio)
        self.verticalLayout.addLayout(self.horizontalLayout_9)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.filter_label = QtWidgets.QLabel(Form)
        self.filter_label.setObjectName("filter_label")
        self.horizontalLayout_4.addWidget(self.filter_label)
        self.filter_box = QtWidgets.QLineEdit(Form)
        self.filter_box.setObjectName("filter_box")
        self.horizontalLayout_4.addWidget(self.filter_box)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.select_folder_section = QtWidgets.QHBoxLayout()
        self.select_folder_section.setObjectName("select_folder_section")
        self.videos_label = QtWidgets.QLabel(Form)
        self.videos_label.setObjectName("videos_label")
        self.select_folder_section.addWidget(self.videos_label)
        self.select_folder = QtWidgets.QPushButton(Form)
        self.select_folder.setObjectName("select_folder")
        self.select_folder_section.addWidget(self.select_folder)
        self.refresh_list = QtWidgets.QPushButton(Form)
        self.refresh_list.setObjectName("refresh_list")
        self.select_folder_section.addWidget(self.refresh_list)
        self.verticalLayout.addLayout(self.select_folder_section)
        self.file_list = QtWidgets.QTextEdit(Form)
        self.file_list.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.file_list.setObjectName("file_list")
        self.verticalLayout.addWidget(self.file_list)
        self.copy = QtWidgets.QPushButton(Form)
        self.copy.setObjectName("copy")
        self.verticalLayout.addWidget(self.copy)
        self.instruction_label = QtWidgets.QLabel(Form)
        self.instruction_label.setWordWrap(True)
        self.instruction_label.setObjectName("instruction_label")
        self.verticalLayout.addWidget(self.instruction_label)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Folder scanner"))
        self.file_types_label.setText(_translate("Form", "File types"))
        self.videos_radio.setText(_translate("Form", "Videos"))
        self.pdfs_radio.setText(_translate("Form", "PDFs"))
        self.filter_label.setText(_translate("Form", "Filter"))
        self.videos_label.setText(_translate("Form", "Files"))
        self.select_folder.setText(_translate("Form", "Select folder"))
        self.refresh_list.setText(_translate("Form", "Refresh list"))
        self.copy.setText(_translate("Form", "Copy file list to clipboard"))
        self.instruction_label.setText(_translate("Form", "Use this application to get a list of the files within a directory. This can then be copied into the Pairwise Comparisons admistrator dashboard https://education-metrics.appsport.com/pwva"))

