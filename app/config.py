import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///code_logs.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # ML Model paths
    MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'concept_classifier.pkl')
    TRAINING_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'training_data.csv')
