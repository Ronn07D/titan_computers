from flask import Blueprint

bp_catalogo = Blueprint('catalogo', __name__, template_folder='templates')

from app.modules.catalogo import routes