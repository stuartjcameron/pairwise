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

class Comparison(ndb.Model):
    comparison_number = ndb.IntegerProperty()
    judge = ndb.IntegerProperty()
    left = ndb.IntegerProperty()
    right = ndb.IntegerProperty()
    shown_time = ndb.DateTimeProperty()
    choice_time = ndb.DateTimeProperty()
    #round_number = ndb.IntegerProperty()
    result = ndb.IntegerProperty()          # 1 for left, 2 for right


#TODO: Need to work with judged_once, judged_twice within current round, not within settings
class Settings(ndb.Model):
    round_number = ndb.IntegerProperty()
    #judged_once = ndb.TextProperty()
    #judged_twice = ndb.TextProperty()

class Round(ndb.Model):
    # round_number = ndb.IntegerProperty() -- move to id
    judged_once = ndb.TextProperty()
    judged_twice = ndb.TextProperty()
    
app = Flask(__name__)

userdb_old = {
    'stuartjcameron@gmail.com': {'name': 'Stuart', 'number': 1, 'admin': False},
    'stuart.cameron.opml@gmail.com': {'name': 'Stuart_OPM', 'number': 2, 'admin': True},
    'reg.allen.cacsa@gmail.com': {'name': 'Reg Allen', 'number': 3, 'admin': True},
    'petersamh1@gmail.com': {'name': 'Peter-Sam Hill', 'number': 4, 'admin': True},
    'kofidua@gmail.com': {'name': 'Richard Dua-Ansah', 'number': 5, 'admin': False},
    'naafoley27@gmail.com': {'name': 'Jackline Quaye', 'number': 6, 'admin': False},
    'takasmah@gmail.com': {'name': 'Anthony Asmah', 'number': 7, 'admin': False},
    'jomaxikon@gmail.com': {'name': 'Joyce Ackon', 'number': 8, 'admin': False},
    'essihaffar@gmail.com': {'name': 'Essi Haffar', 'number': 9, 'admin': False},
    'cc3ghanajudge1@gmail.com': {'name': 'Backup 1', 'number': 10, 'admin': False},
    'cc3ghanajudge2@gmail.com': {'name': 'Backup 2', 'number': 11, 'admin': False}
}

userdb = {'cc3bljudge1@gmail.com': {'name': 'Judge 1', 'number': 1, 'admin': False}, 
          'cc3bljudge2@gmail.com': {'name': 'Judge 2', 'number': 2, 'admin': False}, 
          'cc3bljudge3@gmail.com': {'name': 'Judge 3', 'number': 3, 'admin': False}, 
          'cc3bljudge4@gmail.com': {'name': 'Judge 4', 'number': 4, 'admin': False}, 
          'cc3bljudge5@gmail.com': {'name': 'Judge 5', 'number': 5, 'admin': False}, 
          'cc3bljudge6@gmail.com': {'name': 'Judge 6', 'number': 6, 'admin': False}, 
          'cc3bljudge7@gmail.com': {'name': 'Judge 7', 'number': 7, 'admin': False}, 
          'cc3bljudge8@gmail.com': {'name': 'Judge 8', 'number': 8, 'admin': False}, 
          'cc3bljudge9@gmail.com': {'name': 'Judge 9', 'number': 9, 'admin': False}, 
          'cc3bljudge10@gmail.com': {'name': 'Judge 10', 'number': 10, 'admin': False}, 
          'cc3bljudge11@gmail.com': {'name': 'Judge 11', 'number': 11, 'admin': False}, 
          'cc3bljudge12@gmail.com': {'name': 'Judge 12', 'number': 12, 'admin': False}, 
          'cc3ghanajudge1@gmail.com': {'name': 'Judge 13', 'number': 14, 'admin': True}, 
          'cc3ghanajudge2@gmail.com': {'name': 'Judge 14', 'number': 20, 'admin': True},
          'cc3evaluation@gmail.com': {'name': 'Judge 15', 'number': 15, 'admin': False}, 
          'cc3bljudge13@gmail.com': {'name': 'Judge 13(b)', 'number': 13, 'admin': False},
          'stuartjcameron@gmail.com': {'name': 'Stuart', 'number': 16, 'admin': False}, 
          'stuart.cameron.opml@gmail.com': {'name': 'Stuart-OPML', 'number': 17, 'admin': True}, 
          'reg.allen.cacsa@gmail.com': {'name': 'Reg Allen', 'number': 18, 'admin': True}, 
          'petersamh1@gmail.com': {'name': 'Peter-Sam Hill', 'number': 19, 'admin': True},
          'rhodor@pdaghana.com': {'name': 'Judge 16', 'number': 21, 'admin': False}
}

def check_user(admin_required=False):
    """ Check if user is logged in and has permission to use the app.
    Returns a tuple with 1. dictionary of user info, if logged in; 
        2. whether okay to proceed (user is logged in and has permission)
        3. message if not okay
    """
    
    user = users.get_current_user()
    if user:
        email = user.email().lower()
        user_dict = {'nickname': user.nickname(), 
                    'email': user.email(),
                    'logout': users.create_logout_url(request.path),
                    'logoutOutput': users.create_logout_url('/pairwise/output')}
        registered = email in userdb
        admin = registered and userdb[email]['admin']
        if registered and (admin or not admin_required):
            user_dict.update(userdb[email])
            return user_dict, True, None
        else:
            r = """You are signed in to Google accounts as {}. However you do not have permission to access this page. 
            <br />Click <a href="{}">here</a> to sign out and then sign in as a different user."""  
            message = r.format(user.nickname(), users.create_logout_url(request.path))
            return user_dict, False, message
    else:
        r = """This is the Pairwise Comparisons Pilot Application. You need to sign in with 
            a recognised Google account to access the site. <br /><a href="{}">Click here to be
            redirected to the Google sign-in page.</a> """
        login_url = users.create_login_url(request.path)
        return None, False, r.format(login_url)

def count_comparisons(left, right, round_number):
    """ Count comparisons matching the given left right and round_number, and also comparisons where left and right are reversed
        We limit the count to 2 as we don't care if there are more than 2  """
    ancestor_key = ndb.Key("Round", round_number)
    matches = Comparison.query(Comparison.left == left, Comparison.right == right, ancestor=ancestor_key).count(limit=2)
    matches += Comparison.query(Comparison.left == right, Comparison.right == left, ancestor=ancestor_key).count(limit=2)
    return matches


@app.route('/pairwise/query')
def pairwise_query():
    """ Misc queries to DB for admins """
    def draft_output(comparison):
        return 'Judge {}, number {}, left {}, right {}, round {}<br />'.format(comparison.judge, 
                                                                           comparison.comparison_number,
                                                                           comparison.left,
                                                                           comparison.right,
                                                                           comparison.key.parent().id()) 
    
    user, okay, message = check_user(admin_required=True)
    if not okay:
        return message
    if request.args['command'] == 'count':
        if 'round' in request.args:
            round_number = int(request.args['round'])
        else:
            round_number = get_round()
        left = int(request.args['left'])
        right = int(request.args['right'])
        matches = count_comparisons(left, right, round_number)
        return "There are {} existing comparisons of {} with {}, in round {}".format(matches, left, right, round_number)
    elif request.args['command'] == 'list':
        if 'round' in request.args:
            round_number = int(request.args['round'])
        else:
            round_number = get_round()
        left = int(request.args['left'])
        right = int(request.args['right'])
        q1 = Comparison.query(Comparison.left == left, Comparison.right == right) #, Comparison.round_number == round_number)
        q2 = Comparison.query(Comparison.left == right, Comparison.right == left) #, Comparison.round_number == round_number)
        r = 'Comparisons of {} with {} in round {}: <br />'.format(left, right, round_number)
        r += ''.join(q1.map(draft_output)) + ''.join(q2.map(draft_output))  
        return r

def alter_setting(k, v):
    settings = Settings().query().fetch(1)
    if not settings:
        settings = Settings()
    else:
        settings = settings[0]
    setattr(settings, k, v)
    settings.put() 

def get_setting(k):
    settings = Settings().query().fetch(1)
    if not settings:
        return None
    else:
        return getattr(settings[0], k)


def update_judged_record(round_number, left, right):
    round_info = Round().get_by_id(str(round_number))
    pair = [min(left, right), max(left, right)]
    if not round_info:
        round_info = Round(id=str(round_number))
    if round_info.judged_once:
        once = json.loads(round_info.judged_once)
    else:
        once = []
    if round_info.judged_twice:
        twice = json.loads(round_info.judged_twice)
    else:
        twice = []
    if pair in once:
        if pair not in twice:
            twice += pair
            round_info.judged_twice = json.dumps(twice)
            round_info.put()
    else:
        once += pair
        round_info.judged_once = json.dumps(once)
        round_info.put()
    return twice

def get_judged_record(round_number):
    round_info = Round().get_by_id(str(round_number))
    if round_info and round_info.judged_twice:
        return json.loads(round_info.judged_twice)
    return []

def update_judged_record_old(left, right):
    """ Updates record of which pairs have been judged once or twice
    and returns JSON string containing list of all pairs judged twice """
    settings = Settings().query().fetch(1)
    # TODO: change this to get the info from current round:
    # round = Round().query(Round.round_number == get_round()).fetch(1), etc.
    pair = [min(left, right), max(left, right)]
    if settings:
        settings = settings[0]
    else:
        settings = Settings()
    if settings.judged_once:
        once = json.loads(settings.judged_once)
    else:
        once = []
    if settings.judged_twice:
        twice = json.loads(settings.judged_twice)
    else:
        twice = []
    if pair in once:
        if pair not in twice:
            twice += pair
            settings.judged_twice = json.dumps(twice)
            settings.put()
    else:
        once += pair
        settings.judged_once = json.dumps(once)
        settings.put()
    return twice



@app.route('/pairwise/set')
def pairwise_set():
    """ Set application settings such as current round """
    user, okay, message = check_user(admin_required=True)
    if not okay:
        return message
    if 'round' in request.args:
        round_number = int(request.args['round'])
        
        # Create a blank record for the round if it doesn't exist
        if not ndb.Key("Round", round_number).get():
            Round(id=round_number).put()
            
        alter_setting('round_number', round_number)
        return 'Round set to {}.'.format(round_number)

def get_round():
    r = get_setting('round_number')
    if type(r) == int:
        return r
    else:
        return 0

@app.route('/pairwise')
def pairwise_home():
    user, okay, message = check_user()
    if not okay:
        return message
   
    return render_template('index.html', user=user, compressed="false", round=get_round(), weights=get_updated_weights())

@app.route('/pairwise/compressed')
def pairwise_compressed():
    user, okay, message = check_user()
    if not okay:
        return message
   
    return render_template('index.html', user=user, compressed="true", round=get_round(), weights=get_updated_weights())

@app.route('/pairwise/showweights/<r>')
def show_weights(r):
    return get_updated_weights(r)

@app.route('/pairwise/showtwice/<r>')
def show_twice(r):
    twice = get_judged_record(r)
    return "Twice: {}".format(twice)

def get_updated_weights(r=None):
    """ Get weights from text file. Then update them by removing any for pairs that have already been judged twice.
    Returns the weights in a Json string """
    def not_judged_twice(weight):
        return [weight[0], weight[1]] not in twice
    if r is None:
        r = get_round()
    twice = get_judged_record(r)
    #twice = get_judged_record()
    if not twice:
        return get_weights_json()
    weights = json.loads(get_weights_json())
    twice = json.loads(twice)
    return json.dumps(filter(not_judged_twice, weights))

def json_to_datetime(json_date_string):
    return datetime.datetime.strptime(json_date_string, '%Y-%m-%dT%H:%M:%S.%fZ')

def get_weights_json():
    a = []
    with open('inputs/weights.csv', 'r') as f:
        for line in f:
            a.append('[{}]'.format(line.strip()))
    return '[{}]'.format(', '.join(a)) 
    
@app.route('/pairwise/add_comparison')
def add_comparison():
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

@app.route('/pairwise/output')
def output():
    """ Output the results from the comparisons so far """
    user, okay, message = check_user()  # check_user(admin_required=True)
    if not okay:
        return message
    if user['admin']:
        ancestor_key = ndb.Key("Round", get_round())
        comparisons = Comparison.query(ancestor=ancestor_key).order(-Comparison.choice_time)
        #comparisons = Comparison.query()
        #TODO - get the round
        return render_template('output.html', user=user, round=get_round(), comparisons=comparisons.iter())
    else:
        return render_template('output.html', user=user, round=get_round())
    
@app.route('/papers/<number>')
def access_pdf(number):
    _, okay, message = check_user()
    if not okay:
        return message
    # Note, the pdfs are currently saved as 8 digit numbers with 0 padding
    return send_file('inputs/{:0>8}.pdf'.format(number))

@app.route('/cpapers/<number>')
def access_pdf_compressed(number):
    _, okay, message = check_user()
    if not okay:
        return message
    # Note, the pdfs are currently saved as 8 digit numbers with 0 padding
    return send_file('inputs/compressed/{:0>8}.pdf'.format(number))

#@app.errorhandler(400)
#def bad_request(e):
#    logging.exception('Bad request.')
#    return 'Bad request', 400
      
@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
# [END app]