from flask import request, jsonify, Blueprint, session
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_bcrypt import Bcrypt
from flask_session import Session
from api.models import Dislikes, Users, db, Likes

api = Blueprint('api', __name__)

bcrypt = Bcrypt()
server_session = Session()

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

@api.route('/@me', methods=["GET"])
def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
      return jsonify({"error": "Unauthorized"}), 401 
    
    user = Users.query.filter_by(id=user_id).first()
    return format_user(user)


@api.route('/login', methods=["POST"])
def login():
    email = request.json['email']
    password = request.json['password']

    user = Users.query.filter_by(email=email).first()

    if user is None:
      return jsonify({"error": "Unauthorized"}), 401

    if not bcrypt.check_password_hash(user.password, password):
      return jsonify({"error": "Unauthorized"}), 401

    session["user_id"] = user.id
    return format_user(user)

@api.route('/logout', methods=["POST"])
def logout():
    session.clear()
    return '200'

@api.route('/register', methods=["POST"])
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    gender = request.json['gender']
    preference = request.json['preference']

    user_exist = Users.query.filter_by(email=email).first() is not None

    if user_exist:
      return jsonify({"error": "User already exist"}), 409
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = Users(username, email, hashed_password, gender, preference)
    db.session.add(new_user)
    db.session.commit()

    session["user_id"] = new_user.id

    return format_user(new_user)

@api.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    query = """
      SELECT u.username
	      , count(distinct l.id) as total_likes
	      , count(distinct d.id) as total_dislikes
	      , count(distinct i.id) as total_images
      FROM users u
      LEFT JOIN likes l on l.user_id = u.id
      LEFT JOIN dislikes d on d.user_id = u.id
      LEFT JOIN images i on i.user_id = l.user_liked_id or i.user_id = d.user_disliked_id
      WHERE u.id = :user_id
      GROUP BY 1"""

    result = list(db.session.execute(query, {"user_id":user_id}))
    username = result[0][0]
    total_likes = result[0][1]
    total_dislikes = result[0][2]
    total_images = result[0][3]
    total_people = total_likes + total_dislikes
    return {
      "username": username,
      "total_likes": total_likes,
      "total_dislikes": total_dislikes,
      "total_images": total_images,
      "total_people": total_people
    }

def format_queue(id, username, gender, pictures):
  return {
    'user_queue_id': id,
    'username': username,
    'gender': gender,
    'pictures': pictures,
  }

@api.route('/queue/<user_id>', methods=['GET'])
def queue(user_id):
    query = """
      SELECT u.id
        , username
        , gender
        , ARRAY_AGG(i.url ORDER BY  i.url)
      FROM users u
      LEFT JOIN likes l on l.user_liked_id = u.id
      LEFT JOIN dislikes d on d.user_disliked_id = u.id
      INNER JOIN images i on i.user_id = u.id
      WHERE l.user_id != :user_id or d.user_id != :user_id or l.id is null or d.id is null
      GROUP BY 1,2,3
      ORDER BY RANDOM()
      LIMIT 1"""

    result = list(db.session.execute(query, {"user_id":user_id}))
    user_id = result[0][0]
    username = result[0][1]
    gender = result[0][2]
    pictures = result[0][3]
    return format_queue(user_id, username, gender, pictures)

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

@api.route('/delete_info/<user_id>', methods=['DELETE'])
def delete_all(user_id):
    likes = Likes.query.filter_by(user_id=user_id).delete()
    dislikes = Dislikes.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return f'Reactions deleted: {likes} likes and {dislikes} dislikes'

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
