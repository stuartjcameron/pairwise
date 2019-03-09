""" Pairwise video comparisons
Administrator app
"""


import logging
from google.appengine.api import users
from flask import Flask, render_template, request, send_file
from google.appengine.ext import ndb
import datetime
from google.appengine.ext.appstats.formatting import message
import json
from jinja2.nodes import Pair

class MyLog():
    def __init__(self):
        self.file = open('pwv/log.txt', 'w')
    
    def write(self, s):
        self.file.write(s)
    
    def close(self):
        self.file.close()


#dummy call to deal with python bug
datetime.datetime.strptime('2012-01-01', '%Y-%m-%d')

app = Flask(__name__)

@app.route('/pwv/home')
def pwv_home():
    """PWV admin home page"""
    logging.info('opened admin page')
    return "hi"

