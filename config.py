import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ak-easy-pathshala-secret-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'ak_pathshala.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SOCIAL_FACEBOOK = os.environ.get('SOCIAL_FACEBOOK') or 'https://facebook.com/akeasypathshala'
    SOCIAL_INSTAGRAM = os.environ.get('SOCIAL_INSTAGRAM') or 'https://instagram.com/akeasypathshala'
    SOCIAL_TWITTER = os.environ.get('SOCIAL_TWITTER') or 'https://twitter.com/akeasypathshala'
    SITE_EMAIL = os.environ.get('SITE_EMAIL') or 'info@akeasypathshala.com'
    SITE_PHONE = os.environ.get('SITE_PHONE') or '+977-1-6631838'
