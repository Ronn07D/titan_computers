from app.extensions import db
from datetime import datetime

class Oferta(db.Model):
    __tablename__ = 'oferta'
    id_oferta = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    porcentaje_descuento = db.Column(db.Numeric(5, 2), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    estado = db.Column(db.Boolean, default=True)

    # Relación con Productos (Muchos a Muchos a través de detalle_oferta)
    productos = db.relationship('Producto', secondary='detalle_oferta', backref='ofertas')
    
    # Relación con la tabla de detalles
    detalles = db.relationship('DetalleOferta', backref='oferta', lazy=True)

class DetalleOferta(db.Model):
    __tablename__ = 'detalle_oferta'
    id_detalle_oferta = db.Column(db.Integer, primary_key=True)
    id_oferta = db.Column(db.Integer, db.ForeignKey('oferta.id_oferta'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    precio_oferta = db.Column(db.Numeric(10, 2), nullable=False)

class Promocion(db.Model):
    __tablename__ = 'promocion'
    id_promocion = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    condiciones = db.Column(db.String(255))
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    estado = db.Column(db.Boolean, default=True)

    # Relación con Productos
    productos = db.relationship('Producto', secondary='detalle_promocion', backref='promociones')
    #Relacion con detallePromocion
    detalles = db.relationship('DetallePromocion', backref='promocion', lazy=True)

class DetallePromocion(db.Model):
    __tablename__ = 'detalle_promocion'
    id_detalle_promocion = db.Column(db.Integer, primary_key=True)
    id_promocion = db.Column(db.Integer, db.ForeignKey('promocion.id_promocion'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)