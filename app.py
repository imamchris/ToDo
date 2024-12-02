from sqlalchemy import create_engine, text  # Python, SQLAlchemy for database interaction
from werkzeug.security import generate_password_hash, check_password_hash  # Python, Werkzeug for password hashing
from flask import Flask, render_template, request, redirect, url_for, flash, session  # Python, Flask for web framework
from datetime import datetime  # Python, datetime for date handling
import os, secrets  # Python, os and secrets for environment variables and security

app = Flask(__name__)  # Flask application instance
app.secret_key = secrets.token_hex(16)  # Flask, secret key for session management

# Update the DATABASE_URI to point to the new database
DATABASE_URI = os.getenv('USER_DATABASE_URI', 'sqlite:///user_data.db')  # Python, environment variable for database URI
engine = create_engine(DATABASE_URI)  # SQLAlchemy, create database engine

# Initialize the database
with engine.connect() as conn:  # SQLAlchemy, connect to the database
    conn.execute(text("DROP TABLE IF EXISTS users"))  # SQL, drop users table if exists
    conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)"))  # SQL, create users table
    conn.execute(text("INSERT OR IGNORE INTO users (username, password_hash) VALUES ('testuser', :password_hash)"), {'password_hash': generate_password_hash('testpassword')})  # SQL, insert test user
    conn.execute(text("DROP TABLE IF EXISTS todos"))  # SQL, drop todos table if exists
    conn.execute(text("CREATE TABLE todos (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, description TEXT, completed BOOLEAN, due_date TEXT, category TEXT, FOREIGN KEY(user_id) REFERENCES users(id))"))  # SQL, create todos table
    conn.commit()  # SQLAlchemy, commit the transaction

# Home route
@app.route('/')  # Flask, route for home page
def home():
    return render_template('index.html')  # Flask, render HTML template

# Login route
@app.route('/login', methods=['GET', 'POST'])  # Flask, route for login page
def login():
    if request.method == 'POST':  # Flask, handle POST request
        username = request.form['username']  # Flask, get username from form
        password = request.form['password']  # Flask, get password from form
        with engine.connect() as conn:  # SQLAlchemy, connect to the database
            user = conn.execute(text("SELECT * FROM users WHERE username = :username"), {'username': username}).fetchone()  # SQL, select user by username
            if user and check_password_hash(user.password_hash, password):  # Python, check password hash
                session['user_id'] = user.id  # Flask, set user ID in session
                session['username'] = user.username  # Flask, set username in session
                flash('Login successful!', 'success')  # Flask, flash success message
                return redirect(url_for('dashboard'))  # Flask, redirect to dashboard
            else:
                flash('Invalid username or password', 'danger')  # Flask, flash error message
    return render_template('login.html')  # Flask, render HTML template

# Signup route
@app.route('/signup', methods=['GET', 'POST'])  # Flask, route for signup page
def signup():
    if request.method == 'POST':  # Flask, handle POST request
        username = request.form['username']  # Flask, get username from form
        password = request.form['password']  # Flask, get password from form
        password_hash = generate_password_hash(password)  # Python, generate password hash
        try:
            with engine.connect() as conn:  # SQLAlchemy, connect to the database
                conn.execute(text("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)"), {'username': username, 'password_hash': password_hash})  # SQL, insert new user
                conn.commit()  # SQLAlchemy, commit the transaction
            flash('Signup successful! Please login.', 'success')  # Flask, flash success message
            return redirect(url_for('login'))  # Flask, redirect to login page
        except Exception as e:
            flash('Username already exists. Please choose a different one.', 'danger')  # Flask, flash error message
    return render_template('signup.html')  # Flask, render HTML template

# Dashboard route
@app.route('/dashboard')  # Flask, route for dashboard page
def dashboard():
    if 'user_id' not in session:  # Flask, check if user is logged in
        flash('You need to login first', 'warning')  # Flask, flash warning message
        return redirect(url_for('login'))  # Flask, redirect to login page
    
    sort_by = request.args.get('sort_by', 'due_date_asc')  # Flask, get sort_by parameter from URL
    filter_by_category = request.args.get('filter_by_category', 'all')  # Flask, get filter_by_category parameter from URL
    sort_options = {
        'due_date_asc': 'due_date ASC',
        'due_date_desc': 'due_date DESC',
        'name_asc': 'name ASC',
        'name_desc': 'name DESC',
        'completed': 'completed ASC'
    }
    sort_query = sort_options.get(sort_by, 'due_date ASC')  # Python, get sort query
    
    with engine.connect() as conn:  # SQLAlchemy, connect to the database
        if filter_by_category == 'all':
            todos = conn.execute(text(f"SELECT * FROM todos WHERE user_id = :user_id ORDER BY {sort_query}"), {'user_id': session['user_id']}).fetchall()  # SQL, select todos by user ID and sort
        else:
            todos = conn.execute(text(f"SELECT * FROM todos WHERE user_id = :user_id AND category = :category ORDER BY {sort_query}"), {'user_id': session['user_id'], 'category': filter_by_category}).fetchall()  # SQL, select todos by user ID, category, and sort
    
    # Convert due_date from string to datetime.date
    todos = [
        {
            **todo._asdict(),
            'due_date': datetime.strptime(todo.due_date, '%Y-%m-%d').date() if todo.due_date else None
        }
        for todo in todos
    ]
    
    current_date = datetime.now().date()  # Python, get current date
    return render_template('dashboard.html', todos=todos, user_id=session['user_id'], username=session['username'], current_date=current_date, sort_by=sort_by, filter_by_category=filter_by_category)  # Flask, render HTML template

# Add ToDo route
@app.route('/add_todo', methods=['POST'])  # Flask, route for adding a new ToDo
def add_todo():
    if 'user_id' not in session:  # Flask, check if user is logged in
        flash('You need to login first', 'warning')  # Flask, flash warning message
        return redirect(url_for('login'))  # Flask, redirect to login page

    name = request.form.get('name')  # Flask, get name from form
    description = request.form.get('description', '')  # Flask, get description from form, default to empty string
    due_date = request.form.get('due_date')  # Flask, get due date from form
    category = request.form.get('category', 'General')  # Flask, get category from form, default to General

    if not name or not due_date:  # Python, check if name and due date are provided
        flash('Name and due date are required!', 'danger')  # Flask, flash error message
        return redirect(url_for('dashboard'))  # Flask, redirect to dashboard

    with engine.connect() as conn:  # SQLAlchemy, connect to the database
        conn.execute(text("INSERT INTO todos (user_id, name, description, completed, due_date, category) VALUES (:user_id, :name, :description, :completed, :due_date, :category)"), 
                     {'user_id': session['user_id'], 'name': name, 'description': description, 'completed': False, 'due_date': due_date, 'category': category})  # SQL, insert new ToDo
        conn.commit()  # SQLAlchemy, commit the transaction

    flash('Todo item added!', 'success')  # Flask, flash success message
    return redirect(url_for('dashboard'))  # Flask, redirect to dashboard

# Edit ToDo route
@app.route('/edit_todo/<int:todo_id>', methods=['GET', 'POST'])  # Flask, route for editing a ToDo
def edit_todo(todo_id):
    if 'user_id' not in session:  # Flask, check if user is logged in
        flash('You need to login first', 'warning')  # Flask, flash warning message
        return redirect(url_for('login'))  # Flask, redirect to login page
    
    with engine.connect() as conn:  # SQLAlchemy, connect to the database
        todo = conn.execute(text("SELECT * FROM todos WHERE id = :id AND user_id = :user_id"), {'id': todo_id, 'user_id': session['user_id']}).fetchone()  # SQL, select ToDo by ID and user ID
    
    if request.method == 'POST':  # Flask, handle POST request
        name = request.form.get('name') or todo.name  # Flask, get name from form or use existing name
        description = request.form.get('description') or todo.description  # Flask, get description from form or use existing description
        due_date = request.form.get('due_date') or todo.due_date  # Flask, get due date from form or use existing due date
        category = request.form.get('category') or todo.category  # Flask, get category from form or use existing category
        
        with engine.begin() as conn:  # SQLAlchemy, begin a transaction
            conn.execute(text("UPDATE todos SET name = :name, description = :description, due_date = :due_date, category = :category WHERE id = :id AND user_id = :user_id"), 
                            {'name': name, 'description': description, 'due_date': due_date, 'category': category, 'id': todo_id, 'user_id': session['user_id']})  # SQL, update ToDo
            conn.commit()  # SQLAlchemy, commit the transaction
        
        flash('Todo item updated!', 'success')  # Flask, flash success message
        return redirect(url_for('dashboard'))  # Flask, redirect to dashboard
    
    return render_template('edit_todo.html', todo=todo)  # Flask, render HTML template

# Complete ToDo route
@app.route('/complete_todo/<int:todo_id>', methods=['POST'])  # Flask, route for completing a ToDo
def complete_todo(todo_id):
    if 'user_id' not in session:  # Flask, check if user is logged in
        flash('You need to login first', 'warning')  # Flask, flash warning message
        return redirect(url_for('login'))  # Flask, redirect to login page
    
    with engine.connect() as conn:  # SQLAlchemy, connect to the database
        todo = conn.execute(text("SELECT completed FROM todos WHERE id = :id AND user_id = :user_id"), {'id': todo_id, 'user_id': session['user_id']}).fetchone()  # SQL, select ToDo by ID and user ID
        if todo:
            new_status = not todo.completed  # Python, toggle completion status
            conn.execute(text("UPDATE todos SET completed = :completed WHERE id = :id AND user_id = :user_id"), {'completed': new_status, 'id': todo_id, 'user_id': session['user_id']})  # SQL, update completion status
            conn.commit()  # SQLAlchemy, commit the transaction
            flash('Todo item completion status updated!', 'success')  # Flask, flash success message
        else:
            flash('Todo item not found', 'danger')  # Flask, flash error message
    
    return redirect(url_for('dashboard'))  # Flask, redirect to dashboard

# Delete ToDo route
@app.route('/delete_todo/<int:todo_id>', methods=['POST'])  # Flask, route for deleting a ToDo
def delete_todo(todo_id):
    if 'user_id' not in session:  # Flask, check if user is logged in
        flash('You need to login first', 'warning')  # Flask, flash warning message
        return redirect(url_for('login'))  # Flask, redirect to login page
    
    with engine.connect() as conn:  # SQLAlchemy, connect to the database
        conn.execute(text("DELETE FROM todos WHERE id = :id AND user_id = :user_id"), {'id': todo_id, 'user_id': session['user_id']})  # SQL, delete ToDo by ID and user ID
        conn.commit()  # SQLAlchemy, commit the transaction
    
    flash('Todo item deleted!', 'success')  # Flask, flash success message
    return redirect(url_for('dashboard'))  # Flask, redirect to dashboard

# Logout route
@app.route('/logout')  # Flask, route for logging out
def logout():
    session.clear()  # Flask, clear session
    flash('You have been logged out', 'success')  # Flask, flash success message
    return redirect(url_for('login'))  # Flask, redirect to login page

if __name__ == '__main__':
    app.run(debug=True)  # Flask, run the application in debug mode