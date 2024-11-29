from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import os, secrets

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
    conn.execute(text("DROP TABLE IF EXISTS todos"))
    conn.execute(text("CREATE TABLE todos (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, description TEXT, completed BOOLEAN, due_date TEXT, FOREIGN KEY(user_id) REFERENCES users(id))"))
    conn.commit()

# Home
@app.route('/')
def home():
    return render_template('index.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with engine.connect() as conn:
            user = conn.execute(text("SELECT * FROM users WHERE username = :username"), {'username': username}).fetchone()
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
    return render_template('login.html')

# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        try:
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)"), {'username': username, 'password_hash': password_hash})
                conn.commit()
            flash('Signup successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Username already exists. Please choose a different one.', 'danger')
    return render_template('signup.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('You need to login first', 'warning')
        return redirect(url_for('login'))
    
    with engine.connect() as conn:
        todos = conn.execute(text("SELECT * FROM todos WHERE user_id = :user_id"), {'user_id': session['user_id']}).fetchall()
    
    # Convert due_date from string to datetime.date
    todos = [
        {
            **todo._asdict(),
            'due_date': datetime.strptime(todo.due_date, '%Y-%m-%d').date() if todo.due_date else None
        }
        for todo in todos
    ]
    
    current_date = datetime.now().date()
    return render_template('dashboard.html', todos=todos, user_id=session['user_id'], username=session['username'], current_date=current_date)

# Add ToDo
@app.route('/add_todo', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        flash('You need to login first', 'warning')
        return redirect(url_for('login'))

    name = request.form.get('name')
    description = request.form.get('description', '')  # Get description from form, default to empty string
    due_date = request.form.get('due_date')  # Get due date from form

    if not name or not due_date:
        flash('Name and due date are required!', 'danger')
        return redirect(url_for('dashboard'))

    with engine.connect() as conn:
        conn.execute(text("INSERT INTO todos (user_id, name, description, completed, due_date) VALUES (:user_id, :name, :description, :completed, :due_date)"), 
                     {'user_id': session['user_id'], 'name': name, 'description': description, 'completed': False, 'due_date': due_date})
        conn.commit()

    flash('Todo item added!', 'success')
    return redirect(url_for('dashboard'))

# Edit ToDo
@app.route('/edit_todo/<int:todo_id>', methods=['GET', 'POST'])
def edit_todo(todo_id):
    if 'user_id' not in session:
        flash('You need to login first', 'warning')
        return redirect(url_for('login'))
    
    with engine.connect() as conn:
        todo = conn.execute(text("SELECT * FROM todos WHERE id = :id AND user_id = :user_id"), {'id': todo_id, 'user_id': session['user_id']}).fetchone()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        
        with engine.begin() as conn:
            conn.execute(text("UPDATE todos SET name = :name, description = :description, due_date = :due_date WHERE id = :id AND user_id = :user_id"), 
                            {'name': name, 'description': description, 'due_date': due_date, 'id': todo_id, 'user_id': session['user_id']})
            conn.commit()
        
        flash('Todo item updated!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_todo.html', todo=todo)

# Complete ToDo
@app.route('/complete_todo/<int:todo_id>', methods=['POST'])
def complete_todo(todo_id):
    if 'user_id' not in session:
        flash('You need to login first', 'warning')
        return redirect(url_for('login'))
    
    with engine.connect() as conn:
        todo = conn.execute(text("SELECT completed FROM todos WHERE id = :id AND user_id = :user_id"), {'id': todo_id, 'user_id': session['user_id']}).fetchone()
        if todo:
            new_status = not todo.completed
            conn.execute(text("UPDATE todos SET completed = :completed WHERE id = :id AND user_id = :user_id"), {'completed': new_status, 'id': todo_id, 'user_id': session['user_id']})
            conn.commit()
            flash('Todo item completion status updated!', 'success')
        else:
            flash('Todo item not found', 'danger')
    
    return redirect(url_for('dashboard'))

# Delete ToDo
@app.route('/delete_todo/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    if 'user_id' not in session:
        flash('You need to login first', 'warning')
        return redirect(url_for('login'))
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM todos WHERE id = :id AND user_id = :user_id"), {'id': todo_id, 'user_id': session['user_id']})
        conn.commit()
    
    flash('Todo item deleted!', 'success')
    return redirect(url_for('dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)