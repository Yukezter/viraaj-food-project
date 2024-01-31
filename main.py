from urllib.parse import urlencode
import uuid
import json
import fcntl
import requests
from flask import Flask, request, render_template, redirect, url_for, g, make_response

APP_NAME = "FoodApp"
YELP_API_KEY = "Ds2alHcCHxAgWWvd8y7j9qqQ-JEg-02RNRHeG-OcJgV8BII2RnHoWm2lYiFpGs9Rj7Vob1kxnHR-tbrMI84t_Lz9LK9aak6HHNGOTBGPLK1c5_H-6Qh9iWeEfs2FZXYx"
YELP_BASE_URL = "https://api.yelp.com/v3"
YELP_LIMIT = 15

global db
db_file_name = "db.json"


def save_db_to_file():
    with open(db_file_name, "w") as db_file:
        fcntl.flock(db_file, fcntl.LOCK_EX)
        json.dump(db, db_file)
        fcntl.flock(db_file, fcntl.LOCK_UN)
        print("Saved db to local file...")


try:
    with open(db_file_name, "r") as fp:
        db = json.load(fp)
except FileNotFoundError:
    db = {"users": {}, "parties": {}}

    save_db_to_file()

yelp_headers = {"accept": "application/json", "Authorization": "Bearer " + YELP_API_KEY}

def yelp(path, params=None):
    url = f"{YELP_BASE_URL}{path}"

    if params is not None:
      url += f'?{urlencode(params)}'  

    response = requests.get(url, headers=yelp_headers)

    return response.json()


app = Flask(  # Create a flask app
    __name__,
    template_folder="templates",  # Name of html file folder
    static_folder="static",  # Name of directory for static files
)

# Routes
# Home (Page)           GET  /
# Create User (Page)    GET  /users/create
# Create User           POST /users
# Create Party (Page)   GET  /parties/create
# Create Party          POST /parties
# Party (Page)          GET  /parties/{id}
# Submit Choices        POST /parties/{id}

cookie_name = f"{APP_NAME}_user_id"


@app.before_request
def before_request():  # This function code runs before every request
    if request.endpoint != "create_user_page" and request.endpoint != "create_user":
        user_id = request.cookies.get(cookie_name)

        if user_id is None:
            return redirect(url_for("create_user_page", return_to=request.url))

        user = db["users"].get(user_id)

        if user is None:
            return redirect(url_for("create_user_page", return_to=request.url))

        g.user = user


@app.after_request
def after_request(response):
    if request.method == "POST":
      response.call_on_close(save_db_to_file)
    return response


# GET '/' for the home page
@app.route("/")
def home_page():
    parties = []

    for party_id in g.user["parties"]:
        party = db["parties"][party_id]

        if party is not None:
            parties.append(party)

    return render_template("home.html", user=g.get("user"), parties=parties)


# GET '/about' for the about page
@app.route("/about")
def about_page():
    return render_template("about.html")


# GET '/users/create' for create user page
@app.route("/users/create", methods=["GET"])
def create_user_page():
    return_to = request.args.get("return_to", url_for("home_page"))
    return render_template("create-user.html", return_to=return_to)


# POST '/users' to save user to the database
@app.route("/users", methods=["POST"])
def create_user():
    user_id = str(uuid.uuid4())
    username = request.form["username"]

    user = {"id": user_id, "username": username, "parties": []}

    db["users"][user_id] = user

    resp = make_response(redirect(request.args.get("return_to", url_for("home_page"))))
    resp.set_cookie(cookie_name, user_id)

    return resp


# GET '/parties/create' to get create party page
@app.route("/parties/create", methods=["GET"])
def create_party_page():
    return render_template("create-party.html")


# POST '/parties/create' to save party to database
@app.route("/parties", methods=["POST"])
def create_party():
    party_id = str(uuid.uuid4())
    party_name = request.form["name"]
    location = request.form["location"]
    radius = request.form["radius"]

    party = {
        "id": party_id,
        "name": party_name,
        "location": location,
        "radius": int(radius),
        "owner": {
            'id': g.user["id"],
            'username': g.user['username']
        },
        "members": {g.user["id"]: {"page": 0, "choices": {}}},
        "matches": [],
    }

    db["parties"][party_id] = party
    db["users"][g.user["id"]]["parties"].append(party_id)

    return redirect(url_for("party_page", party_id=party_id))


# GET '/parties/<party_id>' to get businesses page
@app.route("/parties/<party_id>", methods=["GET"])
def party_page(party_id):
    party = db.get("parties", {}).get(party_id)

    if party is None:
        resp = make_response("Party not found", 400)
        return resp

    member = party["members"].setdefault(g.user["id"], {"page": 0, "choices": {}})

    radius_in_meters = int(party["radius"] * 1609.34)
    yelp_response = yelp("/businesses/search", {
        "limit": YELP_LIMIT,
        "location": party['location'],
        "radius": 40000 if radius_in_meters > 40000 else radius_in_meters,
        "sorty_by": "best_match",
        "offset": member["page"] * YELP_LIMIT,
    })

    businesses = []

    for business in yelp_response["businesses"]:
        print(json.dumps(business, indent = 4))
        businesses.append(
            {
                "id": business["id"],
                "name": business["name"],
                "url": business["url"],
                "image_url": business["image_url"],
                "rating": business["rating"],
                "review_count": business["review_count"],
                "price": business.get("price", "$"),
                "categories": ', '.join(c['title'] for c in business['categories']),
            }
        )

    return render_template("party.html", businesses=businesses, party=party)


# POST '/parties/<party_id>' to save chosen businesses
@app.route("/parties/<party_id>", methods=["POST"])
def submit_businesses(party_id):
    party = db.get("parties", {}).get(party_id)

    if party is None:
        resp = make_response("Party not found", 400)
        return resp

    # The code below won't run if party does not exist
    member = party["members"][g.user["id"]]
    member["page"] += 1

    for business_id, choice in request.form.items():
        if choice == "on":
            member["choices"][business_id] = True

            is_match = True
            for user_id, member in party["members"].items():
                if user_id == party['owner']['id']:
                    continue

                if member["choices"].get(business_id) is None:
                    is_match = False
                    break

            if is_match is False:
                break
            
            business = yelp(f"/businesses/{business_id}")

            party["matches"].append({
                "id": business["id"],
                "name": business["name"],
                "url": business["url"],
                "image_url": business["image_url"],
                "rating": business["rating"],
                "price": business["price"],
                "categories": ', '.join(c['title'] for c in business['categories']),
            })

    return redirect(url_for("party_page", party_id=party["id"]))


if __name__ == "__main__":  # Makes sure this is the main process
    app.run(  # Starts the site
        host="0.0.0.0",  # EStablishes the host, required for repl to detect the site
        port=8000,  # Select the port the machine hosts on
        debug=True,
    )
