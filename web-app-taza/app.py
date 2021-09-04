#!/usr/bin/env python3

from flask import Flask, flash, render_template, request, redirect, url_for, make_response, session, redirect
from markupsafe import escape
import pymongo
import datetime
from bson.objectid import ObjectId
import os
import subprocess
import credentials
# instantiate the app
app = Flask(__name__)
app.secret_key = 'mysecret'

# load credentials and configuration options from .env file
# if you do not yet have a file named .env, make one based on the template in env.example
config = credentials.get()

# turn on debugging if in development mode
if config['FLASK_ENV'] == 'development':
    # turn on debugging, if in development
    app.debug = True # debug mnode

# make one persistent connection to the database
connection = pymongo.MongoClient(config['MONGO_HOST'], 27017, 
                                username=config['MONGO_USER'],
                                password=config['MONGO_PASSWORD'],
                                authSource=config['MONGO_DBNAME'])
db = connection[config['MONGO_DBNAME']] # store a reference to the database


# set up the routes
@app.route('/')
def index():
    if 'username' in session:
        #try route this to the home page, since the session is already active
        return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/login', methods = ['POST'])
def login():
    #removing the user from the session and adding them back when they sign in
    session.pop('username', None)
    users = db.users
    login_user = users.find_one({'name':request.form['username']})
    #checking if the username is valid
    if login_user:
       #checking if th password is correct
        if login_user['password'] == request.form['pass']:
            #adding the user to the new session
            session['username'] = request.form['username']
            
            #flash("You have been successfully logged in!!")
            return redirect(url_for('home'))
    
    
    #add an error signal but redirect back to the login page
    flash("Incorrect Username/Password!!")
    return redirect(url_for('index'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = db.users
        existing_user = users.find_one({'name': request.form['username']})
        #checking if the user exists
        if existing_user == None:
            #saving the username and pass in the database
            users.insert({'name':request.form['username'], 'password': request.form['pass']})
            #creating a session for the user
            session['username'] = request.form['username']
            #need to edit this to redirect to the home page
            return redirect(url_for('home'))

        #add error sign and redirect back to login
        flash('That username already exists!')   
    return render_template('register.html')

@app.route('/signout')
def signOut():
    #removing the user from the session
    session.pop('username', None)
    flash('You have been logged out', 'info')
    #redirecting the user back to the login page
    return redirect(url_for('index'))

def isLoggedIn():
    #cheking if the user is logged in
    if 'username' in session:
        return True
    return False

#update home !!!!!
@app.route('/home')
def home():
    """
    Route for the home page
    """
    #check if username is logged in
    if isLoggedIn():
        #if logged in then take it to the page
        return render_template('read.html')

    #if not, then redirect to login page
    return redirect(url_for('index'))


@app.route('/read')
def read():
    """
    Route for GET requests to the read page.
    Displays some information for the user with links to other pages.
    """
    if isLoggedIn():
        docs = db.exampleapp.find({}).sort("created_at", -1) # sort in descending order of created_at timestamp
        return render_template('read.html', docs=docs) # render the read template
    return redirect(url_for('index'))

@app.route('/create')
def create():
    """
    Route for GET requests to the create page.
    Displays a form users can fill out to create a new document.
    """
    if isLoggedIn():
        return render_template('create.html') # render the create template
    return redirect(url_for('index'))

@app.route('/create', methods=['POST'])
def create_post():
    """
    Route for POST requests to the create page.
    Accepts the form submission data for a new document and saves the document to the database.
    """
    if not isLoggedIn():
        return redirect(url_for('index'))

    date_of_incident = request.form['fdate']
    time_of_incident = request.form['ftime']
    name = request.form['fname']
    address = request.form['faddress']
    phone_number = request.form['fnumber']
    date_of_birth = request.form['fDOB']
    gender = request.form['fgender']
    type_of_injury = request.form['finjuryType']
    details_of_injury = request.form['finjuryDetails']


    # create a new document with the data the user entered
    doc = {
        "date_of_incident": date_of_incident,
        "time_of_incident": time_of_incident,
        "name": name,
        "address": address,
        "phone_number":phone_number,
        "date_of_birth":date_of_birth,
        "gender":gender,
        "type_of_injury":type_of_injury,
        "details_of_injury": details_of_injury, 
        "created_at": datetime.datetime.utcnow()
    }
    db.exampleapp.insert_one(doc) # insert a new document

    return redirect(url_for('read')) # tell the browser to make a request for the /read route


@app.route('/edit/<mongoid>')
def edit(mongoid):
    """
    Route for GET requests to the edit page.
    Displays a form users can fill out to edit an existing record.
    """
    if not isLoggedIn():
        return redirect(url_for('index'))
    doc = db.exampleapp.find_one({"_id": ObjectId(mongoid)})
    return render_template('edit.html', mongoid=mongoid, doc=doc) # render the edit template


@app.route('/edit/<mongoid>', methods=['POST'])
def edit_post(mongoid):
    """
    Route for POST requests to the edit page.
    Accepts the form submission data for the specified document and updates the document in the database.
    """
    if not isLoggedIn():
        return redirect(url_for('index'))
    date_of_incident = request.form['fdate']
    time_of_incident = request.form['ftime']
    name = request.form['fname']
    address = request.form['faddress']
    phone_number = request.form['fnumber']
    date_of_birth = request.form['fDOB']
    gender = request.form['fgender']
    type_of_injury = request.form['finjuryType']
    details_of_injury = request.form['finjuryDetails']

    doc = {
        "date_of_incident": date_of_incident,
        "time_of_incident": time_of_incident,
        "name": name,
        "adress": address,
        "phone_number":phone_number,
        "date_of_birth":date_of_birth,
        "gender":gender,
        "type_of_injury":type_of_injury,
        "details_of_injury": details_of_injury, 
        "created_at": datetime.datetime.utcnow()
    }

    db.exampleapp.update_one(
        {"_id": ObjectId(mongoid)}, # match criteria
        { "$set": doc }
    )

    return redirect(url_for('read')) # tell the browser to make a request for the /read route


@app.route('/delete/<mongoid>')
def delete(mongoid):
    """
    Route for GET requests to the delete page.
    Deletes the specified record from the database, and then redirects the browser to the read page.
    """
    if not isLoggedIn():
        return redirect(url_for('index'))

    db.exampleapp.delete_one({"_id": ObjectId(mongoid)})
    return redirect(url_for('read')) # tell the web browser to make a request for the /read route.

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    GitHub can be configured such that each time a push is made to a repository, GitHub will make a request to a particular web URL... this is called a webhook.
    This function is set up such that if the /webhook route is requested, Python will execute a git pull command from the command line to update this app's codebase.
    You will need to configure your own repository to have a webhook that requests this route in GitHub's settings.
    Note that this webhook does do any verification that the request is coming from GitHub... this should be added in a production environment.
    """
    # run a git pull command
    process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE)
    pull_output = process.communicate()[0]
    # pull_output = str(pull_output).strip() # remove whitespace
    process = subprocess.Popen(["chmod", "a+x", "flask.cgi"], stdout=subprocess.PIPE)
    chmod_output = process.communicate()[0]
    # send a success response
    response = make_response('output: {}'.format(pull_output), 200)
    response.mimetype = "text/plain"
    return response

@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template('error.html', error=e) # render the edit template


if __name__ == "__main__":
    #import logging
    #logging.basicConfig(filename='/home/ak8257/error.log',level=logging.DEBUG)
    app.run(debug = True, port= 8080)
