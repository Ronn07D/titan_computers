from flask import Blueprint

bp_pagos = Blueprint(
    'pagos',
    __name__,
    template_folder='templates',
    url_prefix='/pagos'
)

from app.modules.pagos import routes