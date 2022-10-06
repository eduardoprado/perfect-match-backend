from flask import Flask, request, jsonify, Blueprint
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from api.models import Dislikes, Users, db, Likes

api = Blueprint('api', __name__)

@api.route('/hello', methods=['POST', 'GET'])
def handle_hello():

    response_body = {
        "message": "Hello! I'm a message that came from the backend, check the network tab on the google inspector and you will see the GET request"
    }

    return jsonify(response_body), 200

# Create a route to authenticate your users and return JWTs. The
# create_access_token() function is used to actually generate the JWT.
@api.route('/login', methods=["POST"])
def login():
    email = request.json['email']
    password = request.json['password']
    if email != "test" or password != "test":
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=email)
    return jsonify(access_token=access_token)

# Register user
def format_user(user):
  return {
    "created_at": user.created_at,
    "id": user.id,
    "email": user.email,
    "password": user.password,
    "username": user.username,
    "gender": user.gender,
    "preference": user.preference
  }

@api.route('/register', methods=["POST"])
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    gender = request.json['gender']
    preference = request.json['preference']
    user = Users(username, email, password, gender, preference)
    db.session.add(user)
    db.session.commit()
    return format_user(user)

def format_queue(username, gender, pictures):
  return {
    'username': username,
    'gender': gender,
    'pictures': pictures,
  }

@api.route('/queue/<user_id>', methods=['GET'])
def queue(user_id):
    query = """
      SELECT username
        , gender
        , ARRAY_AGG(i.url ORDER BY  i.url)
      FROM users u
      LEFT JOIN likes l on l.user_liked_id = u.id
      LEFT JOIN dislikes d on d.user_disliked_id = u.id
      INNER JOIN images i on i.user_id = u.id
      WHERE l.user_id != :user_id or d.user_id != :user_id or l.id is null or d.id is null
      GROUP BY 1,2
      ORDER BY RANDOM()
      LIMIT 1"""

    result = list(db.session.execute(query, {"user_id":user_id}))
    username = result[0][0]
    gender = result[0][1]
    pictures = result[0][2]
    return format_queue(username, gender, pictures)

# Create Likes
def format_like(like):
  return {
    "created_at": like.created_at,
    "user_id": like.user_id,
    "user_liked_id": like.user_liked_id,
  }

@api.route('/like', methods=['POST'])
def create_like():
    user_id = request.json['user_id']
    user_liked_id = request.json['user_liked_id']
    like = Likes(user_id, user_liked_id)
    db.session.add(like)
    db.session.commit()
    return format_like(like)

# Create Dislikes
def format_dislike(dislike):
  return {
    "created_at": dislike.created_at,
    "user_id": dislike.user_id,
    "user_disliked_id": dislike.user_disliked_id,
  }

@api.route('/dislike', methods=['POST'])
def create_dislike():
    user_id = request.json['user_id']
    user_disliked_id = request.json['user_disliked_id']
    dislike = Dislikes(user_id, user_disliked_id)
    db.session.add(dislike)
    db.session.commit()
    return format_dislike(dislike)
    

@api.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200
