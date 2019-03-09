# -*- coding: utf-8 -*-
"""
Created on Fri Jan 05 13:45:35 2018

@author: Stuart
"""

import os
import csv
from datetime import datetime


class ComparisonsCsv(object):
    """ Write pairwise comparison information to a CSV file """
    default_file_name = "pwv_output.csv"
    
    def __init__(self, folder, file_name=None):
        self.set_location(folder, file_name)
        
    def write_header(self):
        self.writer.writerow(["comparison_id", "user_email", "pair_index",
                              "left_file_name", "right_file_name", "choice",
                              "recorded_time"])
        
    def write(self, comparison_id, user_email, pair_index, left, 
                         right, choice):
        self.open()
        row_data = [comparison_id, user_email, pair_index, left, right,
                    choice, datetime.now()]
        self.writer.writerow(row_data)
        self.file.close()
    
    def set_location(self, folder, file_name=None):
        if file_name is None:
            file_name = self.default_file_name
        self.folder = folder
        self.file_location = os.path.join(folder, file_name)
        
    def move(self, new_folder, file_name=None):
        """ Change output location and move the file if it already exists """
        if file_name is None:
            file_name = self.default_file_name
        new_file_location = os.path.join(new_folder, file_name)
        if os.path.exists(self.file_location):
            os.rename(self.file_location, new_file_location)
        self.folder = new_folder
        self.file_location = new_file_location
        
    def open(self):
        """ Open file to append CSV, and write the header row if it's a new
        file """
        file_exists = os.path.exists(self.file_location)
        self.file = open(self.file_location, 'ab')
        self.writer = csv.writer(self.file)
        if not file_exists:
            self.write_header()
        
    def view(self):
        os.startfile(self.file_location)
        
