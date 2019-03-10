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
from flask import (Flask, render_template, request, send_file, jsonify, redirect,
                   make_response, abort)
from google.appengine.ext import ndb
import datetime
#from google.appengine.ext.appstats.formatting import message
#import json
#from jinja2.nodes import Pair
from functools import wraps
#from random import sample
from os import urandom
from hashlib import sha256
import operator as op
from random import randrange, random, shuffle
from random import choice as random_choice
from collections import Counter
import StringIO
import csv

ITEMS_PER_PAGE = 10
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
    min_time = ndb.IntegerProperty() # min time between showing and submitting, in sec
    warn_time = ndb.IntegerProperty() # show a warning after this many sec
    #filetype = ndb.StringProperty()  # usually 'video', 'document' or generic 'file'

    def get_creator(self):
        return UserAccount.get_by_id(self.creator)

    @classmethod
    def all(cls, page=1):
        #TODO: add page if ever needed
        return cls.query().order(-cls.created)

    @classmethod
    def list_by_judge_id(cls, judge_id):
        """ Return a list of permitted round IDs and names for this judge
            Rounds are permitted if opened == True and there is a file_list.
            We return the list as (id, name) tuples """
        query = cls.query(cls.judges == judge_id,
                            cls.file_list != None,
                            cls.opened == True)
        return [(r.key.id(), r.name) for r in query]


    def to_dict_with_id(self):
        d = self.to_dict()
        d['id'] = self.key.id()
        return d

    def get_file_list(self):
        if self.file_list:
            return FileList.get_by_id(self.file_list)

    def get_filetype(self):
        file_list = self.get_file_list()
        if file_list:
            return file_list.filetype

    def get_file_list_text(self):
        if self.file_list:
            return FileList.get_by_id(self.file_list).content_preview()
        else:
            return None

    def count_comparisons(self):
        return PwvComparison.query(ancestor=self.key).count()


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
    def all(cls, page=1, items_per_page=ITEMS_PER_PAGE):
        query = cls.query().order(-cls.created)
        offset = (page - 1) * items_per_page
        return query.fetch(items_per_page, offset=offset)

    @classmethod
    def by_judge_id(cls, judge_id, page=1):
        #TODO: ignoring pages
        return cls.query().filter(cls.judge == judge_id).order(-cls.created)

    @classmethod
    def completed_by_judge_id(cls, round_id, judge_id):
        query = cls.query(ancestor=ndb.Key(PwvRound, round_id))
        return query.filter(cls.judge == judge_id, cls.completed != None)

    @classmethod
    def incomplete_by_judge_id(cls, round_id, judge_id):
        query = cls.query(ancestor=ndb.Key(PwvRound, round_id))
        return query.filter(cls.judge == judge_id, cls.completed == None)

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
        return cls.query(ancestor=ancestor_key).order(-cls.created).fetch()

    @classmethod
    def delete_by_round_id(cls, round_id):
        ancestor_key = ndb.Key("PwvRound", round_id)
        ndb.delete_multi(cls.query(ancestor=ancestor_key).fetch(keys_only=True))

    @classmethod
    def count_tests(cls):
        return cls.query(PwvComparison.test == True).count()

    @classmethod
    def delete_tests(cls):
        test_keys = cls.query(PwvComparison.test == True).fetch(keys_only=True)
        ndb.delete_multi(test_keys)

    @classmethod
    def count_by_round(cls, round_id):
        ancestor_key = ndb.Key("PwvRound", round_id)
        return cls.query(ancestor=ancestor_key).count()

    @classmethod
    def today(cls, timezone_offset):
        """ Return comparisons since the beginning of the day """
        t = datetime.datetime.today()
        midnight = datetime.datetime(t.year, t.month, t.day)
        midnight_utc = midnight - datetime.timedelta(hours=timezone_offset)
        return cls.query(cls.completed >= midnight_utc)

    def get_judge_name(self):
        account = UserAccount.get_by_id(self.judge)
        if account:
            return account.name or account.nickname

    def get_round_name(self):
        round_id = self.key.parent().id()
        round_ = PwvRound.get_by_id(round_id)
        # round_ = self.key.parent().get()  # -- not sure why this returns None
        if round_:
            return round_.name

    def get_result_string(self):
        if self.result == 1:
            return "left"
        elif self.result == 2:
            return "right"
        else:
            return "none"

    def formatted_dict(self):

        return {
            'judge': self.get_judge_name(),
            'round': self.get_round_name(),
            'left': self.left,
            'right': self.right,
            'result': self.get_result_string(),
            'created': self.created,
            'completed': self.completed
        }

class Weighting(ndb.Model):
    """ Pair of file lists within a round that will only be compared with each other """
    created = ndb.DateTimeProperty()
    name = ndb.StringProperty()
    left = ndb.StringProperty(repeated=True)
    right = ndb.StringProperty(repeated=True)
    weight = ndb.FloatProperty()
    duplicates = ndb.IntegerProperty()

    def get_list(self, side):
        return '\n'.join(self.left if side == 1 else self.right)

    def get_length(self, side):
        return len(self.left if side == 1 else self.right)

    def count_duplicates(self):
        #lists = [self.left, self.right]
        sets = [set(self.left), set(self.right)]
        #duplicates = [len(L) - len(s) for L, s in zip(lists, sets)]
        #if duplicates == [0, 0]:
        if len(sets[0]) == len(self.left) and len(sets[1]) == len(self.right):
            self.duplicates = len(sets[0] & sets[1])
        else:
            self.duplicates = sum(a == b for a in self.left for b in self.right)



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
            #login = users.create_login_url(request.path)
            #cls.current.change_user = users.create_logout_url(login)
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
        if not account_key:
            raise NoSessionError
        account = account_key.get()
        #TODO: use session ID instead of username; then check both email and
        # password match

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
        #login = users.create_login_url(request.path)
        #cls.current.change_user = users.create_logout_url(login)
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
            if not r:
                logging.warn('UA.get_by_user: no user found with email=%s', user.email())
                return None
            if r.user_id is not None:
                logging.warn('UA.get_by_user: user already has user_id=%s', r.user_id)
                return None
            r.user_id = user.user_id()
            logging.info('UA.get_by_user: user found with email=%s, new user_id=%s',
                         user.email(),
                         user.user_id())
            r.new_user = True
        r.nickname = user.nickname()
        r.email = user.email().lower()
        r.put() # updates entry with latest nickname and email address, in case these ever change
        return r

    @classmethod
    def get_by_token(cls, token):
        #TODO: look up by series ID instead
        hashed = hash_password(token)
        return cls.query().filter(cls.token == hashed).get()

    @classmethod
    def get_by_email(cls, email):
        return cls.query().filter(cls.email == email.lower()).get()

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
    name = ndb.StringProperty()
    creator = ndb.IntegerProperty() # refers to account_id
    old_creator_name = ndb.StringProperty() # for when account no longer exists
    created = ndb.DateTimeProperty()
    content = ndb.StringProperty(repeated=True)
    pseudonyms = ndb.StringProperty(repeated=True)
    number_of_pairs = ndb.IntegerProperty()
    filetype = ndb.StringProperty()

    @classmethod
    def all(cls):
        return cls.query().order(cls.name)

    def content_rows(self):
        return '\n'.join(self.content)

    def get_creator_name(self):
        if self.creator:
            account = UserAccount.get_by_id(self.creator)
            if account:
                return account.name or account.nickname
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

    def get_pseudonym(self, filename):
        i = self.content.index(filename)
        if not self.pseudonyms:
            self.add_pseudonyms()
        return self.pseudonyms[i]

    def add_pseudonyms(self):
        """ Add a list of pseudonyms. This function can be deleted once all file lists have pseudonyms ... """
        pseudonyms = range(len(self.content))
        shuffle(pseudonyms)
        self.pseudonyms = map(str, pseudonyms)
        self.put()

    @classmethod
    def name_in_use(cls, name):
        """ Check if a file list name is already in use """
        for entity in cls.query():
            if name == entity.name:
                return True
        return False



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
@app.route('/pairwise/add_current_user_as_admin')
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


@admin('/pairwise/get_comparisons')
def get_comparisons():
    page = request.args.get('page', type=int, default=1)
    comparisons = [c.formatted_dict() for c in PwvComparison.all(page=page)]
    comparisons_count = PwvComparison.query().count()
    return jsonify({'model': 'PwvComparison',
                    'entities': comparisons,
                    'count': comparisons_count})


@admin('/pairwise')
def home():
    user = UserAccount.current
    comparisons = PwvComparison.all(page=1)
    comparisons_count = PwvComparison.query().count()
    test_count = PwvComparison.count_tests()
    rounds = PwvRound.all()
    users = UserAccount.all()

    logging.info("Welcome, {}".format(user.nickname))
    return render_template('admin_home.html', user=user, rounds=rounds,
                           test_count=test_count,
                           change_user=change_user_link(),
                           comparisons=comparisons, users=users,
                           to_client={'comparisonsCount': comparisons_count,
                                      'itemsPerPage': ITEMS_PER_PAGE})
    # Serve admin home page that lists comparisons, rounds, judges, video lists, with links to the other pages


@admin('/pairwise/todayswork')
def todays_work():
    """ Page with a breakdown of comparisons completed today by user and round """
    timezone = request.args.get('timezone', type=float)
    utc_time = "GMT{:+}".format(timezone)
    comparison_query = PwvComparison.today(timezone_offset=timezone)
    users = {}
    for comparison in comparison_query:
        judge = comparison.get_judge_name()
        round_ = comparison.get_round_name()
        if not judge in users:
            users[judge] = {round_: 1}
        elif not round_ in users[judge]:
            users[judge][round_] = 1
        else:
            users[judge][round_] += 1
    return render_template('admin_today.html', user=UserAccount.current,
                           users=users, utc_time=utc_time)



@admin('/pairwise/user/<int:account_id>')
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
                           change_user=change_user_link(),
                           to_client = {"rounds": rounds, "accountId": account_id,
                                        "account": account.to_dict(), "userNames": names,
                                        "userEmails": emails},
                           comparisons=comparisons)

@admin('/pairwise/new_user')
def new_user_page():
    """PWV admin make new user page"""
    user = UserAccount.current
    #account = UserAccount()
    users = UserAccount.all()
    user_names = [(u.name or u.nickname) for u in users]
    user_emails = [u.email for u in users]
    rounds = PwvRound.all()
    return render_template('admin_new_user.html', user=user, rounds=rounds,
                           change_user=change_user_link(),
                           to_client = {'names': user_names, 'emails': user_emails})


@admin('/pairwise/new_weight')
def new_weight_page():
    logging.info('new weight page')
    round_id = request.args.get('round', type=int)
    round_ = PwvRound.get_by_id(round_id)
    if round_.file_list:
        file_list = round_.get_file_list().content
    else:
        abort(404)
    weight = Weighting(
        parent=round_.key,
        created=datetime.datetime.now(),
        name=get_new_weight_name(),
        left=file_list,
        right=file_list,
        weight=1)
    key = weight.put()
    file_list = round_.get_file_list().content
    round_ = round_.to_dict_with_id()
    return render_template('admin_weight.html',
                           user=UserAccount.current,
                           round_=round_,
                           weight=weight,
                           new=True,
                           to_client={'round': round_,
                                      'weight': weight.to_dict(),
                                      'fileList': file_list,
                                      'id': key.id(),
                                      'newWeight': True})
@admin('/pairwise/weight')
def weight_page():
    logging.info('weight page')
    round_id = request.args.get('round', type=int)
    weight_id = request.args.get('weight', type=int)
    weight = ndb.Key(PwvRound, round_id, Weighting, weight_id).get()
    if not weight:
        abort(404)
    round_ = PwvRound.get_by_id(round_id)
    file_list = round_.get_file_list().content
    round_ = round_.to_dict_with_id()
    return render_template('admin_weight.html',
                           user=UserAccount.current,
                           round_=round_,
                           weight=weight,
                           new=False,
                           to_client={'round': round_,
                                      'weight': weight.to_dict(),
                                      'id': weight_id,
                                      'fileList': file_list,
                                      'newWeight': False})



@admin('/pairwise/edit_weight', methods=['POST'])
def edit_weight():
    edits = request.get_json()
    weight_id = edits['weightId']
    round_id = edits['roundId']
    weight_key = ndb.Key(PwvRound, round_id, Weighting, weight_id)
    weight = weight_key.get()
    logging.info("""edit weight:
---weight_id=%s
---weight=%s
---edits=%s""", weight_id, weight, edits)
    if 'weight' in edits:
        weight.weight = float(edits['weight'])
    for attr in ['name', 'left', 'right']:
        if attr in edits:
            setattr(weight, attr, edits[attr])
    weight.count_duplicates()
    key = weight.put()
    return jsonify({'editedWeightId': weight_id, 'weight': weight.to_dict()})


@admin('/pairwise/delete_weight')
def delete_weight():
    round_id = request.args.get('round', type=int)
    weight_id = request.args.get('weight', type=int)
    key = ndb.Key(PwvRound, round_id, Weighting, weight_id)
    key.delete()
    return jsonify({'deletedWeightId': weight_id, 'roundId': round_id})


@admin('/pairwise/round/<int:round_id>')
def round_page(round_id):
    """ PWV admin round page """
    user = UserAccount.current
    round_ = PwvRound.get_by_id(round_id)
    if not round_:
        abort(404)  # round doesn't exist (possibly has been deleted)
    rounds_info = [{
        'name': r.name,
        'file_list': getattr(r.get_file_list(), 'content', None),
        'id': r.key.id()} for r in PwvRound.all()]

    comparisons = PwvComparison.by_round_id(round_id)
    logging.info('comparisons by round')
    #logging.info(comparisons.count())
    users = UserAccount.all()
    if round_.file_list:
        file_list = FileList.get_by_id(round_.file_list)
        file_list_content = file_list.content
    else:
        file_list = None
        file_list_content = None
    file_lists = FileList.all()
    creator = round_.get_creator()
    weights = Weighting.query(ancestor=round_.key)

    # n.b. in the template, use user.in_round(round_) to check whether user is in the
    # selected round or not
    return render_template('admin_round.html', user=user, round_=round_,
                           rounds = rounds_info, round_id=round_id,
                           change_user=change_user_link(),
                           creator=creator, comparisons=comparisons, users=users,
                           file_lists=file_lists, file_list=file_list,
                           weights=weights,
                           to_client = {'roundsInfo': rounds_info, 'round': round_.to_dict(),
                                        'roundId': round_id, 'fileList': file_list_content})

@admin('/pairwise/file_list/<int:file_list_id>')
def file_list_page(file_list_id):
    """ PWV admin file list page """
    rounds = PwvRound.query().filter(PwvRound.file_list == file_list_id) #.fetch()
    file_list = FileList.get_by_id(file_list_id)
    return render_template('admin_file_list.html', user=UserAccount.current,
                           rounds=list(rounds),
                           change_user=change_user_link(),
                           file_list=file_list, to_client={'id': file_list_id})

@admin('/pairwise/new_round')
def new_round_page():
    round_ = add_default_round()
    rounds_info = [{
        'name': r.name,
        'file_list': getattr(r.get_file_list(), 'content', None),
        'id': r.key.id()} for r in PwvRound.all()]
    users = UserAccount.all()
    file_lists = FileList.all()
    creator = round_.get_creator()
    # n.b. in the template, use user.in_round(round_) to check whether user is in the
    # selected round or not
    return render_template('admin_round.html',
                           user=UserAccount.current,
                           round_=round_,
                           rounds=rounds_info,
                           round_id=round_.key.id(),
                           change_user=change_user_link(),
                           creator=creator,
                           comparisons=[],
                           users=users,
                           file_lists=file_lists,
                           file_list=None,
                           weights=None,
                           to_client = {'roundsInfo': rounds_info, 'round': round_.to_dict(),
                                        'roundId': round_.key.id(), 'fileList': None})



@admin('/pairwise/test_comp')
def test_comp_page():
    rounds = PwvRound.all()
    return render_template('admin_test_comp.html', user=UserAccount.current,
                            rounds=rounds,
                            change_user=change_user_link(),
                           to_client={'rounds': PwvRound.all_dicts()})



##########################
# ADMIN FUNCTIONS RETURNING CSV
###############################
def query_to_csv(q, fieldnames=None, convert=None):
    """ Convert an NDB query to a CSV string """
    # Note, this may use a lot of memory/time if the query is large
    # Ideally we should (i) yield a line at a time so it can be written
    # gradually (ii) write to cloud storage first and then allow the user to
    # download the file once it has been written
    output = StringIO.StringIO()
    if convert is None:
        convert=lambda entity: entity.to_dict()
    if fieldnames is None:
        model = ndb.Model._lookup_model(q.kind)
        properties = model._properties.keys()
        fieldnames = properties
    writer = csv.DictWriter(output, fieldnames=fieldnames,
                            restval="n/a", extrasaction='ignore')
    writer.writeheader()
    for entity in q:
        writer.writerow(convert(entity))
    r = output.getvalue()
    output.close()
    return r

def date_for_filename():
    return datetime.datetime.now().strftime("%Y-%m-%d %H%M")



@admin('/pairwise/all_comparisons_csv')
def all_comparisons_csv():
    q = PwvComparison.query()
    fieldnames = ['judge', 'round', 'left', 'right', 'result', 'created', 'completed']
    csv = query_to_csv(q, fieldnames=fieldnames, convert=PwvComparison.formatted_dict)
    output = make_response(csv)
    filename = date_for_filename() + "_all.csv"
    output.headers["Content-Disposition"] = "attachment; filename=" + filename
    output.headers["Content-type"] = "text/csv"
    return output

@admin('/pairwise/comparisons_csv')
def comparisons_by_round_csv():
    round_id = request.args.get('round', type=int)
    round_key = ndb.Key(PwvRound, round_id)
    round_ = round_key.get()
    q = PwvComparison.query(ancestor=round_key)
    fieldnames = ['judge', 'round', 'left', 'right', 'result', 'created', 'completed']
    csv = query_to_csv(q, fieldnames=fieldnames, convert=PwvComparison.formatted_dict)
    output = make_response(csv)
    filename = date_for_filename() + "_" + round_.name + ".csv"
    output.headers["Content-Disposition"] = "attachment; filename=" + filename
    output.headers["Content-type"] = "text/csv"
    return output

@admin('/pairwise/new_file_list')
def new_file_list_page():
    return render_template("admin_new_file_list.html",
                           user=UserAccount.current)

#TODO:
# Make an open function returning all comparisons for a given round
# (This will be easier to access from R if it does not require any log in
# or admin rights)

#####################################################################
# ADMIN FUNCTIONS RETURNING JSON
#####################################################################

@admin('/pairwise/remove_test_comps')
def remove_test_comps():
    PwvComparison.delete_tests()
    logging.info("remove_test_comps")
    return jsonify({"deleted": True})
    # TODO: also need to update round information - reduce number
    # of file views etc.
    # Serve admin home page that lists comparisons, rounds, judges, video lists, with links to the other pages


@admin('/pairwise/add_user', methods=['POST'])
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
        email=request.json['email'].lower(),
        admin=request.json['admin'],
        )
    key = new_account.put()
    return jsonify({'round_id': key.id()})


@admin('/pairwise/add_round', methods=['POST'])
def add_round():
    logging.info('adding new round')
    judge_ids = [int(account_id) for account_id in request.json['judges']]
    if 'fileList' in request.json:
        file_list_key = add_file_list(content=request.json['fileList'],
                          file_type=request.json.get('fileType', None))
    round_ = PwvRound(
        name=request.json['name'],
        opened=request.json['opened'],
        file_list=file_list_key.id(),
        judges=judge_ids,
        creator=UserAccount.current.key.id(),
        created=datetime.datetime.now(),
        max_views=3,
        max_views_by_user=None,
        max_comparisons=None,
        max_comparisons_by_user=1,
        min_time=30,
        warn_time=None
        )
    round_id = round_.put().id()
    for judge_id in judge_ids:
        account = UserAccount.get_by_id(judge_id)
        account.rounds.append(round_id)
        account.put()

    return jsonify({'round_id': round_id})

@admin('/pairwise/get_user_by_email/<email>')
def get_user_by_email(email):
    logging.info('get_user_by_email: looking up email %s', email)
    account = UserAccount.get_by_email(email)
    user_id_is_none = account.user_id is None
    return jsonify({'account': account.to_dict(), 'userIdIsNone': user_id_is_none})


def get_new_round_name():
    existing_round_names = [r.name for r in PwvRound.query()]
    i = 1
    name = "New round"
    while name in existing_round_names:
        name = "New round ({})".format(i)
        i += 1
    return name

def get_new_weight_name():
    existing_weight_names = [w.name for w in Weighting.query()]
    i = 1
    name = "New weighting"
    while name in existing_weight_names:
        name = "New weighting ({})".format(i)
        i += 1
    return name

def add_default_round():
    logging.info('adding blank new round')
    round_ = PwvRound(
        name=get_new_round_name(),
        opened=False,
        #file_list=[],
        #judges=[],
        creator=UserAccount.current.key.id(),
        created=datetime.datetime.now(),
        max_views=3,
        max_views_by_user=None,
        max_comparisons=None,
        max_comparisons_by_user=1,
        min_time=30,
        warn_time=None)
    round_.put()
    return round_


@admin('/pairwise/edit_user/<int:account_id>', methods=['POST'])
def edit_user(account_id):
    account = UserAccount.get_by_id(account_id)
    edits = request.json
    if 'name' in edits:
        account.name = edits['name']
    if 'admin' in edits:
        account.admin = edits['admin']
    if 'email' in edits:
        user = users.User(edits['email'].lower())
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

@admin('/pairwise/delete_user/<int:account_id>', methods=['GET'])
def delete_user(account_id):
    account = UserAccount.get_by_id(account_id)
    account.key.delete()
    PwvComparison.delete_by_judge_id(account_id)
    #TODO: for all file lists created by this user, replace creator=None and
    # defunctCreatorName = the old name
    return jsonify({"deletedAccountId": account_id})

@admin('/pairwise/edit_round/<int:round_id>', methods=['POST'])
def edit_round(round_id):
    round_ = PwvRound.get_by_id(round_id)
    edits = request.json
    if 'fileList' in edits:
        file_list_key = add_file_list(content=edits['fileList'],
                          file_type=edits.get('fileType', None))
        round_.file_list = file_list_key.id()

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

    other_fields = {'name', 'opened', 'max_views', 'max_comparisons', 'max_views_by_user', 'max_comparisons_by_user', 'min_time', 'warn_time'}
    for field in other_fields & set(edits):
        setattr(round_, field, edits[field])

    key = round_.put()
    return jsonify({'round_id': key.id(), 'newRoundInfo': round_.to_dict()})

@admin('/pairwise/delete_round/<int:round_id>', methods=['GET'])
def delete_round(round_id):
    round_ = PwvRound.get_by_id(round_id)
    round_.key.delete()
    PwvComparison.delete_by_round_id(round_id)
    return jsonify({'deletedRoundId': round_id})



@admin('/pairwise/add_fake_file_list/<name>')
def add_fake_file_list(name):
    file_list = FileList(
        account_id=UserAccount.current.key.id(),
        name=name,
        created=datetime.datetime.now(),
        content=["1", "2", "3", "4", "5"])
    key = file_list.put()
    return jsonify({'fileListId': key.id()})



def add_file_list(content, file_type=None, name=None):
    pseudonyms = range(len(content))
    shuffle(pseudonyms)
    number = 1
    while FileList.name_in_use(name):
        name = "{} ({})".format(name, number)
        number += 1

    file_list = FileList(
        creator=UserAccount.current.key.id(),
        name=name,
        created=datetime.datetime.now(),
        content=content,
        pseudonyms=map(str, pseudonyms),
        filetype=file_type
        )
    key = file_list.put()
    return key


@admin('/pairwise/add_file_list2', methods=['POST'])
def add_file_list_wrap2():
    key = add_file_list(content=request.json['file_list'],
                        file_type=request.json['file_type'],
                        name=request.json['description'])
    return jsonify({'fileListId': key.id()})

@session('/pairwise/add_file_list', admin_required=True, methods=['POST'])
def add_file_list_wrap():
    logging.info("add file list")
    key = add_file_list(content=request.json['fileList'],
                        file_type=request.json['fileType'],
                        name=request.json['description'])
    return jsonify({'fileListId': key.id()})


@admin('/pairwise/delete_file_list')
def delete_file_list():
    """ Deletes a file list, unless the file list is attached to a round """
    file_list_id = request.args.get('id', type=int)
    logging.info("""delete_file_list: file_list_id=%s""", file_list_id)
    r = PwvRound.query().filter(PwvRound.file_list == file_list_id).get()
    logging.info("""delete_file_list: file_list_id=%s
    --query=""", file_list_id, r)
    if r is None:
        ndb.Key(FileList, file_list_id).delete()
        return jsonify({'deleted': True})
    else:
        # there was a round using this file list, so don't delete
        return jsonify({'deleted': False})

    """round_keys = []
    for r in PwvRound.all():
        if r.file_list_id == file_list_id:
            r.file_list_id = None
            round.keys.append(r.key)
    if round_keys:
        ndb.delete_multi(round_keys)"""



# USER FUNCTIONS RETURNING JSON


def add_comparison(round_id, test=False):
    round_key = ndb.Key("PwvRound", round_id)
    round_ = PwvRound.get_by_id(round_id)
    file_list = round_.get_file_list()
    #logging.info("round ")
    #logging.info(round_key.id())
    #logging.info(round_)
    user = UserAccount.current
    pair_index, left, right = select_files(round_, user)
    if pair_index is None:
        return None
    comparison = PwvComparison(
        parent=round_key,
        judge=user.key.id(),
        created=datetime.datetime.now(),
        pair=pair_index,
        left=left,
        right=right,
        test=test)
    # Not sure why I wrote this - do not want to store min_time and warn_time
    # in the comparison
    #if round_.min_time is not None:
    #    comparison.min_time = round_.min_time
    #if round_.warn_time is not None:
    #    comparison.warn_time = round_.warn_time
    comparison_key = comparison.put()
    logging.info("""add_comparison:
    --round=%s
    --judge=%s
    --pair=%s
    --left=%s
    --right=%s""", round_key, user.key.id(),pair_index, left, right)
    return {'comparisonId': comparison_key.id(),
            'left': left,
            'right': right,
            'pseudonym_left': file_list.get_pseudonym(left),
            'pseudonym_right': file_list.get_pseudonym(right),
            'filetype': file_list.filetype,
            'min_time': round_.min_time,
            'warn_time': round_.warn_time}

@admin('/pairwise/add_comparison_admin')
def add_comparison_admin_wrap():
    logging.info("add_comparison_admin_wrap")
    round_id = request.args.get('round', type=int)
    test = request.args.get('test', default=False, type=bool)
    result = add_comparison(round_id, test)
    return jsonify(result)

@session('/pairwise/add_comparison')
def add_comparison_wrap():
    logging.info("add comparison wrap")
    round_id = request.args.get('round', type=int)
    test = request.args.get('test', default=False, type=bool)
    return jsonify(existing_or_new_comparison(round_id, test))

def existing_or_new_comparison(round_id, test=False):
    """ Return an existing comparison if there is an incomplete one for this user
    and round. If not, add a new comparison and return it. """
    logging.info("""existing_or_new_comparison: round_id=%s, test=%s""", round_id, test)
    user_id = UserAccount.current.key.id()

    # First check for an existing comparison for this user and round
    existing = PwvComparison.incomplete_by_judge_id(round_id, user_id).get()
    if existing:
        logging.info("""existing_or_new_comparison: existing one found. ID=%s""", existing.key.id())
        round_ = PwvRound.get_by_id(round_id)
        file_list = round_.get_file_list()
        return {'comparisonId': existing.key.id(),
                        'left': existing.left,
                        'right': existing.right,
                        'pseudonym_left': file_list.get_pseudonym(existing.left),
                        'pseudonym_right': file_list.get_pseudonym(existing.right),
                        'filetype': file_list.filetype,
                        'min_time': round_.min_time,
                        'warn_time': round_.warn_time
                        }
    else:
        logging.info("""existing_or_new_comparison: adding new one""")
        return add_comparison(round_id, test)


@session('/pairwise/start_judging')
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
        new_comp = existing_or_new_comparison(round_id)
        if new_comp is None:
            return 'end', None
            # no more comparisons can be added due to round exclusion rules (or any other reason)
        else:
            return 'comparison', new_comp
    else:
        return 'choose round', permitted_rounds

@session('/pairwise/get_rounds')
def get_rounds():
    """ Return the list of rounds permitted for the signed in user """
    permitted_rounds = PwvRound.list_by_judge_id(UserAccount.current.key.id())
    return jsonify({'rounds': permitted_rounds})

def select_files(round_, user):
    weights = Weighting.query(ancestor=round_.key).fetch()
    if weights:
        return select_files_weighted(round_, user, weights)
    else:
        return select_files_unweighted(round_, user)



def random_weighted_selection(weights):
    sum_weights = float(sum(weights))
    prob_selection = [weight / sum_weights for weight in weights]
    rand = random()
    for i, prob in enumerate(prob_selection):
        if rand < prob:
            return i
        rand -= prob

def select_files_weighted(round_, user, weights):
    logging.info("""Selecting files with weights
    round_id=%s,
    weights=%s""", round_.key.id(), [weight.key.id() for weight in weights])
    file_list = round_.get_file_list()
    number_of_files = len(file_list.content)
    # 1. Find out which files and pairs will be excluded for this user
    excl_file_indices, excl_pairs = get_exclusions(round_, user)
    #excl_files = [file_list.content[i] for i in excl_file_indices]
    # 2. Count number of comparisons remaining in each weighting scheme
    # 3. Probability of selection proportional to the
    # adjusted_weight = number of comparisons * weight
    comparisons_by_weight = []
    adjusted_weights = []   # total weight for each weighting scheme
    for weight in weights:
        comparisons = []
        comparisons_by_weight.append(comparisons)
        for a in weight.left:
            ai = file_list.content.index(a)
            if ai in excl_file_indices:
                continue
            for b in weight.right:
                bi = file_list.content.index(b)
                if bi in excl_file_indices:
                    continue
                k = pair_to_k(min(ai, bi), max(ai, bi), number_of_files)
                if k not in excl_pairs:
                    comparisons.append((k, a, b))
        adjusted_weights.append(len(comparisons) * weight.weight)
    logging.info("""Selecting files with weights
    n comparisons=%s
    adjusted_weights=%s""", [len(comparisons) for comparisons in comparisons_by_weight],
        adjusted_weights)
    if not any(comparisons for comparisons in comparisons_by_weight):
        return None, None, None
    chosen_scheme = random_weighted_selection(adjusted_weights)
    k, a, b = random_choice(comparisons_by_weight[chosen_scheme])
    if random() < .5:
        return k, a, b
    else:
        return k, b, a

def get_exclusions(round_, user):
    file_list = round_.get_file_list()
    excluded_pairs = set()
    excluded_files = set()
    if round_.max_views_by_user is not None or round_.max_comparisons_by_user is not None:
        user_id = user.key.id()
        user_pairs_viewed = Counter()
        user_files_viewed = Counter()
        user_comparisons = PwvComparison.completed_by_judge_id(round_.key.id(), user_id)
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
    excluded_file_indices = set(map(file_list.content.index, excluded_files))
    if round_.max_views is not None:
        round_files_viewed = Counter(round_.files_viewed)
        excluded_file_indices |= set(f for f, c in round_files_viewed.items()
                                  if c >= round_.max_views)
    if round_.max_comparisons is not None:
        excluded_pairs |= set(round_.pairs_viewed)
    excluded_pairs = list(excluded_pairs)
    return excluded_file_indices, excluded_pairs



def select_files_unweighted(round_, user):
    """ Select two files for comparison given a round and user
        1. make list of pairs to be excluded because already viewed too many times by
        (i) this user or (ii) any user, according to the rules specified for the round
        2. make list of files to be excluded because already viewed too many times
        3. randomly select from all pairs excluding the excluded pairs
        4. if L, R are in the excluded_files list then add this pair to the excluded_pairs
        list and redo the selection. Repeat until a pair can be found that is not excluded.

    """
    file_list = round_.get_file_list()
    excluded_pairs = set()
    excluded_files = set()
    if round_.max_views_by_user is not None or round_.max_comparisons_by_user is not None:
        user_id = user.key.id()
        user_pairs_viewed = Counter()
        user_files_viewed = Counter()
        user_comparisons = PwvComparison.completed_by_judge_id(round_.key.id(), user_id)
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
    excluded_file_indices = set(map(file_list.content.index, excluded_files))
    if round_.max_views is not None:
        round_files_viewed = Counter(round_.files_viewed)
        excluded_file_indices |= set(f for f, c in round_files_viewed.items()
                                  if c >= round_.max_views)
    if round_.max_comparisons is not None:
        excluded_pairs |= set(round_.pairs_viewed)
    excluded_pairs = list(excluded_pairs)
    number_of_files = len(file_list.content)
    if len(excluded_file_indices) == number_of_files:
        return None, None, None     # no files left to view

    number_of_pairs = file_list.get_number_of_pairs()
    logging.info("""select_files:
    --number_of_files=%s
    --user_id=%s
    --excluded_pairs=%s
    --excluded_file_indices=%s""", number_of_files, user.key.id(), excluded_pairs, excluded_file_indices
    )

    while True:
        if len(excluded_pairs) >= number_of_pairs:
            return None, None, None     # no pairs left so end the application or refuse test

        pair_index = randrange_excluding(number_of_pairs, excluded_pairs)
        a, b = kth_pair(pair_index, number_of_files)
        logging.info("""select_files: pair_index=%s, a=%s, b=%s""", pair_index, a, b)
        if a in excluded_file_indices or b in excluded_file_indices:
            # if files are on the excluded file list, add the pair to the excluded pairs
            # list and try again
            #logging.info("""select_files: a or b were in excluded_file_indices:--a=%s b=%s""", a, b)
            excluded_pairs.append(pair_index)
        else:
            # Randomly choose which file will appear on left and right
            if random() < .5:
                return pair_index, file_list.content[a], file_list.content[b]
            else:
                return pair_index, file_list.content[b], file_list.content[a]


@admin('/pairwise/comparison')
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
    # not currently used?

@session('/pairwise/complete_comparison', methods=['POST'])
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

@admin('/pairwise/complete_comparison_admin', methods=['POST'])
def complete_comparison_admin_wrap():
    """ Complete the incomplete comparison for the current user in the given round.
    An error will be logged if there are zero, or more than one incomplete comparison for the current user
    in the given round.
    If the comparison is completed successfully then also get the next thing for the user
    to do and return that to the client software."""
    d = request.get_json()
    comparison_id = d['comparison']
    round_id = d['round']
    choice = d['choice']
    completed_id = complete_comparison(comparison_id, round_id, choice)
    return jsonify({"completed_id": completed_id, "choice": choice})


def mark_in_round(round_, comparison):
    """ Mark as completed in the round a pair and files from a comparison """
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
        logging.info("""complete_comparison
        --comparison_id=%s
        --comparison.result=%s""", comparison_id, comparison.result)
        comparison_key = comparison.put()
        return comparison_key.id()
    else:
        # the comparison ID conflicts with the user_id
        # -- something has gone wrong with either the DB or the client software
        raise BadPostError

@app.route('/pairwise/create_session')
def create_session_page():
    logging.info("create_session_page")
    user = users.get_current_user()
    if not user:
        return redirect(users.create_login_url(request.full_path))
    account = UserAccount.get_by_user(user)
    if not account:
        logging.info("create_session_page: creating new account")
        account = UserAccount()
        account.nickname = user.nickname()
        #login = users.create_login_url(request.full_path)
        #account.change_user = users.create_logout_url(login)
        return render_template("signin_for_session.html", user=account,
                               change_user=change_user_link())
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
    return render_template("session_okay.html", user=account,
                           change_user=change_user_link())

def change_user_link():
    """ Return link that signs the user out and allows them to sign back in
    as another user """
    login = users.create_login_url(request.full_path)
    return users.create_logout_url(login)

@app.route('/pairwise/show_current_user_info')
def show_current_user_info():
    info = {}
    user = users.get_current_user()
    if user:
        info['userExists'] = True
        info['userEmail'] = user.email()
        info['userId'] = user.user_id()
        info['userNickname'] = user.nickname()
        account = UserAccount.get_by_email(user.email())
        if account:
            info['accountFromEmailExists'] = True
            info['accountFromEmail'] = account.to_dict()
        account_from_id = UserAccount.query().filter(UserAccount.user_id == user.user_id()).get()
        if account_from_id:
            info['accountFromIdExists'] = True
            info['accountFromId'] = account_from_id.to_dict()
    else:
        info['userExists'] = False
    auth = request.authorization
    if auth:
        info['authExists'] = True
        info['authUsername'] = auth.username
        info['authPassword'] = auth.password
        account_from_auth = UserAccount.get_by_token(auth.password)
        if account_from_auth:
            info['accountFromAuthExists'] = True
            info['accountFromAuth'] = account.to_dict()
    else:
        info['authExists'] = False
    return jsonify(info)

@app.route('/pairwise/start_session')
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
    #login = users.create_login_url(request.path)
    #account.change_user = users.create_logout_url(login)
    #message = """You are signed in to Google accounts as {}. However you do not
    #        have permission to access this page. <br />Click <a href="{}">here</a> to
    #        sign out and then sign in as a different user.""".format(nickname, logout)

    return render_template("no_permission.html", user=account,
                           change_user=change_user_link(),
                           ), 403

@app.errorhandler(NotLoggedInError)
def not_logged_in_page(e):
    logging.error("Not logged in error")

    # Make a path to login then return to current page
    login_url = users.create_login_url(request.full_path)
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

def pair_to_k(a, b, n):
    """ Return the position number of a pair a, b (reverse of kth_pair) """
    for i in xrange(a):
        b += n - i - 2
    return b - 1

def randrange_excluding(stop, excl_list):
    """ Return a random integer n such that 0 <= n < b
        but n is not in excl_list. The excl_list will be sorted in-place """
    logging.info("""randrange_excluding: --stop: %s   --excl_list len: %s""",
                 stop, len(excl_list))
    if excl_list:
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
    else:
        return randrange(stop)
