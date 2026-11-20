from flask import Blueprint

bp_carrito = Blueprint('carrito', __name__, template_folder='templates')

from app.modules.carrito import routes
