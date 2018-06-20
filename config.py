# Define the application directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Enable the development environment
DEBUG = True

# Define the database
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = True
