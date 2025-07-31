from flask import Flask, redirect, url_for
from app.extensions import db, login_manager
from app.models import User

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'aathi-vehicle-parking-123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.admin import admin_bp
    from app.routes.user import user_bp
    from app.routes.auth import auth_bp
    from app.errors import register_error_handlers

    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)

    register_error_handlers(app)

    with app.app_context():
        from app import models
        db.create_all()

    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    return app
