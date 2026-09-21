import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-12345'

    # SQLite database
    INSTANCE_PATH = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(INSTANCE_PATH, exist_ok=True)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(INSTANCE_PATH, 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'static',
        'uploads'
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
