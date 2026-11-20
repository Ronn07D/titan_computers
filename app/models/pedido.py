from app.extensions import db
from datetime import datetime

class Carrito(db.Model):
    __tablename__ = 'carrito'
    id_carrito = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('cliente.id_cliente'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.Enum('ACTIVO', 'PROCESADO'), default='ACTIVO')
    
    cliente = db.relationship('Cliente', backref='carritos')
    detalles = db.relationship('DetalleCarrito', backref='carrito', lazy=True, cascade="all, delete-orphan")

class DetalleCarrito(db.Model):
    __tablename__ = 'detalle_carrito'
    id_detalle_carrito = db.Column(db.Integer, primary_key=True)
    id_carrito = db.Column(db.Integer, db.ForeignKey('carrito.id_carrito'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    
    producto = db.relationship('Producto')

class Pedido(db.Model):
    __tablename__ = 'pedido'
    id_pedido = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('cliente.id_cliente'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.Enum('PENDIENTE', 'ENVIADO', 'ENTREGADO', 'CANCELADO'), default='PENDIENTE')
    observaciones = db.Column(db.String(255))
    
    cliente = db.relationship('Cliente', backref='pedidos')
    detalles = db.relationship('DetallePedido', backref='pedido', lazy=True, cascade="all, delete-orphan")

class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedido'
    id_detalle_pedido = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedido.id_pedido'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
    producto = db.relationship('Producto')