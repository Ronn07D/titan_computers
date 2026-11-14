from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.usuario import Usuario, Cliente

def registrar_usuario(nombre_usuario, contrasena, nombres, apellidos, correo, telefono, rol='CLIENTE'):
    # Verificar si el usuario ya existe
    if Usuario.query.filter_by(nombre_usuario=nombre_usuario).first():
        return False, "El nombre de usuario ya está en uso."
    
    # Encriptar la contraseña (RNF-02)
    hash_contrasena = generate_password_hash(contrasena)
    
    # Crear el Usuario
    nuevo_usuario = Usuario(nombre_usuario=nombre_usuario, contrasena_hash=hash_contrasena, rol=rol)
    db.session.add(nuevo_usuario)
    db.session.flush() # Para obtener el ID generado
    
    # Crear el Cliente vinculado
    nuevo_cliente = Cliente(
        id_usuario=nuevo_usuario.id_usuario,
        nombres=nombres, apellidos=apellidos, correo=correo, telefono=telefono
    )
    db.session.add(nuevo_cliente)
    db.session.commit()
    
    return True, "Usuario registrado exitosamente."

def verificar_login(nombre_usuario, contrasena):
    # Buscar usuario activo
    usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario, estado=True).first()
    # Verificar contraseña
    if usuario and check_password_hash(usuario.contrasena_hash, contrasena):
        return usuario
    return None