# query_db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from setup_db import Base, User, ToDo

# Create an engine and a session
engine = create_engine('sqlite:///example.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Example query: Get all users
users = session.query(User).all()
for user in users:
    print(f"User ID: {user.id}, Name: {user.name}")

# Example query: Get all todos
todos = session.query(ToDo).all()
for todo in todos:
    print(f"ToDo ID: {todo.id}, Description: {todo.description}, User ID: {todo.user_id}")

# Close the session
session.close()
print("Session closed successfully.")
