# db dictionary
db = {
  'users': {
    '1': {
      'id': '1',
      'name': 'Jane Doe',
      'parties': ['1', '2']
    },
    '2': {
        'id': '2',
        'name': 'Jane Doe',
        'parties': ['1', '2']
}
  },
  'parties': {
    '1': {
      'id': '1',
      'name': 'Taco Tuesday',
      'description': 'Taco Tuesdays with friends',
      'location': 'Irvine',
      'range': 20,
      'owner': '1',
      'members': ['1', '2']
    },
    '2': {
      'id': '2',
      'name': 'Taco Tuesday',
      'description': 'Taco Tuesdays with friends',
      'location': 'Irvine',
      'range': 20,
      'owner': '1',
      'members': ['1', '2', '3']
    },
  }
}

# Get dictionary key value

# print(db['users']['2'])

# user_id = '1'
# print(db.get('users').get(user_id))

# Set dictionary key value


# db['users']['3'] = {
#     'id': '3',
#     'name': 'Jack',
#     'parties': [] 
# }

# print(db.get('users').get('3'))

# db['parties']['3'] = {
#     'id': '3',
#     'name': 'Wednesday Lunch',
#     'location': 'Irvine',
#     'owner': '3', # user's id
#     'members': ['3'] # user ids
# }

# Test

# Part 1: Access user with user id 5
user_5 = db.get('users').get('5')

# Part 2: If user does not exist, add new user with id 5
if user_5 is None:
    db['users']['5'] = {
    'id': '5',
    'name': 'James',
    'parties': []
}
    
# Part 3: Print user with user id 5
print(db['users']['5'])