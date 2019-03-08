# -*- coding: utf-8 -*-
"""
Created on Sat Dec 09 20:43:55 2017

Pairwise Comparisons Video
Small application to upload a folder structure to the online database

@author: Stuart
"""
from __future__ import print_function
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog)
from qt_forms.uploader import Ui_Form
from file_match import get_all_files
from shared_utilities import sign_in, warn, info, post
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
        self.ui.upload.clicked.connect(self.upload)
        self.ui.sign_in.clicked.connect(self.sign_in)
        self.ui.videos_radio.clicked.connect(self.set_videos)
        self.ui.pdfs_radio.clicked.connect(self.set_pdfs)
        self.ui.file_types.textChanged.connect(self.change_file_types)
        self.ui.refresh_list.clicked.connect(self.update_file_list)
        self.file_list = []
        self.signed_in = False
        self.email = None
        self.token = None
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
        
    def sign_in(self):
        """ Toggle sign in """
        if self.signed_in:
            self.email = None
            self.token = None
            self.ui.sign_in_label.setText("You are not signed in.")
            self.ui.sign_in.setText("Sign in")
            self.signed_in = False
        else:
            self.ui.sign_in.setText("Signing in...")
            try:
                self.email, self.token = sign_in()
            except:
                self.ui.sign_in.setText("Sign in")
                return
            self.ui.sign_in_label.setText("Signed in as {}".format(self.email))
            self.ui.sign_in.setText("Sign out")
            self.signed_in = True
        
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
            self.ui.file_list.clear()
            self.ui.file_list.addItem("Searching {}".format(self.folder))
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
        self.ui.file_list.clear()
        if self.file_list:
            self.ui.file_list.addItems(self.file_list)
            self.ui.videos_label.setText("File list ({})".format(len(self.file_list)))
        else:
            if warning:
                self.ui.file_list.addItem("No matching file found in the selected folder")
            self.ui.videos_label.setText("File list")
            
        
    def validate(self, user_input):
        if not user_input['file_list']:
            return "No videos in selected folder"
        if not self.signed_in:
            return "Not signed in"
        if not self.email:
            return "No email address recorded"
        if not self.token:
            return "No session key recorded"
        if user_input['description'] == "":
            return "No description/name"

    def get_file_type(self):
        """ Read the file type from the list of extensions """
        if all(ext in file_extensions['video'] for ext in self.file_types):
            return 'video'
        if all(ext in file_extensions['document'] for ext in self.file_types):
            return 'document'
        return 'file'
        
    def upload(self):
        self.ui.upload.setText("Uploading...")
        
        user_input = {
                      'file_list': self.file_list,
                      'description': self.ui.description.toPlainText(),
                      'file_type': self.get_file_type()
                      }
        
        problem = self.validate(user_input)
        if problem:
            warn("""Please ensure all fields are filled correctly""")
        else:
            print("Uploading", user_input)
            r = post("add_file_list", user=self.email, token=self.token, json=user_input)
            if r is not Exception:
                #self.disable_form()
                info("""The file list was uploaded successfully""")
                #self.uploaded = True
                self.ready_form()
            else:
                self.ui.upload.setText("Upload")
            
            #r = requests.post(base_url + "/add_file_list", 
            #                  json=user_input,
            #                  auth=(self.email, self.token),
            #                  timeout=3)
            #print r.text
            #if r.status_code == 200 and "fileListId" in r.json():
            #    self.disable_form()
            #    info("""The file list was uploaded successfully""")
            #    self.uploaded = True
            #else:
            #    warn("""There was a server problem and the file list has not
            #    been uploaded. Please try again.""")
            #    #TODO: handle different status codes esp as internet may not be connected.
        
    def ready_form(self):
        """ Ready form to upload again """
        self.ui.upload.setText("Upload")
        self.uploaded = False
            
    def disable_form(self):
        """ Disable form after uploading - the user has to clear the form 
            to start again. (This is not currently used - instead we just
            ready the form so they can continue using it."""
        self.ui.description.setEnabled(False)
        self.ui.select_folder.setEnabled(False)
        self.ui.upload.setText("Clear form and start again")
        self.ui.upload.clicked.disconnect()
        self.ui.upload.clicked.connect(self.clear)
            
    def clear(self):
        """ Clear the form so that the user can upload a new file list """
        self.file_list = []
        self.ui.description.clear()
        self.ui.file_list.clear()
        self.ui.upload.clicked.disconnect()
        self.ui.upload.clicked.connect(self.upload)
        self.ui.description.setEnabled(True)
        self.ui.select_folder.setEnabled(True)
        self.ui.upload.setText("Upload")
        self.update_files_display()
        self.uploaded = False
        
def itin(a, b):      # currently not used
    return (item in b for item in a)
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = UploaderPanel()
    widget.show()
    sys.exit(app.exec_())
 