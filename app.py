import os
from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User
from routes import auth_bp, main_bp, student_bp, admin_bp, api_bp
from utils.helpers import get_category_icon, get_category_color

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Register custom Jinja template filters
    @app.template_filter('cat_icon')
    def cat_icon_filter(cat_name):
        return get_category_icon(cat_name)

    @app.template_filter('cat_color')
    def cat_color_filter(cat_name):
        return get_category_color(cat_name)

    @app.template_filter('date_format')
    def date_format_filter(d, fmt='%b %d, %Y'):
        if not d:
            return 'Ongoing'
        return d.strftime(fmt)

    # Automatic database table creation
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database initialization notice: {e}")

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
