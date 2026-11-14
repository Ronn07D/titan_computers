from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.modules.auth import bp_auth
from app.modules.auth.services import verificar_login, registrar_usuario
from app.extensions import login_manager
from app.models.usuario import Usuario
from flask_login import current_user

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contrasena = request.form.get('contrasena')
        
        user = verificar_login(usuario, contrasena)
        if user:
            login_user(user) #inicia sesion
            #si es admin, a futuro lo mandamos a panel
            if user.rol == 'ADMIN':
                return redirect('/')
            return redirect('/') 
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            
    return render_template('auth/login.html')

@bp_auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('has cerrado sesion', 'info')
    return redirect(url_for('auth.login'))


@bp_auth.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Recibimos los datos del formulario
        usuario = request.form.get('usuario')
        contrasena = request.form.get('contrasena')
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')

        # Llamamos a la lógica de negocio
        exito, mensaje = registrar_usuario(usuario, contrasena, nombres, apellidos, correo, telefono)

        if exito:
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(mensaje, 'danger')

    return render_template('auth/registro.html')


@bp_auth.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        # Actualizamos los datos del cliente
        current_user.cliente.nombres = request.form.get('nombres')
        current_user.cliente.apellidos = request.form.get('apellidos')
        current_user.cliente.correo = request.form.get('correo')
        current_user.cliente.telefono = request.form.get('telefono')
        
        from app.extensions import db
        db.session.commit()
        flash('Perfil actualizado correctamente', 'success')
        return redirect(url_for('auth.perfil'))

    return render_template('auth/perfil.html')


@bp_auth.route('/admin/usuarios')
@login_required
def admin_usuarios():
    # Seguridad: Solo el ADMIN puede entrar aquí
    if current_user.rol != 'ADMIN':
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect('/')
    
    usuarios = Usuario.query.all()
    return render_template('auth/admin_usuarios.html', usuarios=usuarios)

@bp_auth.route('/admin/usuario/<int:id>/estado')
@login_required
def cambiar_estado_usuario(id):
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    usuario = Usuario.query.get_or_404(id)
    # No permitir que el admin se desactive a sí mismo
    if usuario.id_usuario != current_user.id_usuario:
        usuario.estado = not usuario.estado
        from app.extensions import db
        db.session.commit()
        flash(f'Estado de {usuario.nombre_usuario} actualizado.', 'success')
    
    return redirect(url_for('auth.admin_usuarios'))
