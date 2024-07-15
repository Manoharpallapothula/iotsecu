from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'mannu734'
SECRET_STRING = 'ManoharT1485'

# SQLite database configuration
DATABASE = 'users.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# MongoDB configuration
client = MongoClient('mongodb+srv://test:test@cluster0.wwz3l5h.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db_mongo = client['sensor']
collection = db_mongo['time_tem_hum']

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate username and password (similar to previous example)
        if not username or not password:
            error = "Both username and password are required."
            return render_template('login.html', error=error)
        
        if len(username) < 3:
            error = "Username must be at least 3 characters."
            return render_template('login.html', error=error)
        
        if len(password) < 6:
            error = "Password must be at least 6 characters."
            return render_template('login.html', error=error)
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = username
            return redirect(url_for('sensor_data'))
        else:
            error = 'Invalid username or password'  # Define error message
            return render_template('login.html', error=error)  # Pass error message to login.html

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Process registration form submission
        username = request.form['username']
        password = request.form['password']
        entered_string = request.form['secret_string']

        # Validate the entered secret string
        if entered_string != SECRET_STRING:
            error = "Invalid string. Please enter the correct registration string."
            return render_template('register.html', error=error)
        
        # Validate username and password (similar to previous example)
        if not username or not password:
            error = "Both username and password are required."
            return render_template('register.html', error=error)
        
        if len(username) < 3:
            error = "Username must be at least 3 characters."
            return render_template('register.html', error=error)
        
        if len(password) < 6:
            error = "Password must be at least 6 characters."
            return render_template('register.html', error=error)
        
        # Check for existing username (similar to previous example)
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            error = "Username already exists. Please choose a different username."
            return render_template('register.html', error=error)

        # Add user to the SQLite database (similar to previous example)
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        db.commit()

        # Redirect to login page after successful registration
        return redirect(url_for('home'))

    # Render registration form for GET requests
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return f'Welcome, {session["username"]}!'
    else:
        return redirect(url_for('home'))

@app.route('/sensor_data')
def sensor_data():
    # Fetch data from MongoDB
    data = collection.find()

    # Pass data to the template
    return render_template('index.html', data=data)

@app.route('/filter_aws')
def filter_aws():
    # Fetch data from MongoDB filtered by AWS
    data = collection.find({"Cloud": "AWS"})
    return render_template('aws.html', data=data)

@app.route('/filter_google')
def filter_google():
    # Fetch data from MongoDB filtered by Google
    data = collection.find({"Cloud": "Google"})
    return render_template('google.html', data=data)

@app.route('/filter_azure')
def filter_azure():
    # Fetch data from MongoDB filtered by Azure
    data = collection.find({"Cloud": "Azure"})
    return render_template('azure.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
