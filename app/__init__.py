from flask import Flask
from .extensions import db, migrate, login_manager
from config import Config
from datetime import date

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

    # Registrar blueprints de catalogo
    from app.modules.catalogo import bp_catalogo
    app.register_blueprint(bp_catalogo, url_prefix='/catalogo')

    # Blueprint de Ofertas
    from app.modules.ofertas import bp_ofertas
    app.register_blueprint(bp_ofertas, url_prefix='/ofertas')

    # blueprint de carrito
    from app.modules.carrito import bp_carrito
    app.register_blueprint(bp_carrito, url_prefix='/carrito')

    @app.route('/')
    def index():
        from flask import render_template
        from app.models.catalogo import Producto
        from app.models.oferta import Oferta
        
        
        # 1. Traemos los últimos 4 productos agregados
        productos_destacados = Producto.query.filter_by(estado=True).order_by(Producto.id_producto.desc()).limit(4).all()
        
        # 2. Traemos las ofertas vigentes
        hoy = date.today()
        ofertas_vigentes = Oferta.query.filter(
            Oferta.estado == True,
            Oferta.fecha_inicio <= hoy,
            Oferta.fecha_fin >= hoy
        ).all()
        
        # Creamos el diccionario de descuentos para las tarjetas
        descuentos = {}
        for oferta in ofertas_vigentes:
            for detalle in oferta.detalles:
                descuentos[detalle.id_producto] = detalle.precio_oferta

        return render_template('index.html', 
                            productos=productos_destacados, 
                            descuentos=descuentos)

    return app