from datetime import datetime
from app.extensions import db


class Pago(db.Model):
    __tablename__ = 'pago'

    id_pago = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedido.id_pedido'), nullable=False)
    metodo = db.Column(db.Enum('TRANSFERENCIA', 'QR'), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    referencia = db.Column(db.String(60))          # nro. de transaccion (opcional)
    comprobante = db.Column(db.String(255))        # nombre del archivo subido
    estado = db.Column(db.Enum('PENDIENTE', 'VALIDADO', 'RECHAZADO'),
                       nullable=False, default='PENDIENTE')
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_validacion = db.Column(db.DateTime)
    id_validador = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))
    observacion = db.Column(db.String(255))        # motivo si se rechaza

    pedido = db.relationship('Pedido', backref=db.backref('pagos', lazy=True))
    validador = db.relationship('Usuario')


class Venta(db.Model):
    __tablename__ = 'venta'

    id_venta = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedido.id_pedido'),
                          nullable=False, unique=True)
    id_pago = db.Column(db.Integer, db.ForeignKey('pago.id_pago'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    pedido = db.relationship('Pedido', backref=db.backref('venta', uselist=False))
    pago = db.relationship('Pago', backref=db.backref('venta', uselist=False))
