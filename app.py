from email.policy import default
import sqlite3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime


host = 'perfect-match-database.cyf5ascpbcvs.us-east-1.rds.amazonaws.com'
database = 'perfect_match_db'
port = 5432
user = 'eduardo'
password = '%Helium_77'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://eduardo:%Helium_77@perfect-match-database.cyf5ascpbcvs.us-east-1.rds.amazonaws.com/perfect_match_db'
db = SQLAlchemy(app)

class User (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    gender = db.Column(db.String(100), nullable=False)
    preference = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"User: {self.username}"
    
    def __init__(self, username) -> None:
        self.username = username

@app.route('/')
def hello():
    return 'Hello!'

if __name__ == 'main':
    app.run()