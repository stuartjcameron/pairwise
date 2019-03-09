""" Pairwise video comparisons
Administrator app
"""

"""
# TODO here
Most UI logic will be done in JS
This app has to serve database requests, in json:
- List of comparisons in reverse-date order, filtered by round or judge
- List of rounds
- List of judges
- List of video lists
- Current user information
But also want to allow multiple requests to be combined e.g. serve the rounds and the judges at once.

And perform the following functions:
- Create new judge (+ invitation process to verify the judge)
- Create new round
- Link judge(s) to a round
- Link a video list to a round
- Create new incomplete comparison for a given round and judge
- Complete a comparison for a given round, judge and outcome; and create a new one
"""

import logging
from google.appengine.api import users
from flask import Flask, render_template, request, send_file
from google.appengine.ext import ndb
import datetime
from google.appengine.ext.appstats.formatting import message
import json
from jinja2.nodes import Pair

#dummy call to deal with python bug
datetime.datetime.strptime('2012-01-01', '%Y-%m-%d')

app = Flask(__name__)


class NotLoggedInError(Exception):
    pass

class NoPermissionError(Exception):
    pass

# Round will be parent of comparisons
class Round(ndb.Model):
    judges = ndb.IntegerProperty(repeated=True)
    created = ndb.DateTimeProperty()
    modified = ndb.DateTimeProperty()
    creator = ndb.IntegerProperty()

class Comparison(ndb.Model):
    comparison_number = ndb.IntegerProperty()
    judge = ndb.IntegerProperty()
    left = ndb.IntegerProperty()
    right = ndb.IntegerProperty()
    shown_time = ndb.DateTimeProperty()
    choice_time = ndb.DateTimeProperty()
    #round_number = ndb.IntegerProperty()
    result = ndb.IntegerProperty()          # 1 for left, 2 for right

class UserAccount(ndb.Model):
    user_id = ndb.StringProperty()  # to store the user id https://cloud.google.com/appengine/docs/standard/python/users/userobjects
    admin = ndb.BooleanProperty()
    name = ndb.StringProperty()
    rounds = ndb.StringProperty(repeated=True)
    verified = ndb.BooleanProperty()
    verify_number = ndb.IntegerProperty()
    
    @classmethod
    def get_current(cls, admin_required=False):
        """ Get account info for the current user and verify they are registered and (if needed) an admin """
        user = users.get_current_user()
        if not user:
            raise NotLoggedInError
        account = cls.get_by_user(user)
        if not account:
            raise NoPermissionError
        if admin_required and not account.admin:
            raise NoPermissionError
        return account
    
    @classmethod
    def get_by_user(cls, user):
        """ Get account info for the specified user. Returns an object that merges the info from User
        with the info in the UserAccount DB. """
        r = cls.query().filter(cls.user_id == user.user_id()).get() 
        if r:
            r.nickname = user.nickname()
            r.email = user.email()
            r.logout = users.create_logout_url(request.path),
            r.logout_output = users.create_logout_url('pwv/')
        return r

def check_user(admin_required=False):
    """ Check if user is logged in and has permission to use the app.
    Returns a tuple with 1. dictionary of user info, if logged in; 
        2. whether okay to proceed (user is logged in and has permission)
        3. message if not okay
    """
    
    user = UserAccount.get_current()
    if user:
        if user.registered and (user.admin or not admin_required):
            return user, True, None
        else:
            message = """You are signed in to Google accounts as {}. However you do not 
            have permission to access this page. <br />Click <a href="{}">here</a> to 
            sign out and then sign in as a different user.""".format(user.nickname, user.logout)
            return user, False, message
    else:
        login_url = users.create_login_url(request.path)
        message = """This is the Pairwise Comparisons Pilot Application. You need to sign in with 
            a recognised Google account to access the site. <br /><a href="{}">Click here to be
            redirected to the Google sign-in page.</a> """.format(login_url)
        return None, False, message


def no_permission(user):
    return """You are signed in to Google accounts as {}. However you do not 
            have permission to access this page. <br />Click <a href="{}">here</a> to 
            sign out and then sign in as a different user.""".format(user.nickname, user.logout)


@app.route('/pwva/add_user')
def add_user():
    """ Send an email invitation to the specified address, and add the user as unverified.
        Return True if successful, False if not """
    logging.info("Inviting new user")
    user = UserAccount.get_current(admin_required=True)
    new_account = UserAccount()
    new_user = users.User(request.args['email'])
    new_account.user_id = new_user.user_id()
    new_account.put()
    #todo - check if user email is already in database
    #todo - add other properties from the page: name
    
#TODO: DISABLE THIS AFTER PRODUCTION... OR MAKE IT WORK FOR ME ONLY
@app.route('/pwva/add_current_user_as_admin')
def make_admin():
    logging.info("Making current user admin")
    user = users.get_current_user()
    account = UserAccount()
    account.user_id = user.user_id()
    account.admin = True
    key = account.put()
    return "Added user {} with ID {}".format(user.nickname(), key.id())

 
@app.route('/pwva/get_comparisons')
def get_comparisons():
    user = UserAccount.get_current()
    if 'judge' in request.args:
        judge = int(request.args['judge'])
        logging.info('comparisons for judge', judge)
        comparisons = Comparison.query().order(-Comparison.choice_time) # add filter    
    elif 'round' in request.args:
        round_id = int(request.args['round'])
        ancestor_key = ndb.Key("Round", round_id)
        logging.info('comparisons for roudn', round_id)
        comparisons = Comparison.query(ancestor=ancestor_key).order(-Comparison.choice_time)
    else:
        logging.info('all comparisons coming')
        comparisons = Comparison.query().order(-Comparison.choice_time)
    
    # TODO: add number to return and start item; also want count (as a separate function?)    
    return comparisons # hope it jsonifies?

@app.route('/pwva/add_comparison/<round_id>')
def add_comparison():
    """ Make a new incomplete comparison for a given round and the current user.
    It will not be possible to add more than one incomplete comparison for a round and user.
    Return the path to the left video and path to the right video.
    """
    user, okay, message = check_user()
    if not okay:
        return message  # might be more appropriate to respond with 404?
    #TODO: allow verify=true => check if entry exists before adding it.
    required = ['result', 'left', 'right', 'shownTime', 'choiceTime', 'comparisonNumber', 'id']
    not_found = set(required) - set(request.args)
    if not_found:
        return "Required argument {} is missing".format(' '.join(list(not_found))), 400
    
    comparison_id = request.args['id']
    round_number = int(request.args['round'])
    verify_status = 'new record'
    if 'verify' in request.args and request.args['verify'] == "true":
        comparison = Comparison.get_by_id(parent=ndb.Key("Round", round_number), id=comparison_id)
        logging.info("Verifying if record {} already exists. Result: {}".format(comparison_id, comparison))
        if comparison:      # Just verifying an existing record
            #TODO: check all information is the same?
            return json.dumps({"verified": True, "currentRound": get_round()})
        else:
            verify_status = 'verified record not found'
    comparison = Comparison(parent=ndb.Key("Round", round_number), id=comparison_id)
    if request.args['result'] == 'left':
        result = 1
    else:
        result = 2
    left = int(request.args['left'])
    right = int(request.args['right'])
    comparison.populate(
        judge = user['number'],
        result = result,
        shown_time = json_to_datetime(request.args['shownTime']),
        choice_time = json_to_datetime(request.args['choiceTime']),
        comparison_number = int(request.args['comparisonNumber']),
        left = left,
        right = right)
    current_round = get_round()
    judged_twice = update_judged_record(round_number, left, right)
    
    # If the round has changed, get the record for the new round instead of the old one
    if current_round != round_number:
        judged_twice = get_judged_record(current_round)
    #how_often = count_comparisons(left, right, current_round)
    comparison.put()
    #TODO: if round has changed, need to check how often each pair has been judged in the new round
      
    #return "Written to database: {}. Current round is {}. Pair judged {} times in current round".format(comparison.__dict__, current_round, how_often)
    output = {"saved": True, 
              "currentRound": current_round,
              "left": left,
              "right": right,
              "judgedTwice": judged_twice,
              "verifyStatus": verify_status}
    return json.dumps(output)    

@app.route('/pwva/complete_comparison/<round_id>/<comparison_id>/<outcome>')
def complete_comparison(round_id, comparison_id, outcome):
    """ Complete the incomplete comparison for the current user in the given round.
    An error will be logged if there are zero, or more than one incomplete comparison for the current user
    in the given round."""
    return "Round id {}, comparison id {}, outcome {}".format(round_id, comparison_id, outcome)
    


@app.route('/pwva')
def home():
    user = UserAccount.get_current(admin_required=True)
    return 'Welcome'
    # Serve admin home page that lists comparisons, rounds, judges, video lists, with links to the other pages

@app.route('/pwva/judge/<judge_id>')
def judge(judge_id):
    """PWV admin judge page"""
    logging.info('opened judge page')
    return "hi"

@app.route('/pwva/round/<round_id>')
def round_page(round_id):
    """ PWV admin round page """
    logging.info("opened round page for round {}".format(round_id))
    return "hi round"

@app.errorhandler(NoPermissionError)
def no_permission_page(e):
    logging.error("No permission error")
    #TODO: get user from the caller instead of looking it up again
    user = users.get_current_user()
    nickname = user.nickname()
    logout = users.create_logout_url(request.path)
    return """You are signed in to Google accounts as {}. However you do not 
            have permission to access this page. <br />Click <a href="{}">here</a> to 
            sign out and then sign in as a different user.""".format(nickname, logout)
    
@app.errorhandler(NotLoggedInError)
def not_logged_in_page(e):
    logging.error("Not logged in error")
    login_url = users.create_login_url(request.path)
    message = """This is the Pairwise Comparisons Pilot Application. You need to sign in with 
            a recognised Google account to access the site. <br /><a href="{}">Click here to be
            redirected to the Google sign-in page.</a> """.format(login_url)
    return message, 403
