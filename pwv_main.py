# -*- coding: utf-8 -*-
"""
Created on Mon Dec 04 18:52:47 2017

@author: Stuart
"""
from __future__ import print_function
    
import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QDialog, 
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import QTimer, QTranslator
#from PyQt5.QtCoreApplication import translate
from qt_forms.main import Ui_MainWindow
from qt_forms.settings import Ui_Settings
from shared_utilities import sign_in, warn, info, post, get
from comparisons_csv import ComparisonsCsv
from datetime import datetime


def serialize_date(d):
    if d is None:
        return None
    return d.isoformat()
    
def deserialize_date(s):
    if s is None or s == "":
        return None
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
    #return datetime.strptime(s, "YYYY-MM-DDTHH:MM:SS.mmmmmm")

    
class Settings(object):
    """ Store settings """
    
    def __init__(self):
        self._fields = ['email', 'file_folder', 'output_folder', 'min_time',
                       'round',  'token', 'rounds', 'comparison_shown',
                       'warn_time'] # also 'series_id'
        self._not_required = ['min_time', 'warn_time', 'comparison_shown']
        self._required = set(self._fields) - set(self._not_required)
        self._file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                            "pwv_settings.json")
        self._read_settings_from_file()
        
    def _read_settings_from_file(self):
        try:
            with open(self._file, 'r') as f:
                d = json.load(f)
        except IOError:
            d = {}
        if 'comparison_shown' in d:
            d['comparison_shown'] = deserialize_date(d['comparison_shown'])
        for field in self._fields:
            setattr(self, field, d.get(field, None))
            
    def reset(self):
        self._read_settings_from_file()
        
    def save(self):
        with open(self._file, 'w') as f:
            d = {k: getattr(self, k) for k in self._fields}
            if 'comparison_shown' in d:
                d['comparison_shown'] = serialize_date(d['comparison_shown'])
            json.dump(d, f)
            
    def complete(self):
        for field in self._required:
            value = getattr(self, field, None)
            if value is None or value == "":
                print("settings.complete: {}={}".format(field, value))
                return False
        print("settings.complete: everything ok")
        return True
        #TODO: consider moving the output file if the user changes the 
        # output folder in the settings panel
        # e.g. settings.output = ComparisonsCsv(old_location)
        # ...
        # settings.output.move(new_location)
                   

class JudgePanel(QMainWindow):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.play_left.clicked.connect(self.open_left)
        self.ui.play_right.clicked.connect(self.open_right)
        self.ui.submit.clicked.connect(self.submit)
        self.ui.submit.setEnabled(False)
        self.ui.play_left.setEnabled(False)
        self.ui.play_right.setEnabled(False)
        self.ui.actionPreferences.triggered.connect(self.open_settings)
        self.ui.actionView_output.triggered.connect(self.view_output)
        self.ui.actionQuit.triggered.connect(self.close)
        self.settings_panel = SettingsPanel(self)
        self.statusBar()
        self.left = None
        self.right = None
        self.pseudonym_left = None
        self.pseudonym_right = None
        self.comparison_id = None
        self.warning_timer = None
        self.filetype = "document"       # later this will be set from the round
        self.messages = {'default': {
            'warning': self.tr("{{}} seconds have passed. Please select a {file} now."),
            'label': self.tr("{File} {{number}}"),
            'instruction': self.tr('Open the {files} and select an option'),
            'open left': self.tr("Open left {file}"),
            'open right': self.tr("Open right {file}"),
            'select left': self.tr("Select left {file}"),
            'select right': self.tr("Select right {file}")},
        'video': {
            'instruction': self.tr('Play the videos and select an option'),
            'open left': self.tr("Play left {file}"),
            'open right': self.tr("Play right {file}")
            }}
        self.update_form()

    def say(self, content):
        if self.filetype in self.messages and content in self.messages[self.filetype]:
            m = self.messages[self.filetype][content]
        else:
            m = self.messages['default'][content]
        return m.format(file=self.get_filetype(),
            File=self.get_filetype().capitalize(),
            files=self.get_filetype(plural=True))
   
    
    def update_form(self):
        """ Update certain parts of form e.g. after changing file type."""
        #TODO: remove duplication of retranslateUi ...
        self.ui.play_left.setText(self.say('open left'))
        self.ui.radio_left.setText(self.say('select left'))
        self.ui.play_right.setText(self.say('open right'))
        self.ui.radio_right.setText(self.say('select right'))
        
        
    def get_filetype(self, plural=False):
        """ Returns a string for the current file type. This is needed to
        ensure the file type string gets translated. """
        if self.filetype in ["video", "document"]:
            r = self.filetype
        else:
            r = "file"
        if plural:
            r += "s"
        return self.tr(r)
    
    def start_judging(self):
        self.show()
        self.output = ComparisonsCsv(settings.output_folder)
        self.setEnabled(True)
        self.ui.submit.setEnabled(True)
        self.get_direction()
        
    def get_direction(self):
        """ Authenticate user with server and ask what to do next """
        self.ui.left_file_label.setText("")
        self.ui.right_file_label.setText("")
        self.statusBar().showMessage(self.tr('Contacting the server'))
        r = get("start_judging", settings.email, settings.token,
            params={'round': settings.round})
        print("get_direction:", r)
        self.statusBar().showMessage("")
        if r is Exception:      # may need to check connection or sign in again
            self.open_settings()
        else:
            self.do_next_thing(r['action'], r['detail'])
        
        
    def do_next_thing(self, action, detail):
        if action == 'choose round':
            self.choose_round(detail)
        elif action == 'comparison':
            self.set_choice(detail)
            self.ui.submit.setEnabled(True)
            self.ui.play_left.setEnabled(True)
            self.ui.play_right.setEnabled(True)
        elif action == 'end':
            info(self.tr("There are no more comparisons to do in this round."))
            self.ui.submit.setEnabled(False)
            self.ui.play_left.setEnabled(False)
            self.ui.play_right.setEnabled(False)
        else:
            warn(self.tr("The server returned an action that this application was not able to complete. Action: {}; detail: {}".format(action, detail)))
        
    
    def clear_form(self):
        print("clear_form")
        self.ui.radio_left.setAutoExclusive(False)
        self.ui.radio_right.setAutoExclusive(False)
        self.ui.radio_left.setChecked(False)
        self.ui.radio_right.setChecked(False)
        self.ui.radio_left.setAutoExclusive(True)
        self.ui.radio_right.setAutoExclusive(True)
        
    def start_timer(self):
        print("starting timer", settings.warn_time)
        if settings.warn_time is not None:
            #self.warning_timer = Timer(settings.warn_time, time_warning, 
            #                           kwargs={'warn_time': settings.warn_time,
            #                                   'panel': self})
            #self.warning_timer.start()
            self.warning_timer = QTimer()
            self.warning_timer.timeout.connect(self.show_time_warning)
            self.warning_timer.start(settings.warn_time * 1000)
        
    def cancel_timer(self):
        print("cancelling timer")
        if self.warning_timer is not None:
            self.warning_timer.stop()
    
    def show_time_warning(self):
        warn(self.say("warning").format(settings.warn_time))
        self.cancel_timer()
        
    def set_choice(self, comparison):
        print("set_choice", comparison)
        self.clear_form()
        self.left = comparison['left']
        self.right = comparison['right']
        self.pseudonym_left = comparison['pseudonym_left']
        self.pseudonym_right = comparison['pseudonym_right']
        self.filetype = comparison['filetype']
        self.update_form()  # need to do this because file type may have changed
        self.ui.left_file_label.setText(self.say('label').format(number=self.pseudonym_left))
        self.ui.right_file_label.setText(self.say('label').format(number=self.pseudonym_right))
        self.comparison_id = comparison['comparisonId']
        self.statusBar().showMessage(self.say('instruction'))
        settings.comparison_shown = datetime.now()
        if comparison.get('min_time') is not None:
            settings.min_time = comparison['min_time']
        if comparison.get('warn_time') is not None:
            settings.warn_time = comparison['warn_time']
        settings.save()
        self.start_timer()
            
    def choose_round(self, permitted):
        """ Cannot continue with the currently selected round. Display a warning
        and go to the settings panel. """
        warn(self.tr("The selected round is no longer available. Please choose a different one"))
        settings.rounds = permitted
        self.cancel_timer()
        self.open_settings()
        
    def open_settings(self):
        print("About to show the settings panel")
        #self.settings_panel = SettingsPanel(self)
        self.settings_panel.show()
        self.cancel_timer()
        print(self.settings_panel)
        
    def view_output(self):
        print("About to view output")
        self.output.view()
        
    def open_left(self):
        print("Playing video A!")
        #p = subprocess.Popen(["C:/Program Files (x86)/VideoLAN/VLC/vlc.exe","file:\\\Users\Dhruv\Desktop\Motivation\RiseShine.mp4"])
        self.open_file(self.left)
        
    def open_right(self):
        print("Playing video B!")
        self.open_file(self.right)
        
    def open_file(self, location):
        full_path = os.path.normpath(os.path.join(settings.file_folder, location))
        print("Trying to play video at ", full_path)
        try:
            os.startfile(full_path)
        except WindowsError as e:
            #TODO: if file is not found then warn it may have been moved
            warn(self.tr("There was an error opening the file. Please try again."))
            print(e)
        
    def write_output(self, choice):
        self.output.write(comparison_id=self.comparison_id,
                          user_email=settings.email,
                          pair_index="Not recorded",
                          left=self.left,
                          right=self.right,
                          choice=choice)
        
    def submit(self):
        print("Submitted choice")
        submission_time = (datetime.now() - settings.comparison_shown).total_seconds()
        print("Time since comparison was shown is ", submission_time)
        if settings.min_time is not None and submission_time < settings.min_time:
            warn((self.tr("Only {} seconds have passed. You cannot submit your choice until "
            "{} seconds have passed.")).format(int(submission_time), settings.min_time))
            return
        if self.ui.radio_left.isChecked():
            choice = "left"
        elif self.ui.radio_right.isChecked():
            choice = "right"
        else:
            warn(self.tr("You have not selected an option"))
            return
            #choice = None
        self.cancel_timer()
        print("Choice is ", choice)
        self.statusBar().showMessage(self.tr("Submitting choice to server"))
        r = post("complete_comparison", settings.email, settings.token,
                 json={"choice": choice, "comparison": self.comparison_id,
                       "round": settings.round})
        self.statusBar().showMessage(self.tr("Submitted choice to server"))
        while True:
            try:
                self.write_output(choice)
                break
            except IOError:
                warn(self.tr("It was not possible to save the comparison data. Please \
                     select a new location for the output folder."))
                #self.settings_panel.show()
                settings.output_folder = self.settings_panel.select_output_folder()
                settings.save()
                self.output = ComparisonsCsv(settings.output_folder)
        
        if r is not Exception:
            print("submit: response is", r)
            self.do_next_thing(r['action'], r['detail'])

            
class SettingsPanel(QDialog):
    def __init__(self, parent=None):
        global settings
        print("init settings panel")
        print("settings are:", settings)
        QWidget.__init__(self, parent)
        self.parent = parent
        self.ui = Ui_Settings()
        self.ui.setupUi(self)
        self.setEnabled(True)
        self.ui.select_output_folder.clicked.connect(self.select_output_folder)
        self.ui.select_file_folder.clicked.connect(self.select_file_folder)
        #self.populate_rounds()
        self.connected = None
        self.signed_in = (hasattr(settings, "email") and hasattr(settings, "token")
            and settings.email is not None and settings.token is not None)
        # If signed in, check the connection and update the list of rounds
        # that this user can access
        if self.signed_in:
            self.check_connection(quietly=True)
        else:
            self.update_form()
        self.ui.check_connection.clicked.connect(self.check_connection)

            
    def connection_error_quiet(self, r, e):
        def quiet_warning(message):
            print("connection_error_quiet: Warning:", message)
        return self.connection_error(r, e, w=quiet_warning)
        
    def connection_error(self, r, e, w=warn):
        """ Handle connection errors: update connected and signed in settings
        depending on what happened when we tried to connect. """
        print("There was a connection error")
        if r is None or not hasattr(r, "status_code"):
            self.connected = False
            print("SP.connection_error: Not connected and no response")
            w(self.tr("There was no response. Your computer may be offline."))
        elif r.status_code == 403:
            print("Not signed in. Error:", e)
            self.connected = True
            if self.signed_in:
                # User has saved sign in and token information but the server
                # does not accept this - either the token has expired or the
                # email does not match one in the database - so prompt
                # user to sign in again
                w(self.tr("You are connected to the server. Please sign in again."))
                self.sign_out()
            else:
                # There is no sign in information, probably meaning the user
                # has just not attempted to sign in yet.
                w(self.tr("You are connected to the server. Please sign in."))
        elif r.status_code == 404:
            print("SP.connection_error: Page not found, but this could also be due to no connection...")
            w(self.tr("It was not possible to connect to the server. Please check your connection and try again."))
            self.connected = False
        elif 400 <= r.status_code < 500:
            print("SP.connection_error: Client error")
            w(self.tr("It was not possible to connect to the server. Please check your connection and try again."))
            self.connected = False
        elif 500 <= r.status_code < 600:
            print("SP.connection_error: Server error:", r, r.status_code)
            w(self.tr("There seems to be an error with the server."))
            self.connected = True       # connected but need to fix the server...
        else:
            w(self.tr("There was a problem connecting to the server."))
            print("SP.connection_error: Warning: Some other problem not dealt with...", r, r.status_code)
        return Exception
        
        
    def check_connection(self, quietly=False):
        """ Check connection by sending token to server and requesting list
         of permitted rounds. Then update the form. A warning or info message
         will be shown unless quietly=True. """
        print("check_connection: Checking the connection")
        self.ui.check_connection.setText(self.tr("Checking connection..."))
        error_handler = self.connection_error
        if quietly:
            error_handler = self.connection_error_quiet
        r = get("get_rounds", getattr(settings, 'email', None),
                getattr(settings, 'token', None),
                error_handler=error_handler)
        if r is not Exception:
            print("check_connection: connected ok. returned:", r)
            self.connected = True
            self.signed_in = True
            settings.rounds = r['rounds']
            if not quietly:
                if settings.rounds:
                    info(self.tr("You are connected to the server."))
                else:
                    warn(self.tr("You are connected to the server, but do not currently have access to a comparison round."))
        else:
            print("check_connection: there was a connection problem")
            # (A warning message will be generated by the error handler)
        self.update_form()
          
        
    def update_form(self):
        """ Update labels and buttons reflecting settings and status 
            If not connected, disable sign in and rounds buttons
            """
        if self.connected is True:
            self.ui.connection_status.setText(self.tr("Connected to server"))
            self.ui.check_connection.setText(self.tr("Check connection / Refresh"))
            self.ui.round_select.setEnabled(True)
            self.ui.sign_in.setEnabled(True)
        elif self.connected is False:
            self.ui.connection_status.setText(self.tr("Not connected to server"))
            self.ui.check_connection.setText(self.tr("Check connection / Refresh"))
            self.ui.round_select.setEnabled(False)
            self.ui.sign_in.setEnabled(False)
        else:   # Connection has not yet been checked and self.connected is None
            self.ui.connection_status.setText("")
            self.ui.check_connection.setText(self.tr("Check server connection"))
            self.ui.round_select.setEnabled(False)
            self.ui.sign_in.setEnabled(True)
        if self.signed_in:
            self.ui.sign_in.setText(self.tr("Sign out"))
            try:
                self.ui.sign_in.clicked.disconnect()
            except TypeError:
                pass
            self.ui.sign_in.clicked.connect(self.sign_out)
            self.ui.sign_in_label.setText(self.tr("Signed in as {}").format(settings.email))
        else:
            self.ui.sign_in.setText(self.tr("Sign in"))
            
            # If connected but not signed in, then overload the earlier setting
            # and disable the round selector
            self.ui.round_select.setEnabled(False) 
            try:
                self.ui.sign_in.clicked.disconnect()
            except TypeError:
                pass
            self.ui.sign_in.clicked.connect(self.sign_in)
            self.ui.sign_in_label.setText(self.tr("You are not signed in"))
        
        # Fill in any saved settings    
        if settings.output_folder is not None:
            self.ui.output_folder.setText(settings.output_folder)
        if settings.file_folder is not None:
            self.ui.file_folder.setText(settings.file_folder)
        if settings.rounds is not None:
            self.populate_rounds()
            
            
    def sign_in(self):
        """ Sign in. Then check connection. This will also update the rounds
        information if the user has signed in successfully. """
        self.ui.sign_in.setText(self.tr("Signing in..."))
        try:
            settings.email, settings.token = sign_in()
        except:
            self.update_form()
            return
        #self.connected = True
        #self.signed_in = True
        # Checking the connection will also get the rounds, update the
        # self.connection and self.signed_in flags, and update the form
        #time.sleep(1)
        self.check_connection(quietly=True)

        
    def sign_out(self):
        settings.email = None
        settings.token = None
        self.signed_in = False
        self.update_form()
        
        
    def populate_rounds(self):
        """ Obtain the rounds from the server and add them to the drop-down """
        print("Populating the rounds...")
        round_names = [name for (id, name) in settings.rounds]
        self.ui.round_select.clear()
        self.ui.round_select.addItems([""] + round_names)
        self.ui.round_select.setCurrentIndex(self.current_round_index())
         
        
    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr('Select a folder to save output'), os.getcwd())
        print("Selecting folder", folder)
        self.ui.output_folder.setText(folder)
        return folder
        
    def select_file_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr('Select the folder where files are stored'), os.getcwd())
        print("Selecting folder", folder)
        self.ui.file_folder.setText(folder)
        return folder
        
    def validate_settings(self):
        # not currently used - use settings.complete instead
        global settings
        for k in settings._fields:
            if settings.k is None or settings.k == "":
                return "{} is not set".format(k)
        # TODO: validate email address
        # check round is okay for the given user
        
    def get_round_id(self):
        index = self.ui.round_select.currentIndex() - 1
        print("get_round_id: currentIndex=", self.ui.round_select.currentIndex())
        if index >= 0:
            return settings.rounds[index][0]
    
    def current_round_index(self):
        for i, (id, name) in enumerate(settings.rounds):
            if settings.round == id:
                return i + 1
        return 0
        
    def accept(self):
        global settings
        print("accept")
        settings.file_folder = self.ui.file_folder.text()
        settings.output_folder = self.ui.output_folder.text()
        settings.round = self.get_round_id()
        if settings.rounds == []:
            warn(self.tr("The comparisons application cannot start because you do not \
            have access to any rounds."))
        elif settings.complete():
            print("accept: settings complete, so close")
            settings.save()
            judge_panel.start_judging()
            QDialog.accept(self)
        else:
            warn(self.tr("""Please ensure all settings are configured"""))
            
    
    def reject(self):
        print("reject")
        if settings.complete():
            QDialog.reject(self)
        else:
            message = QMessageBox()
            message.setIcon(QMessageBox.Warning)
            message.setText(self.tr("""You need to configure settings before starting the pairwise comparisons application."""))
            message.setWindowTitle(self.tr("Settings needed"))
            message.addButton(self.tr("Return to settings"), QMessageBox.RejectRole)
            message.addButton(self.tr("Exit application"), QMessageBox.AcceptRole)
            confirm_quit = message.exec_()
            print("Rejected without setting anything", confirm_quit)
            if confirm_quit:
                QDialog.reject(self)
                settings.reset()
                self.parent.close()
            else:
                print("Decided not to quit")
                #TODO: figure out how to prevent it from closing here

if __name__ == "__main__":
    settings = Settings()
    print("dir", settings._file, os.getcwd())
    app = QApplication(sys.argv)
    translator = QTranslator()
    translator.load("pwv.qm")
    app.installTranslator(translator)
    judge_panel = JudgePanel()
    
    #settings_panel = SettingsPanel(judge_panel)
    if settings.complete():
        judge_panel.start_judging()
    else:
        judge_panel.show()
        judge_panel.open_settings()
        # then open the judge_panel after settings have been entered

    sys.exit(app.exec_())
 