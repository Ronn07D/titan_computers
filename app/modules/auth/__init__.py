from flask import Blueprint

# 1. Creamos el Blueprint
bp_auth = Blueprint('auth', __name__, template_folder='templates')

# 2. Importamos las rutas AL FINAL para evitar importaciones circulares
from app.modules.auth import routes