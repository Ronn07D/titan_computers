from flask import Blueprint

bp_ventas = Blueprint(
    'ventas',
    __name__,
    template_folder='templates',
    url_prefix='/ventas'
)

from app.modules.ventas import routes