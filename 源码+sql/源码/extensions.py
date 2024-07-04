from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def register_extension(app):
    db.init_app(app)