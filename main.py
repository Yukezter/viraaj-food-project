import os
from datetime import datetime
from collections import UserDict
from urllib.parse import urlencode
import uuid
import json
import fcntl
import requests
from flask import Flask, request, render_template, redirect, url_for, g, make_response

APP_NAME = "FoodApp"
YELP_API_KEY = 'Ds2alHcCHxAgWWvd8y7j9qqQ-JEg-02RNRHeG-OcJgV8BII2RnHoWm2lYiFpGs9Rj7Vob1kxnHR-tbrMI84t_Lz9LK9aak6HHNGOTBGPLK1c5_H-6Qh9iWeEfs2FZXYx'
YELP_BASE_URL = 'https://api.yelp.com/v3'
YELP_LIMIT = 15

global db_prev_update_time

class Database(dict):
  # def __init__(self, *args):
  #   UserDict.__init__(self, args)
  
  def __init__(self,*arg,**kw):
    super(Database, self).__init__(*arg, **kw)
    global db_prev_update_time
    db_prev_update_time = datetime.now().timestamp()
    print('init!!!', db_prev_update_time)

  def __setitem__(self, item, value):
    print("You are changing the value of %s to %s!!", item, value)
    global db_prev_update_time
    db_prev_update_time = datetime.now().timestamp()
    super(Database, self).__setitem__(item, value)

  # def __init__(self, *args, **kwargs):
  #     self.update(*args, **kwargs)

  # def __getitem__(self, key):
  #     val = dict.__getitem__(self, key)
  #     print('GET', key)
  #     return val

  # def __setitem__(self, key, val):
  #     print('SET', key, val)
  #     dict.__setitem__(self, key, val)

  # def __repr__(self):
  #     dictrepr = dict.__repr__(self)
  #     return '%s(%s)' % (type(self).__name__, dictrepr)
      
  # def update(self, *args, **kwargs):
  #     print('update', args, kwargs)
  #     for k, v in dict(*args, **kwargs).items():
  #         self[k] = v

global db
db_file_name = 'db.json'

try:
  with open(db_file_name, 'r') as fp:
    db = Database(json.load(fp))
    
except FileNotFoundError:
  db = Database({
    'users': {},
    'parties': {}
  })

  with open(db_file_name, 'w') as db_file:
    json.dump(db, db_file)

def save_db_to_file():
  global db_prev_update_time
  last_db_sync_time = os.stat(db_file_name).st_ctime
  if last_db_sync_time < db_prev_update_time:
    with open(db_file_name, 'w') as db_file:
      fcntl.flock(db_file, fcntl.LOCK_EX)
      json.dump(db, db_file)
      fcntl.flock(db_file, fcntl.LOCK_UN)
      print('Saved db to local file...')

yelp_headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer ' + YELP_API_KEY
}

def yelp(path, params):
  radius = int(params.get('radius', 10) * 1609.34)
  if radius > 40000:
    radius = 40000

  params = urlencode({
    'limit': YELP_LIMIT,
    'location': params['location'],
    'radius': radius,
    'sorty_by': 'best_match',
    'offset': params.get('offset', 0),
  })

  url = f'{YELP_BASE_URL}{path}?{params}'
  response = requests.get(url, headers=yelp_headers)
  
  return response.json()

app = Flask(  # Create a flask app
    __name__,
    template_folder='templates',  # Name of html file folder
    static_folder='static'  # Name of directory for static files
)

# Routes
# Home (Page)           GET  /
# Create User (Page)    GET  /users/create
# Create User           POST /users
# Create Party (Page)   GET  /parties/create
# Create Party          POST /parties
# Party (Page)          GET  /parties/{id}
# Businesses (Page)     GET  /parties/{id}/businesses
# Submit Businesses     POST /parties/{id}/businesses

cookie_name = f'{APP_NAME}_user_id'
@app.before_request
def before_request(): # This function code runs before every request
  if request.endpoint != 'create_user_page' and request.endpoint != 'create_user':
    user_id = request.cookies.get(cookie_name)

    if user_id is None:
      g.redirect_to = request.endpoint
      return redirect(url_for('create_user_page'))
    
    user = db['users'].get(user_id)

    if user is None:
      g.redirect_to = request.endpoint
      return redirect(url_for('create_user_page'))

    g.user = user

@app.after_request
def after_request(response):
  response.call_on_close(save_db_to_file)

  return response

# GET '/' for the home page
@app.route('/')
def home_page():
  parties = []

  print('home page - user parties', g.user['parties'])

  for party_id in g.user['parties']:
    print('party_id', party_id)
    party = db['parties'][party_id]

    if party is not None:
      parties.append(party)

  return render_template('home.html', user=g.get('user'), parties=parties)

# GET '/about' for the about page
@app.route('/about')
def about_page():
  return render_template('about.html')

# GET '/users/create' for create user page
@app.route('/users/create', methods=['GET'])
def create_user_page():
  return render_template('create-user.html')

# POST '/users' to save user to the database
@app.route('/users', methods=['POST'])
def create_user():
  user_id = str(uuid.uuid4())
  username = request.form['username']

  user = {
    'id': user_id,
    'username': username,
    'parties': []
  }

  global db
  print(db)
  db['users'][user_id] = user
  print(db)

  resp = make_response(redirect(url_for(g.get('return_to', 'home_page'))))
  resp.set_cookie(cookie_name, user_id)
  
  return resp

# GET '/parties/create' to get create party page
@app.route('/parties/create', methods=['GET'])
def create_party_page():
  return render_template('create-party.html')

# POST '/parties/create' to save party to database
@app.route('/parties', methods=['POST'])
def create_party():
  party_id = str(uuid.uuid4())
  party_name = request.form['name']
  location = request.form['location']
  radius = request.form['radius']

  party = {
    'id': party_id,
    'name': party_name,
    'location': location,
    'radius': radius,
    'members': {
      g.user['id']: {
        'page': 0
      }
    },
    'matches': {}
  }

  db['parties'][party_id] = party
  db['users'][g.user['id']]['parties'].append(party_id)

  return redirect(url_for('party_page', party_id=party_id))

# GET '/parties/<party_id>' to get party page
@app.route('/parties/<party_id>', methods=['GET'])
def party_page(party_id):
  party = db['parties'][party_id]

  return render_template('party.html', party=party)

# GET '/parties/<party_id>/businesses' to get businesses page
@app.route('/parties/<party_id>/businesses', methods=['GET'])
def businesses_page(party_id):
  party = db['parties'][party_id]

  yelp_params = {
    'location': party['location'],
    'radius': int(party['radius']),
  }

  member = party['members'].get(g.user['id'])
  if member is None:
    db['parties']['members'][g.user['id']] = {
      'page': 0
    }

    member = db['parties']['members'][g.user['id']]

  page = member["page"]
  if page > 0:
    yelp_params['offset'] = (int(page) - 1) * YELP_LIMIT

  yelp_response = yelp('/businesses/search', yelp_params)

  # print(yelp_response)

  businesses = []

  for business in yelp_response['businesses']:
    categories = []
    for category in business["categories"]:
      categories.append(category["title"])

    businesses.append({
      "id": business["id"],
      "image_url": business["image_url"],
      "name": business["name"],
      "state": business["location"]["state"],
      "city": business["location"]["city"],
      "categories": categories,
      "rating": business["rating"],
      "review_count": business["review_count"],
      "url": business["url"]
    })

  return render_template('businesses.html', businesses=businesses, party=party)

# POST '/parties/<party_id>/businesses' to save chosen businesses
@app.route('/parties/<party_id>/businesses', methods=['POST'])
def submit_businesses(party_id):
  party = db['parties'].get(party_id)

  if party is None:
    resp = make_response("Party not found", 400)
    return resp

  party['members'][g.user.id]["page"] += 1

  for business_id, value in request.form.items():
    if value == 'on':
      for user_id, member in party['members'].items():
        if member['choices'].get(business_id) is None:
          break

      party['matches'][business_id] = True

  return redirect(url_for('businesses_page'))

if __name__ == "__main__":  # Makes sure this is the main process
  app.run(  # Starts the site
      host=
      '0.0.0.0',  # EStablishes the host, required for repl to detect the site
      port=8000,  # Randomly select the port the machine hosts on.
    debug=True
  )

# Party
# {
#   "groups": {
#     "123": {
#       "id": "123",
#       "name": "Taco Tuesday",
#       "description": "Taco Tuesdays with friends",
#       "location": "New York",
#       "range": 100,
#       "members": ["user_id1"]
#     }
#   }
# }

# User (Party Member)
# {
#   "users": {
#     "123": {
#       "id": "123",
#       "name": "Jane Doe",
#       "groups": ["group_id1", "group_id2"]
#     }
#   }
# }