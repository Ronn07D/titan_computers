

from flask import Blueprint

reportes_bp = Blueprint(
    'reportes',
    __name__,
    template_folder='templates',
    url_prefix='/reportes'
)

from app.modules.reportes import routes