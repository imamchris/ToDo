from sqlalchemy import create_engine, text
import os, secrets
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Update the DATABASE_URI to point to the new database
DATABASE_URI = os.getenv('USER_DATABASE_URI', 'sqlite:///user_data.db')
engine = create_engine(DATABASE_URI)

# Initialize the database
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS users"))
    conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)"))
    conn.execute(text("INSERT OR IGNORE INTO users (username, password_hash) VALUES ('testuser', :password_hash)"), {'password_hash': generate_password_hash('testpassword')})
    conn.commit()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM users WHERE username = :username"), {'username': username}).fetchone()
        
        if result and check_password_hash(result.password_hash, password):
            session['user_id'] = result.id
            session['username'] = result.username
            flash('Login successful!', 'success')
            flash('')  # Reset the flash text
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('You need to login first', 'warning')
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

# Uncomment and complete the registration route if needed
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM users WHERE username = :username"), {'username': username}).fetchone()
            
            if result:
                flash('Username already exists', 'danger')
            else:
                password_hash = generate_password_hash(password)
                conn.execute(text("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)"), {'username': username, 'password_hash': password_hash})
                conn.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
    
    return render_template('signup.html')

if __name__ == '__main__':
    app.run(debug=True)