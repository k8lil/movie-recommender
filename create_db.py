import os
from app import app, db

print("Current working directory:", os.getcwd())

with app.app_context():
    db.create_all()
    print("Database created.")