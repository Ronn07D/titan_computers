from app import create_app
from app.modules.auth.services import registrar_usuario

app = create_app()

with app.app_context():
    print("--- CREANDO USUARIO ADMINISTRADOR ---")
    
    # Aquí defines las credenciales del Admin
    exito, mensaje = registrar_usuario(
        nombre_usuario="admin", 
        contrasena="admin123", 
        nombres="Eduardo", 
        apellidos="Claure", 
        correo="admin@titan.com", 
        telefono="7777777"
        rol='ADMIN'
    )
    
    if exito:
        print("¡Éxito! El usuario administrador ha sido creado.")
        print("Usuario: admin")
        print("Contraseña: admin123")
    else:
        print("Aviso:", mensaje)