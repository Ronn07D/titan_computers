from flask import Blueprint

bp_ofertas = Blueprint('ofertas', __name__, template_folder='templates')

from app.modules.ofertas import routes