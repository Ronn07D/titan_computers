from app.extensions import db

class Categoria(db.Model):
    __tablename__ = 'categoria'
    id_categoria = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)
    descripcion = db.Column(db.String(200))
    estado = db.Column(db.Boolean, default=True)
    
    productos = db.relationship('Producto', backref='categoria', lazy=True)

class Marca(db.Model):
    __tablename__ = 'marca'
    id_marca = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)
    descripcion = db.Column(db.String(200))
    estado = db.Column(db.Boolean, default=True)
    
    productos = db.relationship('Producto', backref='marca', lazy=True)

class Producto(db.Model):
    __tablename__ = 'producto'
    id_producto = db.Column(db.Integer, primary_key=True)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categoria.id_categoria'), nullable=False)
    id_marca = db.Column(db.Integer, db.ForeignKey('marca.id_marca'), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    imagen = db.Column(db.String(255)) 
    estado = db.Column(db.Boolean, default=True)