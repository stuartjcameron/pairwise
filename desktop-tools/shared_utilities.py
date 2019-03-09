# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 20:36:55 2017

@author: Stuart
"""
from __future__ import print_function
import webbrowser
import os
import requests
from requests import ConnectionError, HTTPError, Timeout
import time
from PyQt5.QtWidgets import QMessageBox
import sys
print("SYS.ARGV", sys.argv)


TIMEOUT = 10        # seems long but sometimes takes this long using local server

if len(sys.argv) == 2 and sys.argv[1] == "-l":
    BASE_URL = "http://localhost:8080/pwva"
else:
    BASE_URL = "http://education-metrics.appspot.com/pwva"

def show_message(text, icon, title=None):
    message = QMessageBox()
    message.setIcon(getattr(QMessageBox, icon))
    message.setText(text)
    message.setStandardButtons(QMessageBox.Ok)
    if title is None:
        title = icon
    message.setWindowTitle(title)
    message.exec_()

def warn(message):
    show_message(message, "Warning")

def info(message):
    show_message(message, "Information")


def error_message(err):
    """ Return a user-friendlier message for different server issues """
    if not hasattr(err, "response") or not hasattr(err.response, "status_code"):
        return "No response"
    s = err.response.status_code
    if s == 403:
        return "Not signed in"
    elif 400 <= s < 500:
        return "Client error"
    elif 500 <= s < 600:
        return "Server error"
    else:
        return "Unknown error"


def connection_error(response, err):
    """ Default function to handle miscellaneous problems connecting to the
    server.  """
    print("connection_error: response: ", response, type(response))
    print("connection_error: Error:", err)
    if response is not None and hasattr(response, "status_code"):
        print("connection_error: status_code, reason:", response.status_code, response.reason)
        s = response.status_code
        if s == 403:
            warn("There was a problem with your sign-in. Please try signing in again")
        elif 400 <= s < 500:
            warn("There was a problem contacting the server. Please check your connection and try again.")
        elif 500 <= s < 600:
            warn("There was a server error. Please contact the administrator.")
    else:
        warn("""It was not possible to connect to the server. Please check your connection and try again.""")
    #TODO: provide more detail on the response esp whether due to lack of
    # connection, server error, or non-authorisation.
    return Exception

def make_request(method, command, user, token, data=None, error_handler=connection_error):
    r = None
    try:
        if method == "POST":
            r = requests.post(BASE_URL + "/" + command,
                      auth=(user, token),
                    json=data,
                    timeout=10)
        else:
            r = requests.get(BASE_URL + "/" + command,
                             auth=(user, token),
                             params=data,
                             timeout=10)
        r.raise_for_status()
        return r.json()
    except (ConnectionError, HTTPError, Timeout) as e:
        return error_handler(r, e)


def post(command, user, token, json=None, error_handler=connection_error):
    return make_request("POST", command, user, token, data=json, error_handler=error_handler)

def get(command, user, token, params=None, error_handler=connection_error):
    return make_request("GET", command, user, token, data=params, error_handler=error_handler)


def sign_in():
    token = os.urandom(24).encode('hex')
    webbrowser.open(BASE_URL + "/create_session?token=" + token, new=1)
    # It takes some time for the web browser to open and load the page,
    # so we need to wait at least 1s and request again if the account has
    # not yet been updated
    # Try 30 times before giving up

    for _ in range(29):
        time.sleep(1)
        response = get('start_session', 'desktop-app', token,
                       error_handler=sign_in_problem)
        if response:
            break
    else:
        response = get('start_session', 'desktop-app', token)
    if response is Exception:
        print("sign_in: Gave up on signing in")
        return
    else:
        print("sign_in: Signed in")
        return response["email"], response["token"]
    # ideally this first test session would fetch the user name?
    # could it deliver both a user name and server-created password to be
    # stored in the app??

    # TODO: need to handle timeout better.
    # Sign the user out again and show a message to try again.
    #request.get(base_url + "/test_session?session_key=" + key)
    #if everything looks okay show status as signed in, otherwise
    #show status as unable to sign in

def sign_in_problem(r, e):
    #print "sign_in_problem"
    if getattr(r, "status_code", None) == 403:
        print("sign_in_problem: Not logged in yet - keep trying. Error:", e)
    else:
        print("sign_in_problem: Some other problem...", r, getattr(r, "status_code", None))
        return connection_error(r, e)
