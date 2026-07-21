import os
from dotenv import load_dotenv

# Load .env before importing config
load_dotenv()

from flask import Flask
from config import config_by_name
from extensions import db, login_manager, migrate, csrf, mail, limiter, oauth
from models import User


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    try:
        return User.query.get(int(user_id))
    except (TypeError, ValueError):
        return None


def create_app(config_name=None):
    app = Flask(__name__)

    config_name = config_name or os.getenv(
        "FLASK_CONFIG",
        "development"
    )
    print("SECRET_KEY from env:", os.getenv("SECRET_KEY"))

    app.config.from_object(config_by_name[config_name])
    print("App root:", app.root_path)
    print("Database URI:", app.config["SQLALCHEMY_DATABASE_URI"])

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY environment variable is required."
        )

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    #csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    oauth.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    with app.app_context():

        from routes.auth import auth_bp
        from routes.auth_oauth import oauth_bp
        from routes.items import item_bp
        from routes.dashboard import dashboard_bp
        from routes.main import main_bp

        from services.oauth_service import register_oauth_clients

        register_oauth_clients(app)

        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(oauth_bp)
        app.register_blueprint(item_bp)
        app.register_blueprint(dashboard_bp)

        # Create tables automatically
        db.create_all()

    return app

app = create_app()
application = app

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=app.config.get('DEBUG', False))
