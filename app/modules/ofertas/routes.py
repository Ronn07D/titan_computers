from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.oferta import Oferta, DetalleOferta, Promocion, DetallePromocion
from datetime import datetime
from app.modules.ofertas import bp_ofertas
from app.extensions import db
from app.models.oferta import Oferta, DetalleOferta
from app.models.catalogo import Producto

# --- LISTAR OFERTAS ---
@bp_ofertas.route('/admin')
@login_required
def admin_ofertas():
    if current_user.rol != 'ADMIN':
        return redirect('/')
    ofertas = Oferta.query.all()
    return render_template('ofertas/admin_ofertas.html', ofertas=ofertas)

# --- CREAR OFERTA ---
@bp_ofertas.route('/admin/nueva', methods=['GET', 'POST'])
@login_required
def nueva_oferta():
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    productos = Producto.query.filter_by(estado=True).all()

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        porcentaje = float(request.form.get('porcentaje_descuento'))
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        
        nueva_of = Oferta(
            nombre=nombre, 
            porcentaje_descuento=porcentaje,
            fecha_inicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date(),
            fecha_fin=datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        )
        db.session.add(nueva_of)
        db.session.flush()

        productos_seleccionados = request.form.getlist('productos')
        for prod_id in productos_seleccionados:
            producto = Producto.query.get(prod_id)
            precio_oferta = float(producto.precio) - (float(producto.precio) * (porcentaje / 100))
            
            detalle = DetalleOferta(
                id_oferta=nueva_of.id_oferta,
                id_producto=producto.id_producto,
                precio_oferta=precio_oferta
            )
            db.session.add(detalle)

        db.session.commit()
        flash('Oferta creada exitosamente.', 'success')
        return redirect(url_for('ofertas.admin_ofertas'))

    return render_template('ofertas/form_oferta.html', productos=productos)

# --- ACTIVAR / DESACTIVAR OFERTA ---
@bp_ofertas.route('/admin/oferta/<int:id>/estado')
@login_required
def cambiar_estado_oferta(id):
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    oferta = Oferta.query.get_or_404(id)
    oferta.estado = not oferta.estado
    db.session.commit()
    
    estado_texto = "activada" if oferta.estado else "desactivada"
    flash(f'Oferta {oferta.nombre} {estado_texto} correctamente.', 'success')
    return redirect(url_for('ofertas.admin_ofertas'))

# --- EDITAR OFERTA (RF-19) ---
@bp_ofertas.route('/admin/oferta/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_oferta(id):
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    oferta = Oferta.query.get_or_404(id)
    productos = Producto.query.filter_by(estado=True).all()

    if request.method == 'POST':
        oferta.nombre = request.form.get('nombre')
        nuevo_porcentaje = float(request.form.get('porcentaje_descuento'))
        oferta.porcentaje_descuento = nuevo_porcentaje
        oferta.fecha_inicio = datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date()
        oferta.fecha_fin = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date()
        
        # 1. Eliminamos los detalles anteriores para recalcular desde cero
        DetalleOferta.query.filter_by(id_oferta=oferta.id_oferta).delete()
        
        # 2. Recreamos los detalles con el nuevo porcentaje
        productos_seleccionados = request.form.getlist('productos')
        for prod_id in productos_seleccionados:
            producto = Producto.query.get(prod_id)
            # Recalculamos el precio
            precio_oferta = float(producto.precio) - (float(producto.precio) * (nuevo_porcentaje / 100))
            
            detalle = DetalleOferta(
                id_oferta=oferta.id_oferta,
                id_producto=producto.id_producto,
                precio_oferta=precio_oferta
            )
            db.session.add(detalle)

        db.session.commit()
        flash('Oferta actualizada exitosamente.', 'success')
        return redirect(url_for('ofertas.admin_ofertas'))

    # Buscamos qué productos ya están en esta oferta para marcarlos en el formulario
    productos_en_oferta = [d.id_producto for d in oferta.detalles]
    
    return render_template('ofertas/form_oferta.html', 
                           productos=productos, 
                           oferta=oferta, 
                           productos_en_oferta=productos_en_oferta)


# --- LISTAR PROMOCIONES ---
@bp_ofertas.route('/admin/promociones')
@login_required
def admin_promociones():
    if current_user.rol != 'ADMIN':
        return redirect('/')
    promociones = Promocion.query.all()
    return render_template('ofertas/admin_promociones.html', promociones=promociones)

# --- CREAR PROMOCIÓN ---
@bp_ofertas.route('/admin/promocion/nueva', methods=['GET', 'POST'])
@login_required
def nueva_promocion():
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    productos = Producto.query.filter_by(estado=True).all()

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        condiciones = request.form.get('condiciones')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        
        nueva_promo = Promocion(
            titulo=titulo, descripcion=descripcion, condiciones=condiciones,
            fecha_inicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date(),
            fecha_fin=datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        )
        db.session.add(nueva_promo)
        db.session.flush()

        productos_seleccionados = request.form.getlist('productos')
        for prod_id in productos_seleccionados:
            detalle = DetallePromocion(
                id_promocion=nueva_promo.id_promocion,
                id_producto=prod_id
            )
            db.session.add(detalle)

        db.session.commit()
        flash('Promoción creada exitosamente.', 'success')
        return redirect(url_for('ofertas.admin_promociones'))

    return render_template('ofertas/form_promocion.html', productos=productos)

# --- EDITAR PROMOCIÓN ---
@bp_ofertas.route('/admin/promocion/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_promocion(id):
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    promocion = Promocion.query.get_or_404(id)
    productos = Producto.query.filter_by(estado=True).all()

    if request.method == 'POST':
        promocion.titulo = request.form.get('titulo')
        promocion.descripcion = request.form.get('descripcion')
        promocion.condiciones = request.form.get('condiciones')
        promocion.fecha_inicio = datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date()
        promocion.fecha_fin = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date()
        
        # Eliminamos los detalles viejos y los recreamos
        DetallePromocion.query.filter_by(id_promocion=promocion.id_promocion).delete()
        
        productos_seleccionados = request.form.getlist('productos')
        for prod_id in productos_seleccionados:
            detalle = DetallePromocion(
                id_promocion=promocion.id_promocion,
                id_producto=prod_id
            )
            db.session.add(detalle)

        db.session.commit()
        flash('Promoción actualizada exitosamente.', 'success')
        return redirect(url_for('ofertas.admin_promociones'))

    # Obtenemos los IDs de los productos ya asociados
    productos_en_promo = [d.id_producto for d in promocion.detalles]
    
    return render_template('ofertas/form_promocion.html', 
                           productos=productos, 
                           promocion=promocion, 
                           productos_en_promo=productos_en_promo)

# --- ACTIVAR / DESACTIVAR PROMOCIÓN ---
@bp_ofertas.route('/admin/promocion/<int:id>/estado')
@login_required
def cambiar_estado_promocion(id):
    if current_user.rol != 'ADMIN':
        return redirect('/')
        
    promocion = Promocion.query.get_or_404(id)
    promocion.estado = not promocion.estado
    db.session.commit()
    
    estado_texto = "activada" if promocion.estado else "desactivada"
    flash(f'Promoción {promocion.titulo} {estado_texto} correctamente.', 'success')
    return redirect(url_for('ofertas.admin_promociones'))