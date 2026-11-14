from app.extensions import db
from flask_login import UserMixin
from datetime import datetime

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('ADMIN', 'CLIENTE'), nullable=False)
    estado = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con Cliente
    cliente = db.relationship('Cliente', backref='usuario', uselist=False, cascade="all, delete-orphan")

    def get_id(self):
        return str(self.id_usuario)

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id_cliente = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    nombres = db.Column(db.String(80), nullable=False)
    apellidos = db.Column(db.String(80), nullable=False)
    ci = db.Column(db.String(20))
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(100))