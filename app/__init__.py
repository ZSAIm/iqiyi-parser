
from flask import Flask
from flask_bootstrap import Bootstrap


bootstrap = Bootstrap()


def create_flask_app():
    app = Flask(__name__)
    bootstrap.init_app(app)
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)
    return app



