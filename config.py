import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    # Configuración de la base de datos
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Para Railway (PostgreSQL)
        SQLALCHEMY_DATABASE_URI = db_url.replace(
            'postgres://', 'postgresql://')
    else:
        # Para desarrollo local (SQLite)
        basedir = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + \
            os.path.join(basedir, 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
