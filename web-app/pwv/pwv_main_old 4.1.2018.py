""" Pairwise video comparisons
Administrator app
"""
from __builtin__ import classmethod

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
#from google.auth import app_engine
from flask import Flask, render_template, request, send_file, jsonify, redirect
from google.appengine.ext import ndb
import datetime
from google.appengine.ext.appstats.formatting import message
import json
from jinja2.nodes import Pair
from functools import wraps
#from random import sample
from os import urandom
from hashlib import sha256
import operator as op
from random import randrange, random
from collections import Counter
#dummy call to deal with python bug
datetime.datetime.strptime('2012-01-01', '%Y-%m-%d')

app = Flask(__name__)

class BadPostError(Exception):
    pass


class NoSessionError(Exception):
    pass


class NotLoggedInError(Exception):
    pass


class NoPermissionError(Exception):
    pass

class SessionStartError(Exception):
    pass

def hash_password(password):
    return sha256(password).hexdigest()

# Round will be parent of comparisons
#TODO: Implement these in a separate namespace from the earlier pairwise app
# see https://cloud.google.com/appengine/docs/standard/python/multitenancy/
class PwvRound(ndb.Model):
    judges = ndb.IntegerProperty(repeated=True) # stores a list of account_id
    name = ndb.StringProperty()
    created = ndb.DateTimeProperty()
    modified = ndb.DateTimeProperty()
    creator = ndb.IntegerProperty() # refers to account_id
    opened = ndb.BooleanProperty()
    file_list = ndb.IntegerProperty() # refers to file_list.id
    files_viewed = ndb.IntegerProperty(repeated=True)  # file_list indexes viewed
    pairs_viewed = ndb.IntegerProperty(repeated=True) # pair indexes viewed
    max_views = ndb.IntegerProperty()
    max_comparisons = ndb.IntegerProperty()
    max_views_by_user = ndb.IntegerProperty()
    max_comparisons_by_user = ndb.IntegerProperty()
    
    def get_creator(self):
        return UserAccount.get_by_id(self.creator)
    
    @classmethod
    def all(cls, page=1):
        #TODO: add page if ever needed
        return cls.query().order(-cls.created)
    
    @classmethod
    def by_judge_id(cls, judge_id, page=1):
        return cls.query().filter(cls.judges == judge_id).order(-cls.created)
    
    @classmethod
    def list_by_judge_id(cls, judge_id):
        """ Provide a list of round IDs and names for this judge """
        return [(r.key.id(), r.name) for r in cls.by_judge_id(judge_id)]
    
    def to_dict_with_id(self):
        d = self.to_dict()
        d['id'] = self.key.id()
        return d
        
    def get_file_list(self):
        if self.file_list:
            return FileList.get_by_id(self.file_list)
    
    def get_valid_file_list(self, user=None):
        """ Get the list of files that conform to the round's rules regarding
        maximum views of individual files for the given user. """
        if user is None:
            user = UserAccount.current
        file_list = self.get_file_list().content
        for file in file_list:
            pass
        
        
            
    def get_file_list_text(self):
        if self.file_list:
            return FileList.get_by_id(self.file_list).content_preview()
        else:
            return None

    @classmethod
    def all_dicts(cls):
        """ Return all entities as a list of dicts including their IDs """
        return [r.to_dict_with_id() for r in cls.all()]
            

class PwvComparison(ndb.Model):
    #comparison_number = ndb.IntegerProperty()
    judge = ndb.IntegerProperty() # this will store the account_id not the user_id
    pair = ndb.IntegerProperty() # the pair number based on lexic. ordering of file_list indices
    left = ndb.StringProperty() # the left file name
    right = ndb.StringProperty() # the right file name
    created = ndb.DateTimeProperty()  # date when the comparison was first generated
    completed = ndb.DateTimeProperty() # date when the server received the judge's choice
    #round_number = ndb.IntegerProperty()
    result = ndb.IntegerProperty()          # 1 for left, 2 for right, None for not completed
    test = ndb.BooleanProperty()            # ignore test cases when doing the real comparisons
    
    @classmethod
    def all(cls, page=1):
        return cls.query().order(-cls.created)
        # TODO: add start and stop based on page
        
    @classmethod
    def by_judge_id(cls, judge_id, page=1):
        #TODO: ignoring pages
        return cls.query().filter(cls.judge == judge_id).order(-cls.created)
    
    @classmethod
    def completed_by_judge_id(cls, judge_id):
        return cls.query().filter(cls.judge == judge_id, cls.completed != None)
    
    @classmethod
    def delete_by_judge_id(cls, judge_id):
        ndb.delete_multi(cls.query(cls.judge == judge_id).fetch(keys_only=True))
    
    @classmethod
    def count_by_judge_id(cls, judge_id):
        #TODO: filter by judge
        return cls.query().filter(cls.judge == judge_id).count()
        
    @classmethod
    def by_round_id(cls, round_id, page=1):
        ancestor_key = ndb.Key("PwvRound", round_id)
        logging.info('getting by round id')
        logging.info(round_id)
        logging.info(type(round_id))
        logging.info(ancestor_key.id())
        return cls.query(ancestor=ancestor_key).order(-cls.created).fetch()
    
    @classmethod
    def delete_by_round_id(cls, round_id):
        ancestor_key = ndb.Key("PwvRound", round_id)
        ndb.delete_multi(cls.query(ancestor=ancestor_key).fetch(keys_only=True))
        
    @classmethod
    def count_by_round(cls, round_id):
        ancestor_key = ndb.Key("PwvRound", round_id)
        return cls.query(ancestor=ancestor_key).count()
    
    def get_judge_name(self):
        account = UserAccount.get_by_id(self.judge)
        if account:
            return account.name or account.nickname
    
    def get_round_name(self):
        round_id = self.key.parent().id()
        round_ = PwvRound.get_by_id(round_id)
        # round_ = self.key.parent().get()  # -- not sure why this returns None
        logging.info(self.key.parent().id())
        logging.info(round_)
        logging.info(PwvRound.get_by_id(self.key.parent().id()))
        if round_:
            return round_.name


class UserAccount(ndb.Model):
    user_id = ndb.StringProperty()  # to store the user id https://cloud.google.com/appengine/docs/standard/python/users/userobjects
    admin = ndb.BooleanProperty()
    name = ndb.StringProperty()
    rounds = ndb.IntegerProperty(repeated=True)
    new_user = ndb.BooleanProperty()
    nickname = ndb.StringProperty()
    email = ndb.StringProperty()
    token = ndb.StringProperty()
    token_created = ndb.DateTimeProperty()
        
    @classmethod
    def all(cls, page=1):
        return cls.query().order(-cls.name)
    
    def count_comparisons(self):
        return PwvComparison.count_by_judge_id(self.key.id())
    
    def in_round(self, round_):
        return self.key.id() in round_.judges  #TODO: check if this works as intended
    
    @classmethod
    def create_session(cls):
        user = users.get_current_user()
        return cls.get_by_user(user)
              
    @classmethod
    def check(cls, admin_required=False): #, check_session=False):
        """ Check the current user (i) is signed in to Google, (ii) has an account for this app, 
        and (iii) is an admin if required.
        Raise errors if not which will lead to a 401 page. 
        If the user is okay stores the info in UserAccount.current
        """
        user = users.get_current_user()
        if not user:
            raise NotLoggedInError
            #if check_session and "token" in request.json:
            #    cls.check_session()
            #else:
            #    raise NotLoggedInError
        else:
            account = cls.get_by_user(user)
            if not account:
                raise NoPermissionError
            if admin_required and not account.admin:
                raise NoPermissionError
            cls.current = account
            login = users.create_login_url(request.path)
            cls.current.change_user = users.create_logout_url(login)
                #return account
    
    @classmethod
    def check_session(cls, admin_required=False):
        """ For the desktop app, we use basic auth with username and a server-generated
        token. This tests whether the user has such authentication. """
        #token = request.json["token"]
        auth = request.authorization
        if not auth or auth.username is None or auth.password is None:
            raise NoSessionError
        logging.info("""UserAccount.check_session: username=%s, password=%s""",
                     auth.username, auth.password)
        
        # To ensure consistency - keys only query on the email then get the record
        # using the key
        account_key = cls.query().filter(cls.email == auth.username).get(keys_only=True)
        account = account_key.get()
        #TODO: use session ID instead of username; then check both email and 
        # password match
        if not account:
            raise NoSessionError
        hashed_password = hash_password(auth.password)
        logging.info("""UserAccount.check_session: account exists
        account.token=%s
        hashed password=%s""", account.token, hashed_password)
        if account.token != hashed_password:
            #TODO: also check if session key was set more than ? 1 day ago
            raise NoSessionError
        if admin_required and not account.admin:
            raise NoPermissionError
        cls.current = account
        #TODO: keep password valid for longer if used successfully?
        # or, create new session key every day or so for greater security?
            
    @classmethod
    def get_by_user(cls, user):
        """ Get account info for the specified user. Returns an object that 
        merges the info from User with the info in the UserAccount DB. """
        # first check by user_id
        r = cls.query().filter(cls.user_id == user.user_id()).get() 
        if r:
            r.new_user = False
        else:
            # the user may be new so we check by email too
            # but reject the user if there is already a different user id
            # linked to this email address
            # TODO: flag if the user is new - may want to redirect to a different starting
            # screen
            r = cls.get_by_email(user.email())
            if not r or r.user_id is not None:
                return None
            r.user_id = user.user_id()
            r.new_user = True
        r.nickname = user.nickname()
        r.email = user.email()
        r.put() # updates entry with latest nickname and email address, in case these ever change
        return r
    
    @classmethod
    def get_by_token(cls, token):
        #TODO: look up by series ID instead
        hashed = hash_password(token)
        return cls.query().filter(cls.token == hashed).get()
    
    @classmethod
    def get_by_email(cls, email):
        return cls.query().filter(cls.email == email).get()
    
    #TODO: DRY - this repeats code in PwvRound
    def to_dict_with_id(self):
        d = self.to_dict()
        d['id'] = self.key.id()
        return d
        
    @classmethod
    def all_dicts(cls):
        """ Return all entities as a list of dicts including their IDs """
        return [r.to_dict_with_id() for r in cls.all()]



class FileList(ndb.Model):
    account_id = ndb.IntegerProperty()
    name = ndb.StringProperty()
    creator = ndb.IntegerProperty() # refers to account_id
    old_creator_name = ndb.StringProperty() # for when account no longer exists
    created = ndb.DateTimeProperty()
    content = ndb.StringProperty(repeated=True)
    number_of_pairs = ndb.IntegerProperty()
    
    @classmethod
    def all(cls):
        return cls.query().order(cls.name)
    
    def get_creator_name(self):
        if self.creator:
            account = UserAccount.get_by_id(self.creator)
            if account:
                return account.name
        if self.old_creator_name:
            return self.old_creator_name
        else:
            return "Unknown"
    
    def content_preview(self, max_length=20):
        r = '; '.join(self.content[:max_length])
        if len(r) > max_length:
            return r[:max_length] + "..."
        else:
            return r
        
    def get_number_of_pairs(self):
        """ Return the number of pairs (cache it if it is not already cached) """
        # Note: currently file lists cannot be edited.
        # If they can be edited then need to update self.number_of_pairs each time
        if self.number_of_pairs is None:
            self.number_of_pairs = nc2(len(self.content))
        return self.number_of_pairs
    
    def get_kth_pair(self, k):
        left, right = kth_pair(k, self.get_number_of_pairs())
        return self.content[left], self.content[right]
    

def route(rule, admin=False, session=False, **options):
    """ Wrapper which routes with login required. """
        
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            UserAccount.check(admin_required=admin)
            return f(*args, **kwargs)
        #TODO: may want to allow optional add_url_rule arguments: http://flask.pocoo.org/docs/0.12/api/#url-route-registrations
        app.add_url_rule(rule=rule, view_func=decorated_function, **options)
        return decorated_function
    
    return decorator


def admin(rule, **options):
    """ Wrapper which routes with admin login required.  """
    return route(rule, admin=True, **options)

def session(rule, admin_required=False, **options):
    """ Wrapper which allows either admin online, or session from desktop app """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            UserAccount.check_session(admin_required=admin_required)
            return f(*args, **kwargs)
        #TODO: may want to allow optional add_url_rule arguments: http://flask.pocoo.org/docs/0.12/api/#url-route-registrations
        app.add_url_rule(rule=rule, view_func=decorated_function, **options)
        return decorated_function
    
    return decorator

    
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


#####################################################################
# ADMIN PAGES
#####################################################################


@admin('/pwva')
def home():
    user = UserAccount.current
    comparisons = PwvComparison.all()
    rounds = PwvRound.all()
    users = UserAccount.all()
    file_lists = FileList.all()
       
    logging.info("Welcome, {}".format(user.nickname))
    return render_template('admin_home.html', user=user, rounds=rounds, 
                           comparisons=comparisons, users=users, file_lists=file_lists)
    # Serve admin home page that lists comparisons, rounds, judges, video lists, with links to the other pages

@admin('/pwva/user/<int:account_id>')
def user_page(account_id):
    """PWV admin judge page"""
    user = UserAccount.current
    accounts = UserAccount.all()
    names = [u.name for u in accounts]
    emails = [u.email for u in accounts]
    account = UserAccount.get_by_id(account_id)
    comparisons = PwvComparison.by_judge_id(account_id)
    #rounds = PwvRound.by_judge_id(account_id)
    rounds = PwvRound.all_dicts()
        
    return render_template('admin_user.html', user=user, account=account, 
                           to_client = {"rounds": rounds, "accountId": account_id,
                                        "account": account.to_dict(), "userNames": names,
                                        "userEmails": emails},
                           comparisons=comparisons)

@admin('/pwva/new_user')
def new_user_page():
    """PWV admin make new user page"""
    user = UserAccount.current
    #account = UserAccount()
    users = UserAccount.all()
    user_names = [(u.name or u.nickname) for u in users]
    user_emails = [u.email for u in users]
    rounds = PwvRound.all()
    return render_template('admin_new_user.html', user=user, rounds=rounds,
                           to_client = {'names': user_names, 'emails': user_emails})
    
@admin('/pwva/round/<int:round_id>')
def round_page(round_id):
    """ PWV admin round page """
    user = UserAccount.current
    round_ = PwvRound.get_by_id(round_id)
    round_names = [r.name for r in PwvRound.all()]
    comparisons = PwvComparison.by_round_id(round_id)
    logging.info('comparisons by round')
    #logging.info(comparisons.count())
    users = UserAccount.all()
    file_lists = FileList.all()
    creator = round_.get_creator()
    # n.b. in the template, use user.in_round(round_) to check whether user is in the 
    # selected round or not
    return render_template('admin_round.html', user=user, round_=round_, 
                           creator=creator, comparisons=comparisons, users=users,
                           file_lists=file_lists,
                           to_client = {'roundNames': round_names, 'round': round_.to_dict(),
                                        'roundId': round_id})

@admin('/pwva/new_round')
def new_round_page():
    user = UserAccount.current
    round_names = [r.name for r in PwvRound.all()]
    users = UserAccount.all()
    return render_template('admin_new_round.html', user=user, users=users, 
                           to_client={'roundNames': round_names})
    
@admin('/pwva/test_comp')
def test_comp_page():
    rounds = PwvRound.all()
    return render_template('admin_test_comp.html', user=UserAccount.current,
                            rounds=rounds,
                           to_client={'rounds': PwvRound.all_dicts()})


#####################################################################
# ADMIN FUNCTIONS RETURNING JSON
#####################################################################


@admin('/pwva/add_user', methods=['POST'])
def add_user():
    """ Send an email invitation to the specified address, and add the user as unverified.
        Return True if successful, False if not """
    logging.info("Inviting new user")
    #user = UserAccount.get_current(admin_required=True)
    # new_user = users.User(request.json['email'])
    # The above doesn't seem to do anything useful if the user has not yet signed in
    # so removing it. user_id is then None for accounts that have been created by an admin
    # but where no user has yet signed in.
    new_account = UserAccount(
        name=request.json['name'],
        email=request.json['email'],
        admin=request.json['admin'],
        )
    key = new_account.put()
    return jsonify({'round_id': key.id()})
    

@admin('/pwva/add_round', methods=['POST'])
def add_round():
    logging.info('adding new round')
    judge_ids = [int(account_id) for account_id in request.json['judges']]
    round_ = PwvRound(
        name=request.json['name'],
        opened=request.json['opened'],
        judges=judge_ids,
        creator=UserAccount.current.key.id(),
        created=datetime.datetime.now()
        )
    round_id = round_.put().id()
    for judge_id in judge_ids:
        account = UserAccount.get_by_id(judge_id)
        account.rounds.append(round_id)
        account.put()
    
    return jsonify({'round_id': round_id})

@admin('/pwva/edit_user/<int:account_id>', methods=['POST'])
def edit_user(account_id):
    account = UserAccount.get_by_id(account_id)
    edits = request.json
    if 'name' in edits:
        account.name = edits['name']
    if 'email' in edits:
        user = users.User(edits['email'])
        account.user_id = user.user_id()
        account.email = edits['email']
    if 'rounds' in edits:
        account.rounds = edits['rounds']
        
        # A filter might be better for the below. But expecting the number of rounds
        # and judges to be small.
        for round_ in PwvRound.all():
            should_be_linked = round_.key.id() in edits['rounds']
            linked = account_id in round_.judges
            if should_be_linked and not linked:
                round_.judges.append(account_id)
                round_.put()
            elif linked and not should_be_linked:
                round_.judges.remove(account_id)
                round_.put()
        
    key = account.put()
    return jsonify({'user_id': key.id()})

@admin('/pwva/delete_user/<int:user_id>', methods=['GET'])
def delete_user(account_id):
    account = UserAccount.get_by_id(account_id)
    account.key.delete()
    PwvComparison.delete_by_judge_id(account_id)
    #TODO: for all file lists created by this user, replace creator=None and 
    # defunctCreatorName = the old name
    return jsonify({"deletedAccountId": account_id})
    
@admin('/pwva/edit_round/<int:round_id>', methods=['POST'])
def edit_round(round_id):
    round_ = PwvRound.get_by_id(round_id)
    edits = request.json
    if 'name' in edits:
        round_.name = edits['name']
    if 'judges' in edits:
        round_.judges = edits['judges']
        
        for account in UserAccount.all():
            should_be_linked = account.key.id() in edits['judges']
            linked = round_id in account.rounds
            if should_be_linked and not linked:
                account.rounds.append(round_id)
                account.put()
            elif linked and not should_be_linked:
                account.rounds.remove(round_id)
                account.put()
    
    if 'fileList' in edits:
        round_.file_list = edits['fileList']
        
    key = round_.put()
    return jsonify({'round_id': key.id()})

@admin('/pwva/delete_round/<int:round_id>', methods=['GET'])
def delete_round(round_id):
    round_ = PwvRound.get_by_id(round_id)
    round_.key.delete()
    PwvComparison.delete_by_round_id(round_id)
    return jsonify({'deletedRoundId': round_id})
 


@admin('/pwva/add_fake_file_list/<name>')
def add_fake_file_list(name):
    file_list = FileList(
        account_id=UserAccount.current.key.id(),
        name=name,
        created=datetime.datetime.now(),
        content=["1", "2", "3", "4", "5"])
    key = file_list.put()
    return jsonify({'fileListId': key.id()})


@session('/pwva/add_file_list', admin_required=True, methods=['POST'])
def add_file_list():
    logging.info("add file list")
    file_list = FileList(
        creator=UserAccount.current.key.id(),
        name=request.json['description'],
        created=datetime.datetime.now(),
        content=request.json['file_list']
        )
    key = file_list.put()
    return jsonify({'fileListId': key.id()})


@admin('/pwva/delete_file_list/<int:file_list_id>')
def delete_file_list(file_list_id):
    file_list = FileList.get_by_id(file_list_id)
    file_list.delete()
    round_keys = []
    for r in PwvRound.all():
        if r.file_list_id == file_list_id:
            r.file_list_id = None
            round.keys.append(r.key)
    if round_keys:
        ndb.delete_multi(round_keys)
    return jsonify({'deletedFileListId': file_list_id})
     

# USER FUNCTIONS RETURNING JSON


def add_comparison(round_id, test=False):
    round_key = ndb.Key("PwvRound", round_id)
    round_ = PwvRound.get_by_id(round_id)
    logging.info("round ")
    logging.info(round_key.id())
    logging.info(round_)
    user = UserAccount.current
    left, right = select_files(round_, user)
    comparison = PwvComparison(
        parent=round_key,
        judge=user.key.id(),
        created=datetime.datetime.now(),
        left=left,
        right=right,
        test=test)
    comparison_key = comparison.put()
    return {'comparisonId': comparison_key.id(),
            'left': comparison.left,
            'right': comparison.right}

@session('/pwva/add_comparison')
def add_comparison_wrap():
    round_id = request.args.get('round', type=int)
    test = request.args.get('test', default=False, type=bool)
    result = add_comparison(round_id, test)
    return jsonify(result)
    
@session('/pwva/start_judging')
def start_judging():
    """ Wrapper for next_thing which will issue a directive to the client about
    what to do when the user starts judging """
    round_id = request.args.get('round', type=int)
    action, detail = next_thing(round_id)
    return jsonify({'action': action, 'detail': detail})

def next_thing(round_id):
    """ Check for any issues like round clashes. If not then add a comparison
    and send to user.Return a tuple of the next thing to do for the current user
    and detail needed for the next action """
    permitted_rounds = PwvRound.list_by_judge_id(UserAccount.current.key.id())
    okay = any(round_id == i for (i, _) in permitted_rounds)
    if okay:
        new_comp = add_comparison(round_id)
        return 'comparison', new_comp
    else:
        return 'choose round', permitted_rounds    
    
@session('/pwva/get_rounds')
def get_rounds():
    """ Return the list of rounds permitted for the signed in user """
    permitted_rounds = PwvRound.list_by_judge_id(UserAccount.current.key.id())
    return jsonify({'rounds': permitted_rounds})



    
def select_files_old(round_, user):
    """ Select two files for comparison given a round and user 
        1. make list of files that have not exceeded max_views for user or round
        (n.b. count completed comparisons only)
        2. calculate nc2 for total pairs with the remaining files
        3. make list of pair indices that have exceeded max views for user or round
        4. use randrange_excluding to select pair index excluding the list from 3
    """
    file_list = round_.get_file_list_content
    excluded_pairs = set()
    valid_files = set(file_list)
    if round_.max_views_by_user is not None or round_.max_comparisons_by_user is not None:
        user_id = user.key.id()
        user_pairs_viewed = Counter()
        user_files_viewed = Counter()
        user_comparisons = PwvComparison.by_judge_id(user_id)      
        for comparison in user_comparisons:
            user_files_viewed[comparison.left] += 1
            user_files_viewed[comparison.right] += 1
            user_pairs_viewed[comparison.pair] += 1
        if round_.max_views_by_user is not None:
            valid_files -= set(f for f, c in user_files_viewed.items()
                               if c >= round_.max_views_by_user)            
        if round_.max_comparisons_by_user is not None:
            for pair, count in user_pairs_viewed.items():
                if count >= round_.max_comparisons_by_user:
                    excluded_pairs.add(pair)
    valid_file_indices = set(map(file_list.index, valid_files))
    if round_.max_views is not None:
        round_files_viewed = Counter(round_.files_viewed)
        valid_file_indices -= set(f for f, c in round_files_viewed.items()
                                  if c >= round.max_views)
    if round_.max_comparisons is not None:
        excluded_pairs.update(set(round_.pairs_viewed))
    valid_file_indices = list(valid_file_indices)
    number_of_files = len(valid_file_indices) 
    number_of_pairs = nc2(number_of_files)
    pair_index = randrange_excluding(number_of_pairs, list(excluded_pairs))
    # this won't work! the excluded_pairs list needs to be based on pair indices
    # in the new list
    pair = kth_pair(pair_index, number_of_files)
    
def select_files(round_, user):
    """ Select two files for comparison given a round and user 
        1. make list of pairs to be excluded because already viewed too many times by
        (i) this user or (ii) any user, according to the rules specified for the round
        2. make list of files to be excluded because already viewed too many times
        3. randomly select from all pairs excluding the excluded pairs
        4. if L, R are in the excluded_files list then add this pair to the excluded_pairs
        list and redo the selection. Repeat until a pair can be found that is not excluded.
        
    """
    file_list = round_.get_file_list_content
    excluded_pairs = set()
    excluded_files = set()
    if round_.max_views_by_user is not None or round_.max_comparisons_by_user is not None:
        user_id = user.key.id()
        user_pairs_viewed = Counter()
        user_files_viewed = Counter()
        user_comparisons = PwvComparison.completed_by_judge_id(user_id)      
        for comparison in user_comparisons:
            user_files_viewed[comparison.left] += 1
            user_files_viewed[comparison.right] += 1
            user_pairs_viewed[comparison.pair] += 1
        if round_.max_views_by_user is not None:
            excluded_files = set(f for f, c in user_files_viewed.items()
                               if c >= round_.max_views_by_user)            
        if round_.max_comparisons_by_user is not None:
            for pair, count in user_pairs_viewed.items():
                if count >= round_.max_comparisons_by_user:
                    excluded_pairs.add(pair)
    excluded_file_indices = set(map(file_list.index, excluded_files))
    if round_.max_views is not None:
        round_files_viewed = Counter(round_.files_viewed)
        excluded_file_indices |= set(f for f, c in round_files_viewed.items()
                                  if c >= round.max_views)
    if round_.max_comparisons is not None:
        excluded_pairs |= set(round_.pairs_viewed)
    #excluded_file_indices = list(excluded_file_indices)
    #number_of_files = len(valid_file_indices) 
    #number_of_pairs = nc2(number_of_files)
    excluded_pairs = list(excluded_pairs)
    while True:
        number_of_files = len(file_list)
        pair_index = randrange_excluding(number_of_files, excluded_pairs)
        #TODO: handle error in case there are no non-excluded pairs left
        # - end the application as all pairs have been viewed.
        a, b = kth_pair(pair_index, number_of_files)
        if a in excluded_file_indices or b in excluded_file_indices:
            # if files are on the excluded file list, add the pair to the excluded pairs
            # list and try again
            excluded_pairs.append(pair_index)
        else:
            # Randomly choose which file will appear on left and right
            if random() < .5:
                return pair_index, file_list[a], file_list[b]
            else:
                return pair_index, file_list[b], file_list[a] 
            
    
@admin('/pwva/comparison')
def get_comparison():
    comparison_id = int(request.args['comparison'])
    round_id = int(request.args['round'])
    key = ndb.Key(PwvRound, round_id, PwvComparison, comparison_id)
    comparison = key.get()
    if comparison: 
        return jsonify({'comparison': comparison.to_dict()})
    else:
        return jsonify({'comparison_id': comparison_id, 'round_id': round_id, 
                        'key_id': key.id()})
    # this is also not working

@session('/pwva/complete_comparison', methods=['POST'])
def complete_comparison_wrap():
    """ Complete the incomplete comparison for the current user in the given round.
    An error will be logged if there are zero, or more than one incomplete comparison for the current user
    in the given round.
    If the comparison is completed successfully then also get the next thing for the user
    to do and return that to the client software."""
    d = request.get_json()
    comparison_id = d['comparison']
    round_id = d['round']
    if d['choice'] == "left":
        choice = 1
    elif d['choice'] == "right":
        choice = 2
    else:
        choice = None
    completed_id = complete_comparison(comparison_id, round_id, choice)
    action, detail = next_thing(round_id)
    # we return the completed comparison ID for debugging but are unlikely to do
    # anything with this information
    return jsonify({'action': action, 'detail': detail, 
                    'completed_comparison_id': completed_id})


def mark_in_round(round_, comparison):
    """ Mark as viewed in the round a pair and files from a comparison """
    file_list = round_.get_file_list().content
    left_index = file_list.index(comparison.left)
    right_index = file_list.index(comparison.right)
    round_.files_viewed += [left_index, right_index]
    round_.pairs_viewed.append(comparison.pair)
    round_.put()


def complete_comparison(comparison_id, round_id, choice):
    """ Complete the incomplete comparison for the current user in the given round.
    An error will be logged if there are zero, or more than one incomplete comparison for the current user
    in the given round."""
    round_key = ndb.Key("PwvRound", round_id)
    round_ = round_key.get()
    #comparison_key = ndb.Key("PwvRound", round_id, "PwvComparison", comparison_id)
    comparison = PwvComparison.get_by_id(id=comparison_id, parent=round_key)
    
    user_id = UserAccount.current.key.id()
    if user_id == comparison.judge:
        mark_in_round(round_, comparison)
        comparison.result = choice
        comparison.completed = datetime.datetime.now()
        comparison_key = comparison.put()
        return comparison_key.id()
    else:
        # the comparison ID conflicts with the user_id
        # -- something has gone wrong with either the DB or the client software
        raise BadPostError        

@app.route('/pwva/create_session')
def create_session_page():
    logging.info("create_session_page")
    user = users.get_current_user()
    if not user:
        return redirect(users.create_login_url(request.path))
    account = UserAccount.get_by_user(user)
    if not account:
        logging.info("create_session_page: creating new account")
        account = UserAccount()
        account.nickname = user.nickname()
        login = users.create_login_url(request.full_path)
        account.change_user = users.create_logout_url(login)
        return render_template("signin_for_session.html", user=account)
    account.token = hash_password(request.args["token"])
    logging.info("""create_session_page:
        -- token in args: %s
        -- user account email: %s
        -- hashed token stored in account:%s""", 
        request.args["token"],
        account.email,
        account.token)
    account.token_created = datetime.datetime.now()
    account.put()
    return render_template("session_okay.html", user=account)


@app.route('/pwva/start_session')
def start_session():
    """ The desktop application provides a key which was just used (<1 mins ago) by a user who 
    signed in. We provide the username and a new token which then enables the user to post 
    further data. """
    logging.info("start_session")
    auth = request.authorization
    if not auth:
        raise SessionStartError("No authorization information")
    if not auth.username == "desktop-app":
        raise SessionStartError("Username is not desktop-app")
    account = UserAccount.get_by_token(auth.password)
    if not account:
        #my_info = UserAccount.get_by_email('stuartjcameron@gmail.com')
        raise SessionStartError("No account found")
        #return jsonify({"problem": "no account found", "auth.username": auth.username,
        #                "auth.password": auth.password, 
        #                "stuartjcameron@gmail.com token": my_info.token})
    #TODO: also check account.token_created < 1 min ago
    #TODO: change retrieval method so series ID and hashed token are stored in a new
    # DB and checked against user email on each request
    series_id = urandom(24).encode('hex')
    unhashed_token = urandom(24).encode('hex')
    account.token = hash_password(unhashed_token)
    account.token_created = datetime.datetime.now()
    account.put()
    logging.info("""start_session:
    --unhashed new token=%s,
    --account token (hashed)=%s
    --account.email=%s""",
                 unhashed_token, account.token, account.email)
    #logging.info(unhashed_token)
    #logging.info(account.token)
    return jsonify({"session-start": True,
                    "series_id": series_id,
                    "email": account.email, 
                    "token": unhashed_token})
    
    
# ERROR HANDLERS

@app.errorhandler(SessionStartError)
def session_start_error(e):
    logging.error("Session start error: %s", e)
    #logging.error(e)
    return "There was a problem authenticating the user to start a new session", 403

@app.errorhandler(NoSessionError)
def no_session_error(e):
    logging.error("No session error")
    return "There is no open session with these credentials", 403

@app.errorhandler(BadPostError)
def bad_post_error(e):
    logging.error('Bad post error')
    message = """There was an error in the comparison you attempted to complete and 
        the server could not carry out the request."""
    return message, 500   
    
    
@app.errorhandler(NoPermissionError)
def no_permission_page(e):
    logging.error("No permission error")
    #TODO: get user from the caller instead of looking it up again
    account = UserAccount()
    user = users.get_current_user()
    account.nickname = user.nickname()
        
    # Make a path to logout then login then return to the current page
    login = users.create_login_url(request.path)
    account.change_user = users.create_logout_url(login)
    #message = """You are signed in to Google accounts as {}. However you do not 
    #        have permission to access this page. <br />Click <a href="{}">here</a> to 
    #        sign out and then sign in as a different user.""".format(nickname, logout)
    
    return render_template("no_permission.html", user=account), 403
    
@app.errorhandler(NotLoggedInError)
def not_logged_in_page(e):
    logging.error("Not logged in error")
    
    # Make a path to login then return to current page
    login_url = users.create_login_url(request.path)
    message = """This is the Pairwise Comparisons Pilot Application. You need to sign in with 
            a recognised Google account to access the site. <br /><a href="{}">Click here to be
            redirected to the Google sign-in page.</a> """.format(login_url)
    return message, 403



#         UTILITY FUNCTIONS
def nc2(n):
    return reduce(op.mul, xrange(n, n-2, -1)) // 2    

def kth_pair_files(k, file_list):
    left, right = kth_pair(len(file_list))
    return file_list[left], file_list[right]
    
def kth_pair(k, n):
    """ Return the kth combination of 2 entries from the range 0 <= i < n
        Returns none if k is not in the range 0 <= k < n """
    for i in xrange(n):
        n -= 1
        if k < n:
            return i, k + i + 1
        k -= n
        
def randrange_excluding(stop, excl_list):
    """ Return a random integer n such that 0 <= n < b
        but n is not in excl_list. The excl_list will be sorted in-place """
    excl_list.sort()
    if excl_list[-1] >= stop:
        raise ValueError("Values in excl_list are outside of the range")
    r = randrange(stop - len(excl_list))
    for x in excl_list:
        if r < x:
            return r
        else:
            r += 1
    return r