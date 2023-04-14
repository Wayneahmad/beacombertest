from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import os

app = Flask(__name__)

# Set up the secret key and database configurations
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///questions.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set up the login manager and SQLAlchemy
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)

# Create the Staff model
class Staff(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(10), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

def init_db():
    # Connect to the database
    conn = sqlite3.connect('questions.db')

    # Create the questions table if it doesn't exist
    conn.execute('''CREATE TABLE IF NOT EXISTS questions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question TEXT NOT NULL,
                  option1 TEXT NOT NULL,
                  option2 TEXT NOT NULL,
                  option3 TEXT NOT NULL,
                  option4 TEXT NOT NULL,
                  answer INTEGER NOT NULL)''')

    # Check if the table is empty
    cursor = conn.execute('SELECT COUNT(*) FROM questions')
    count = cursor.fetchone()[0]

    # Add some sample questions to the database if the table is empty
    if count == 0:
        conn.execute('''INSERT INTO questions (question, option1, option2, option3, option4, answer)
                     VALUES
                     ('What is the capital of India?', 'Delhi', 'Mumbai', 'Chennai', 'Kolkata', 1),
                     ('Who is the first president of the USA?', 'George Washington', 'Thomas Jefferson', 'John Adams', 'James Madison', 1),
                     ('What glass is the Jungle babe made with?', 'Hurricane glass', 'Goblet glass', 'Balloon glass', 'Tall Glass', 1),
                     ('How much premix does the jungle babe require?', '65ml Premix', '125ml Premix', '55ml Premix', '75ml premix', 3),
                     ('What glass does a Mauis highland use??', 'Coupette', 'Ballon Glass', 'Skull glass', 'Zombie Glass', 2)''')
        conn.commit()

    conn.close()

# Define the route for the registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if Staff.query.filter_by(email=email).first():
            flash('Email already exists. Please log in or use a different email.')
            return redirect(url_for('register'))

        # Generate a unique staff ID
        staff_id = f'SID{Staff.query.count() + 1:05d}'

        new_user = Staff(email=email, password=password, staff_id=staff_id)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

# Define the route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']

        user = Staff.query.filter((Staff.email == identifier) | (Staff.staff_id == identifier)).first()

        if user and user.password == password:
            login_user(user)
            flash('Login successful.')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.')

    return render_template('login.html')

# Define the route for the logout functionality
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('home'))

# Define the route for the home page
@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('home.html')

# Define the route for the test page
@app.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    if request.method == 'POST':
        # Get the user's answers from the form
        answers = [int(request.form['q1']),
                   int(request.form['q2']),
                   int(request.form['q3']),
                   int(request.form['q4']),
                   int(request.form['q5'])]

        # Get the correct answers from the database
        conn = sqlite3.connect('questions.db')
        cursor = conn.execute('SELECT answer FROM questions')
        correct_answers = [row[0] for row in cursor]
        conn.close()

        # Calculate the user's score
        score = sum([1 for i in range(5) if answers[i] == correct_answers[i]])

        # Redirect to the results page
        return redirect(url_for('results', score=score))

    # If the request method is GET, show the test page
    conn = sqlite3.connect('questions.db')
    cursor = conn.execute('SELECT * FROM questions')
    questions = [row for row in cursor]
    conn.close()
    return render_template('test.html', questions=questions)


@login_manager.user_loader
def load_user(user_id):
    return Staff.query.get(int(user_id))


# Define the route for the results page
@app.route('/results')
@login_required
def results():
    score = request.args.get('score')
    return render_template('results.html', score=score)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the tables if they don't exist
    init_db()
    app.run()
