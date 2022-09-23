import sqlite3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)

@app.route('/')
def hello():
    return 'ajskdbnfkajdfb!'

if __name__ == 'main':
    app.run()