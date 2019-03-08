# -*- coding: utf-8 -*-
"""
Created on Sat Dec 09 20:43:55 2017

Pairwise Comparisons Video
Small application to scan a folder structure and copy it to the clipboard

@author: Stuart
"""
from __future__ import print_function
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog)
from qt_forms.file_scanner_ui import Ui_Form
from file_match import get_all_files
from shared_utilities import info
from time import sleep

file_extensions = {'video': ["mpg", "mp4", "mov", "mpeg", "ogg", "webm", 'flv', 'avi', 'wmv', '3gp'],
                   'pdf': ["pdf"],
                    'document': ["pdf", "docx", "doc"]}


class UploaderPanel(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.select_folder.clicked.connect(self.select_folder)
        self.ui.copy.clicked.connect(self.copy)
        self.ui.videos_radio.clicked.connect(self.set_videos)
        self.ui.pdfs_radio.clicked.connect(self.set_pdfs)
        self.ui.file_types.textChanged.connect(self.change_file_types)
        self.ui.refresh_list.clicked.connect(self.update_file_list)
        self.ui.file_list.setReadOnly(True)
        self.file_list = []
        self.file_types = []
        self.round_filetype = 'file'
        self.filters = None
        self.folder = None
    
    def update_file_types(self):
        """ Update the file types display after pressing one of the file types radio buttons """
        self.ui.file_types.textChanged.disconnect()
        self.ui.file_types.setText(', '.join(self.file_types))
        self.ui.file_types.textChanged.connect(self.change_file_types)

    def set_videos(self):
        """ User pressed the 'Videos' radio button """
        self.file_types = file_extensions['video']
        self.update_file_types()
        
    def set_pdfs(self):
        """ User pressed the 'PDFs' radio button """
        self.file_types = file_extensions['pdf']
        self.update_file_types()
    
    def change_file_types(self):
        self.file_types = [s.strip() for s in self.ui.file_types.text().split(',')]
        self.ui.videos_radio.setAutoExclusive(False)
        self.ui.pdfs_radio.setAutoExclusive(False)
        self.ui.videos_radio.setChecked(False)
        self.ui.pdfs_radio.setChecked(False)
        self.ui.videos_radio.setAutoExclusive(True)
        self.ui.pdfs_radio.setAutoExclusive(True)
        print("file types are", self.file_types)
                
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select the folder where the videos are', os.getcwd())
        print("Selecting folder", folder)
        self.folder = folder
        self.update_file_list()
        
    def update_file_list(self):
        if self.ui.filter_box.text() == "":
            self.filters = None
        else:
            self.filters = [s.strip() for s in self.ui.filter_box.text().split(',')]
        
        if self.folder:
            print("Starting to get files", self.folder, self.file_types, self.filters)
            #self.ui.file_list.clear()
            #self.ui.file_list.addItem("Searching {}".format(self.folder))
            self.ui.file_list.setText("Searching {}".format(self.folder))
            sleep(.1)
            #TODO: the folder may be large
            # get the files ?100 at a time
            # display a message "Scanning the folder"
            # and allow for the process to be interrupted.
            self.file_list = [file.replace("\\", "/") for file in
                          get_all_files(self.folder, self.file_types, self.filters)]
            print("finished getting files")
            self.update_files_display(warning=True)     
        else:
            print("No folder was selected")
        
    
    def update_files_display(self, warning=False):
        #self.ui.file_list.clear()
        if self.file_list:
            self.ui.file_list.setText('\n'.join(self.file_list))
            #self.ui.file_list.addItems(self.file_list)
            self.ui.videos_label.setText("File list ({})".format(len(self.file_list)))
        else:
            if warning:
                self.ui.file_list.setText("No matching file found in the selected folder")
            self.ui.videos_label.setText("File list")
            
        
    def validate(self, user_input):
        if not user_input['file_list']:
            return "No videos in selected folder"
        

    def get_file_type(self):
        """ Read the file type from the list of extensions """
        if all(ext in file_extensions['video'] for ext in self.file_types):
            return 'video'
        if all(ext in file_extensions['document'] for ext in self.file_types):
            return 'document'
        return 'file'
        
    def copy(self):
        """ Copy the file list to the clipboard """
        file_list = '\n'.join(self.file_list)
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard )
        cb.setText(file_list, mode=cb.Clipboard)
        info("""The file list has been copied to the clipboard""")
         
if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = UploaderPanel()
    widget.show()
    sys.exit(app.exec_())
 