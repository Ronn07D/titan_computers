import os
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.modules.catalogo import bp_catalogo
from app.extensions import db
from app.models.catalogo import Categoria, Marca, Producto

# --- RUTAS DE CATEGORÍAS ---

@bp_catalogo.route('/admin/categorias')
@login_required
def admin_categorias():
    if current_user.rol != 'ADMIN':
        return redirect('/')
    categorias = Categoria.query.all()
    return render_template('catalogo/admin_categorias.html', categorias=categorias)

@bp_catalogo.route('/admin/categoria/nueva', methods=['GET', 'POST'])
@login_required
def nueva_categoria():
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        
        nueva_cat = Categoria(nombre=nombre, descripcion=descripcion)
        db.session.add(nueva_cat)
        db.session.commit()
        flash('Categoría creada exitosamente.', 'success')
        return redirect(url_for('catalogo.admin_categorias'))
        
    return render_template('catalogo/form_categoria.html', categoria=None)


# --- RUTAS DE MARCAS ---

@bp_catalogo.route('/admin/marcas')
@login_required
def admin_marcas():
    if current_user.rol != 'ADMIN':
        return redirect('/')
    marcas = Marca.query.all()
    return render_template('catalogo/admin_marcas.html', marcas=marcas)

@bp_catalogo.route('/admin/marca/nueva', methods=['GET', 'POST'])
@login_required
def nueva_marca():
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        
        nueva_mar = Marca(nombre=nombre, descripcion=descripcion)
        db.session.add(nueva_mar)
        db.session.commit()
        flash('Marca creada exitosamente.', 'success')
        return redirect(url_for('catalogo.admin_marcas'))
        
    return render_template('catalogo/form_marca.html', marca=None)

# --- ACTUALIZAR CATEGORÍA ---
@bp_catalogo.route('/admin/categoria/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_categoria(id):
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    categoria = Categoria.query.get_or_404(id)
    
    if request.method == 'POST':
        categoria.nombre = request.form.get('nombre')
        categoria.descripcion = request.form.get('descripcion')
        db.session.commit()
        flash('Categoría actualizada correctamente.', 'success')
        return redirect(url_for('catalogo.admin_categorias'))
        
    return render_template('catalogo/form_categoria.html', categoria=categoria)

# --- ACTUALIZAR MARCA ---
@bp_catalogo.route('/admin/marca/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_marca(id):
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    marca = Marca.query.get_or_404(id)
    
    if request.method == 'POST':
        marca.nombre = request.form.get('nombre')
        marca.descripcion = request.form.get('descripcion')
        db.session.commit()
        flash('Marca actualizada correctamente.', 'success')
        return redirect(url_for('catalogo.admin_marcas'))
        
    return render_template('catalogo/form_marca.html', marca=marca)

# --- ACTIVAR / DESACTIVAR CATEGORÍA (eliminacion logica)---
@bp_catalogo.route('/admin/categoria/<int:id>/estado')
@login_required
def cambiar_estado_categoria(id):
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    categoria = Categoria.query.get_or_404(id)
    
    # Cambiamos el estado (si era True pasa a False y viceversa)
    categoria.estado = not categoria.estado
    db.session.commit()
    
    estado_texto = "activada" if categoria.estado else "desactivada"
    flash(f'Categoría {categoria.nombre} {estado_texto} correctamente.', 'success')
    return redirect(url_for('catalogo.admin_categorias'))


# --- ACTIVAR / DESACTIVAR MARCA (Eliminación Lógica) ---
@bp_catalogo.route('/admin/marca/<int:id>/estado')
@login_required
def cambiar_estado_marca(id):
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    marca = Marca.query.get_or_404(id)
    
    # Invertimos el estado (de True a False y viceversa)
    marca.estado = not marca.estado
    db.session.commit()
    
    estado_texto = "activada" if marca.estado else "desactivada"
    flash(f'Marca {marca.nombre} {estado_texto} correctamente.', 'success')
    return redirect(url_for('catalogo.admin_marcas'))

# --- CATÁLOGO PÚBLICO (RF-15 y RF-16) ---
@bp_catalogo.route('/tienda')
def tienda():
    # 1. Capturamos los filtros de búsqueda (si existen)
    busqueda = request.args.get('q', '')
    categoria_id = request.args.get('categoria', '')
    marca_id = request.args.get('marca', '')

    # 2. Consulta base: solo productos activos
    query = Producto.query.filter_by(estado=True)

    # 3. Aplicamos los filtros
    if busqueda:
        query = query.filter(Producto.nombre.ilike(f'%{busqueda}%'))
    if categoria_id:
        query = query.filter_by(id_categoria=categoria_id)
    if marca_id:
        query = query.filter_by(id_marca=marca_id)

    # 4. Ejecutamos la consulta
    productos = query.all()
    
    # 5. Traemos categorías y marcas activas para los desplegables
    categorias = Categoria.query.filter_by(estado=True).all()
    marcas = Marca.query.filter_by(estado=True).all()

    return render_template('catalogo/tienda.html', 
                           productos=productos, 
                           categorias=categorias, 
                           marcas=marcas,
                           busqueda=busqueda)

#catalogo 

@bp_catalogo.route('/admin/productos')
@login_required
def admin_productos():
    if current_user.rol != 'ADMIN':
        return redirect('/')
    productos = Producto.query.all()
    return render_template('catalogo/admin_productos.html', productos=productos)


# --- CREAR NUEVO PRODUCTO (RF-12) ---
@bp_catalogo.route('/admin/producto/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    # Traemos las categorías y marcas activas para los menús desplegables
    categorias = Categoria.query.filter_by(estado=True).all()
    marcas = Marca.query.filter_by(estado=True).all()

    if request.method == 'POST':
        #genera el codgo automaticamente 
        total_productos = Producto.query.count() + 1
        codigo = f"P-{total_productos:03d}"
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio')
        stock = request.form.get('stock')
        id_categoria = request.form.get('id_categoria')
        id_marca = request.form.get('id_marca')
        
        # Manejo de la imagen
        imagen = request.files.get('imagen')
        nombre_imagen = None
        
        if imagen and imagen.filename != '':
            nombre_imagen = secure_filename(imagen.filename)
            ruta_guardado = os.path.join(current_app.config['UPLOAD_FOLDER'], nombre_imagen)
            imagen.save(ruta_guardado)

        # Guardamos en la Base de Datos
        nuevo_prod = Producto(
            codigo=codigo, nombre=nombre, descripcion=descripcion,
            precio=precio, stock=stock, id_categoria=id_categoria,
            id_marca=id_marca, imagen=nombre_imagen
        )
        db.session.add(nuevo_prod)
        db.session.commit()
        
        flash('Producto registrado exitosamente.', 'success')
        return redirect(url_for('catalogo.admin_productos'))

    # Si es GET, mostramos el formulario vacío
    return render_template('catalogo/form_producto.html', categorias=categorias, marcas=marcas, producto=None)


# --- ACTUALIZAR PRODUCTO (RF-13) ---
@bp_catalogo.route('/admin/producto/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    producto = Producto.query.get_or_404(id)
    categorias = Categoria.query.filter_by(estado=True).all()
    marcas = Marca.query.filter_by(estado=True).all()

    if request.method == 'POST':
        producto.nombre = request.form.get('nombre')
        producto.descripcion = request.form.get('descripcion')
        producto.precio = request.form.get('precio')
        producto.stock = request.form.get('stock')
        producto.id_categoria = request.form.get('id_categoria')
        producto.id_marca = request.form.get('id_marca')
        
        # Si el admin sube una imagen nueva, la reemplazamos
        imagen = request.files.get('imagen')
        if imagen and imagen.filename != '':
            nombre_imagen = secure_filename(imagen.filename)
            ruta_guardado = os.path.join(current_app.config['UPLOAD_FOLDER'], nombre_imagen)
            imagen.save(ruta_guardado)
            producto.imagen = nombre_imagen 

        db.session.commit()
        flash('Producto actualizado exitosamente.', 'success')
        return redirect(url_for('catalogo.admin_productos'))

    return render_template('catalogo/form_producto.html', categorias=categorias, marcas=marcas, producto=producto)

# --- ACTIVAR / DESACTIVAR PRODUCTO (Eliminación Lógica) ---
@bp_catalogo.route('/admin/producto/<int:id>/estado')
@login_required
def cambiar_estado_producto(id):
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    producto = Producto.query.get_or_404(id)
    
    # Invertimos el estado (de True a False y viceversa)
    producto.estado = not producto.estado
    db.session.commit()
    
    estado_texto = "activado" if producto.estado else "desactivado"
    flash(f'Producto {producto.nombre} {estado_texto} correctamente.', 'success')
    return redirect(url_for('catalogo.admin_productos'))
