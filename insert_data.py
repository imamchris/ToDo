from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# Database setup
DATABASE_URL = "sqlite:///test.db"  # Replace with your actual database URL
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Define a sample table
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    password = Column(String, nullable=False)

# Create the table
Base.metadata.create_all(engine)

# Create a new session
Session = sessionmaker(bind=engine)
session = Session()

# Insert test data with hashed password
hashed_password = generate_password_hash("password123")
new_user = User(password=hashed_password)
session.add(new_user)

# Commit the transaction
session.commit()

# Confirm the passing of the command
print("Data has been successfully inserted and committed.")
