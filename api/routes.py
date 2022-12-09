from flask import request, jsonify, Blueprint, session
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_bcrypt import Bcrypt
from flask_session import Session
from api.models import Dislikes, Users, db, Likes, Admins, Models
import boto3
import os
import json
from datetime import datetime

api = Blueprint("api", __name__)

bcrypt = Bcrypt()
server_session = Session()


@api.route("/hello", methods=["GET"])
def hello():
    return "Hello World!", 200

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


@api.route("/@me", methods=["GET"])
def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = Users.query.filter_by(id=user_id).first()
    return format_user(user)


@api.route("/login", methods=["POST"])
def login():
    email = request.json["email"]
    password = request.json["password"]

    user = Users.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Unauthorized"}), 401

    session["user_id"] = user.id
    return format_user(user)


@api.route("/login-admin", methods=["POST"])
def login_admin():
    email = request.json["email"]
    password = request.json["password"]

    admin = Admins.query.filter_by(email=email).first()

    if admin is None:
        return jsonify({"error": "Unauthorized"}), 401

    if not bcrypt.check_password_hash(admin.password, password):
        return jsonify({"error": "Unauthorized"}), 401

    session["user_id"] = admin.id
    return {
        "id": admin.id,
        "email": admin.email,
        "password": admin.password,
        "username": admin.username,
    }


@api.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return "200"


@api.route("/register", methods=["POST"])
def register():
    username = request.json["username"]
    email = request.json["email"]
    password = request.json["password"]
    gender = request.json["gender"]
    preference = request.json["preference"]

    user_exist = Users.query.filter_by(email=email).first() is not None

    if user_exist:
        return jsonify({"error": "User already exist"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = Users(username, email, hashed_password, gender, preference)
    db.session.add(new_user)
    db.session.commit()

    session["user_id"] = new_user.id

    return format_user(new_user)


@api.route("/user/<user_id>", methods=["GET"])
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

    result = list(db.session.execute(query, {"user_id": user_id}))
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
        "user_queue_id": id,
        "username": username,
        "gender": gender,
        "pictures": pictures,
    }


@api.route("/queue/<user_id>", methods=["GET"])
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

    result = list(db.session.execute(query, {"user_id": user_id}))
    user_id = result[0][0]
    username = result[0][1]
    gender = result[0][2]
    pictures = result[0][3]
    return format_queue(user_id, username, gender, pictures)

# Recomendation


def format_recommendation(id, username, gender, likeability, rank, pictures):
    return {
        "user_queue_id": id,
        "username": username,
        "gender": gender,
        "pictures": pictures,
        "likeability": likeability,
        "rank": rank,
    }


@api.route("/recommendation/<user_id>", methods=["GET"])
def recommendation(user_id):
    query = """
      SELECT u.id
        , username
        , gender
		    , r.accuracy as likeability
		    , RANK() OVER (ORDER BY r.accuracy desc)
        , ARRAY_AGG(i.url ORDER BY  i.url)
      FROM users u
      INNER JOIN recommendation r on r.user_evaluated_id = u.id
      INNER JOIN images i on i.user_id = u.id
      WHERE r.user_id = :user_id 
      GROUP BY 1,2,3,4"""

    result = list(db.session.execute(query, {"user_id": user_id}))
    recommended_users = []
    for user in result:
        user_id = user[0]
        username = user[1]
        gender = user[2]
        likeability = user[3]
        rank = user[4]
        pictures = user[5]
        formated_user = format_recommendation(
            user_id, username, gender, likeability, rank, pictures)
        recommended_users.append(formated_user)
    return recommended_users

# Create Likes


def format_like(like):
    return {
        "created_at": like.created_at,
        "user_id": like.user_id,
        "user_liked_id": like.user_liked_id,
    }


@api.route("/like", methods=["POST"])
def create_like():
    user_id = request.json["user_id"]
    user_liked_id = request.json["user_liked_id"]
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


@api.route("/delete_info/<user_id>", methods=["DELETE"])
def delete_all(user_id):
    likes = Likes.query.filter_by(user_id=user_id).delete()
    dislikes = Dislikes.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return f"Reactions deleted: {likes} likes and {dislikes} dislikes"


@api.route("/dislike", methods=["POST"])
def create_dislike():
    user_id = request.json["user_id"]
    user_disliked_id = request.json["user_disliked_id"]
    dislike = Dislikes(user_id, user_disliked_id)
    db.session.add(dislike)
    db.session.commit()
    return format_dislike(dislike)


def format_summary(total_likes, total_dislikes, accuracy, loss, performance):
    performance_upper_threshold = 0.9
    performance_lower_threshold = 0.8
    accuracy_upper_threshold = 0.9
    accuracy_lower_threshold = 0.8
    loss_threshold_upper_threshold = 0.3
    loss_threshold_lower_threshold = 0.2
    data_evaluation = ""
    training_evaluation = ""
    performance_evaluation = ""
    overall_evaluation = ""
    data_balance_upper_threshold = 0.2
    data_balance_lower_threshold = 0.01

    total_images = total_likes + total_dislikes

    if total_likes/total_images <= data_balance_lower_threshold or total_dislikes/total_images <= data_balance_lower_threshold:
        data_evaluation = "failed"
    elif total_likes/total_images < data_balance_upper_threshold or total_dislikes/total_images <= data_balance_upper_threshold:
        data_evaluation = "warning"
    else:
        data_evaluation = "approved"

    if performance >= performance_upper_threshold:
        performance_evaluation = "approved"
    elif performance < performance_upper_threshold and performance >= performance_lower_threshold:
        performance_evaluation = "warning"
    else:
        performance_evaluation = "failed"

    if (accuracy >= accuracy_upper_threshold and loss <= loss_threshold_upper_threshold) or (accuracy >= accuracy_lower_threshold and loss <= loss_threshold_lower_threshold):
        training_evaluation = "approved"
    elif (accuracy >= accuracy_lower_threshold and loss <= loss_threshold_upper_threshold):
        training_evaluation = "warning"
    else:
        training_evaluation = "failed"

    if training_evaluation == "failed" or performance_evaluation == "failed":
        overall_evaluation = "failed"
    elif training_evaluation == "warning" or performance_evaluation == "warning":
        overall_evaluation = "warning"
    else:
        overall_evaluation = "approved"

    return {
        "data": data_evaluation,
        "training": training_evaluation,
        "performance": performance_evaluation,
        "overall": overall_evaluation
    }


@api.route("/summary/<user_id>", methods=["GET"])
def trained(user_id):
    query = """
      SELECT 	COUNT(i.id) as total_images
      FROM likes l
      LEFT JOIN users u on l.user_liked_id = u.id
      INNER JOIN images i on i.user_id = u.id
      WHERE l.user_id = :user_id
      UNION
      SELECT COUNT(i.id) as total_images
      FROM dislikes d
      LEFT JOIN users u on d.user_disliked_id = u.id
      INNER JOIN images i on i.user_id = u.id
      WHERE d.user_id = :user_id"""
    result = list(db.session.execute(query, {"user_id": user_id}))
    total_likes_images = result[0][0]
    total_dislikes_images = result[1][0]
    # approximate value after enhancement
    if total_likes_images < 140:
        total_likes_images = 140
    if total_dislikes_images < 140:
        total_dislikes_images = 140

    bucket_data = "sagemaker-us-east-1-495878410334"
    s3 = boto3.resource("s3", aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
                        )
    bucket = s3.Bucket(bucket_data)
    filename_prefix = "data/" + user_id
    for file in bucket.objects.filter(Prefix=filename_prefix):
        file_name = file.key
        if file_name is not None:
            obj = s3.Object(bucket_data, file_name)
            data = obj.get()["Body"].read()
            data_json = json.loads(data)
    loss_len = len(data_json["data_loss"])
    acc_len = len(data_json["data_accuracy"])
    loss_data = data_json["data_loss"][loss_len-10:loss_len]
    acc_data = data_json["data_accuracy"][acc_len-10:acc_len]
    loss = sum(d["loss"] for d in loss_data) / len(loss_data)
    accuracy = sum(d["accuracy"] for d in acc_data) / len(acc_data)
    performance = data_json["performance_data"]["f1_score"]
    return format_summary(total_likes_images, total_dislikes_images, accuracy, loss, performance)


@api.route("/performance/<user_id>", methods=["GET"])
def performance(user_id):
    bucket_data = "sagemaker-us-east-1-495878410334"
    s3 = boto3.resource("s3", aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
                        )
    bucket = s3.Bucket(bucket_data)
    filename_prefix = "data/" + user_id
    for file in bucket.objects.filter(Prefix=filename_prefix):
        file_name = file.key
        if file_name is not None:
            obj = s3.Object(bucket_data, file_name)
            data = obj.get()["Body"].read()
    return data


@api.route("/model", methods=["POST"])
def create_model():
    user_requested_id = request.json["user_requested_id"]
    status = request.json["status"]
    model = Models(user_requested_id, status)
    db.session.add(model)
    db.session.commit()
    return {
        "created_at": model.created_at,
        "user_id": model.user_requested_id,
        "status": model.status,
    }


@api.route("/update_model/<admin_evaluated_id>", methods=["POST"])
def update_model(admin_evaluated_id):
    status = request.json["status"]
    model_id = request.json["model_id"]

    model = Models.query.filter_by(id=model_id).first()
    model.status = status
    model.admin_evaluated_id = admin_evaluated_id
    model.updated_at = datetime.utcnow()
    db.session.commit()
    return {
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "user_requested_id": model.user_requested_id,
        "admin_evaluated_id": model.admin_evaluated_id,
        "status": model.status,
    }


def format_model_user(model_id, user_requested_id, username, gender, preference, status, created_at):
    if status == "pending":
        status = "Esperando treinamento"
        duration = datetime.utcnow() - created_at
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours == 0:
            waiting_time = str(int(minutes)) + " min"
        else:
            waiting_time = str(int(hours)) + "h e " + \
                str(int(minutes)) + " min"
    elif status == "failed":
        status = "Falhou"
        waiting_time = "-"
    elif status == "approved":
        status = "Aprovado"
        waiting_time = "-"

    return {
        "model_id": model_id,
        "user_requested_id": user_requested_id,
        "username": username,
        "gender": gender,
        "preference": preference,
        "status": status,
        "waiting_time": waiting_time,
    }


@api.route("/get_models", methods=["GET"])
def get_models():
    query = """
      SELECT m.id
            , u.id
            , u.username
	          , u.gender
	          , u.preference
	          , m.status
	          , m.created_at
	          , CASE WHEN m.status = 'pending' THEN 1
	          	   WHEN m.status = 'failed' THEN 2
	          	   WHEN m.status = 'approved' THEN 3
	          	   ELSE 4
	          END as order_type
      FROM models as m
      LEFT JOIN users u on u.id = m.user_requested_id
      ORDER BY 8,7"""

    result = list(db.session.execute(query))
    models_users = []
    for user in result:
        model_id = user[0]
        user_requested_id = user[1]
        username = user[2]
        gender = user[3]
        preference = user[4]
        status = user[5]
        created_at = user[6]
        formated_user = format_model_user(
            model_id, user_requested_id, username, gender, preference, status, created_at)
        models_users.append(formated_user)
    return models_users


@api.route("/model_ready/<user_requested_id>", methods=["GET"])
def model_ready(user_requested_id):
    query = """
      SELECT *
      FROM models as m
      WHERE user_requested_id = :user_requested_id and status != 'pending'
      ORDER BY created_at desc
      LIMIT 1"""

    result = list(db.session.execute(
        query, {"user_requested_id": user_requested_id}))
    if len(result) == 0:
        status = "pending"
    else:
        user_requested_id = result[0][1]
        status = result[0][3]
    return {
        "user_requested_id": user_requested_id,
        "status": status,
    }
