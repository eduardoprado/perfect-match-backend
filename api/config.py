import os
import redis

class ApplicationConfig:
  SECRET_KEY = os.environ.get('SECRET_KEY')
  JWT_SECRET_KEY = os.environ.get('JWT_SECRET')
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
  SESSION_TYPE = 'redis'
  SESSION_PERMANENT = False
  SESSION_USE_SIGNER = True
  SESSION_REDIS = redis.from_url(os.environ['REDIS_URL'])
