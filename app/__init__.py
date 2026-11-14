from flask import Flask
from .extensions import db, migrate, login_manager
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # Si no hay sesión, va al login

    # Registrar Blueprints (Incremento I)
    from app.modules.auth import bp_auth
    app.register_blueprint(bp_auth, url_prefix='/auth')

    #registrar blueprints de catalogo
    from app.modules.catalogo import bp_catalogo
    app.register_blueprint(bp_catalogo, url_prefix='/catalogo')

    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')
    return app