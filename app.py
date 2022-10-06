import os
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from api.utils import APIException
from api.models import db
from api.routes import api

ENV = os.getenv("FLASK_ENV")
app = Flask(__name__)
app.url_map.strict_slashes = False

# Setup database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET')
jwt = JWTManager(app)

db.init_app(app)
CORS(app)

with app.app_context():
    db.create_all()

# Add all endpoints
app.register_blueprint(api)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

if __name__ == 'main':
    app.run()