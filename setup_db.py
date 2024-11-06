from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

def hash_password(password):
    return generate_password_hash(password)

def setup_database():
    engine = create_engine('sqlite:///todo.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

class ToDo(Base):
    __tablename__ = 'todos'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

if __name__ == "__main__":
    session = setup_database()
    # Example usage
    existing_user = session.query(User).filter_by(username="example_user").first()
    if not existing_user:
        new_user = User(username="example_user", password_hash=hash_password("example_password"))
        session.add(new_user)
        session.commit()
    else:
        new_user = existing_user

    # Example usage
    new_todo = ToDo(title="Example Task", description="This is an example task", user_id=new_user.id)
    session.add(new_todo)
    session.commit()

    print("Database setup and example usage completed successfully.")