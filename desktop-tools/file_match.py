# -*- coding: utf-8 -*-
"""
Simple utility functions for grabbing files that match set criteria in a folder
and its subfolders

Created on Mon Dec 18 00:07:44 2017

@author: Stuart
"""
from __future__ import print_function
from os import walk
from os.path import join, relpath
from fnmatch import fnmatch


def get_all_files_OLD(path, extensions):
    """ Get relative paths to all of the files in the given folder, 
    including in sub-folders, which have any of the listed extensions. """
    for dirpath, dirnames, filenames in walk(path):
        for filename in filenames:
            if any(filename.lower().endswith(ext) for ext in extensions):
                yield relpath(join(dirpath, filename), path)


def check_function(extensions, filters):
    """ Return a function that returns True if a filename matches a set of
    extensions and filters """    
    
    if extensions is not None:
        extensions = [e.lower() for e in extensions]
                   
    def by_extension(filename):
        return any(filename.lower().endswith("." + ext) for ext in extensions)
        
    def by_filter(filename):
        return any(fnmatch(filename, filt) for filt in filters)
        
    def by_both(filename):
        return by_extension(filename) and by_filter(filename)
        
    if extensions and filters:
        return by_both
    elif extensions:
        return by_extension
    elif filters:
        return by_filter
    else:
        return lambda filename: True            

def get_all_files(path, extensions=None, filters=None):
    """ Get relative paths to all of the files in the given folder, 
    including in sub-folders, which have any of the listed extensions. """
    meets_criteria = check_function(extensions, filters)
    for dirpath, dirnames, filenames in walk(path):
        for filename in filenames:
            if meets_criteria(filename):
                yield relpath(join(dirpath, filename), path)                

                
def example_usage():
    my_path = "C:\Users\Stuart\Dropbox (Personal)"
    extensions = ["py"]
    files = get_all_files(my_path, extensions)
    for f in files:
        print(f)