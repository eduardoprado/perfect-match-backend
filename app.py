import os
from flask import Flask, jsonify
from flask_cors import CORS
from api.config import ApplicationConfig
from api.utils import APIException
from api.models import db
from api.routes import bcrypt, server_session

ENV = os.getenv("FLASK_ENV")
app = Flask(__name__)
app.config.from_object(ApplicationConfig)

from api.routes import api

db.init_app(app)
bcrypt.init_app(app)
server_session.init_app(app)
CORS(app, supports_credentials=True)

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