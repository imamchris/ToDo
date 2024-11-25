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
    conn.execute(text("DROP TABLE IF EXISTS todos"))
    conn.execute(text("CREATE TABLE todos (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, description TEXT, completed BOOLEAN, FOREIGN KEY(user_id) REFERENCES users(id))"))
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
            result = conn.execute(text("SELECT * FROM users WHERE username = :username"), {'username': username}).fetchone()
        
        if result and check_password_hash(result.password_hash, password):
            session['user_id'] = result.id
            session['username'] = result.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')


# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('You need to login first', 'warning')
        return redirect(url_for('login'))
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM todos WHERE user_id = :user_id"), {'user_id': session['user_id']}).fetchall()
    
    todos = [{'id': row.id, 'name': row.name, 'description': row.description, 'completed': row.completed} for row in result]
    
    return render_template('dashboard.html', todos=todos, username=session['username'], user_id=session['user_id'])

@app.route('/add_todo', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        flash('You need to login first', 'warning')
        return redirect(url_for('login'))
    
    name = request.form.get('name')
    description = request.form.get('description')
    
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO todos (user_id, name, description, completed) VALUES (:user_id, :name, :description, :completed)"), 
                     {'user_id': session['user_id'], 'name': name, 'description': description, 'completed': False})
        conn.commit()
    
    flash('Todo item added!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/complete_todo/<int:todo_id>', methods=['POST'])
def complete_todo(todo_id):
    if 'user_id' not in session:
        flash('You need to login first', 'warning')
        return redirect(url_for('login'))
    
    with engine.connect() as conn:
        conn.execute(text("UPDATE todos SET completed = :completed WHERE id = :id AND user_id = :user_id"), 
                     {'completed': True, 'id': todo_id, 'user_id': session['user_id']})
    conn.commit()
    
    flash('Todo item marked as completed!', 'success')
    return redirect(url_for('dashboard'))

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
        
        with engine.connect() as conn:
            conn.execute(text("UPDATE todos SET name = :name, description = :description WHERE id = :id AND user_id = :user_id"), 
                            {'name': name, 'description': description, 'id': todo_id, 'user_id': session['user_id']})
            conn.commit()
        
        flash('Todo item updated!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_todo.html', todo=todo)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('_flashes', None)  # Clear flash messages
    session.clear()  # Clear all session data
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# Signup
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
