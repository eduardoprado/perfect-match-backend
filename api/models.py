from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Users (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.Text())
    gender = db.Column(db.String(100), nullable=False)
    preference = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"Users: {self.username}"

    def __init__(self, username, email, password, gender, preference):
        self.username = username
        self.email = email
        self.password = password
        self.gender = gender
        self.preference = preference

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Admins (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.Text())
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password


class Images (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    url = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)


class Models (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_requested_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    admin_evaluated_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    url = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)


class Likes (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_liked_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)

    def __init__(self, user_id, user_liked_id):
        self.user_id = user_id
        self.user_liked_id = user_liked_id


class Dislikes (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_disliked_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)

    def __init__(self, user_id, user_disliked_id):
        self.user_id = user_id
        self.user_disliked_id = user_disliked_id


class Recommendation (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_evaluated_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    accuracy = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)

    def __init__(self, user_id, user_evaluated_id, accuracy):
        self.user_id = user_id
        self.user_evaluated_id = user_evaluated_id
        self.accuracy = accuracy
