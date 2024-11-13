from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, text
import os, secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Update the DATABASE_URI to point to the new database
DATABASE_URI = os.getenv('USER_DATABASE_URI', 'sqlite:///user_data.db')
engine = create_engine(DATABASE_URI)
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS users"))
    conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)"))
    conn.execute(text("INSERT OR IGNORE INTO users (username, password_hash) VALUES ('example_user', 'example_password')"))

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
        
        if result and result['password_hash'] == password:
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
