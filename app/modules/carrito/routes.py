from app.models import pedido
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.modules.carrito import bp_carrito
from app.extensions import db
from app.models.pedido import Carrito, DetalleCarrito, Pedido, DetallePedido
from app.models.catalogo import Producto
from app.models.oferta import Oferta
from datetime import date

# --- FUNCIÓN AUXILIAR: Obtener o crear el carrito activo del cliente ---
def obtener_carrito():
    carrito = Carrito.query.filter_by(id_cliente=current_user.cliente.id_cliente, estado='ACTIVO').first()
    if not carrito:
        carrito = Carrito(id_cliente=current_user.cliente.id_cliente)
        db.session.add(carrito)
        db.session.commit()
    return carrito

# --- AGREGAR AL CARRITO (RF-21) ---
@bp_carrito.route('/agregar/<int:id_producto>')
@login_required
def agregar(id_producto):
    if current_user.rol != 'CLIENTE':
        return redirect('/')
        
    producto = Producto.query.get_or_404(id_producto)
    
    # Verificar stock
    if producto.stock <= 0:
        flash('Producto sin stock disponible.', 'danger')
        return redirect(url_for('catalogo.tienda'))
        
    carrito = obtener_carrito()
    
    # Verificar si el producto ya está en el carrito
    detalle = DetalleCarrito.query.filter_by(id_carrito=carrito.id_carrito, id_producto=producto.id_producto).first()
    
    if detalle:
        detalle.cantidad += 1
    else:
        nuevo_detalle = DetalleCarrito(id_carrito=carrito.id_carrito, id_producto=producto.id_producto, cantidad=1)
        db.session.add(nuevo_detalle)
        
    db.session.commit()
    flash('Producto agregado al carrito.', 'success')
    return redirect(url_for('carrito.ver_carrito'))

# --- VER CARRITO ---
@bp_carrito.route('/')
@login_required
def ver_carrito():
    if current_user.rol != 'CLIENTE':
        return redirect('/')
        
    carrito = obtener_carrito()
    
    # Calculamos el total (aplicando ofertas si existen)
    hoy = date.today()
    ofertas_vigentes = Oferta.query.filter(Oferta.estado == True, Oferta.fecha_inicio <= hoy, Oferta.fecha_fin >= hoy).all()
    descuentos = {}
    for oferta in ofertas_vigentes:
        for detalle_of in oferta.detalles:
            descuentos[detalle_of.id_producto] = detalle_of.precio_oferta

    total = 0
    for detalle in carrito.detalles:
        precio = float(descuentos.get(detalle.id_producto, detalle.producto.precio))
        total += precio * detalle.cantidad

    return render_template('carrito/ver_carrito.html', carrito=carrito, descuentos=descuentos, total=total)

# --- ELIMINAR DEL CARRITO (RF-22) ---
@bp_carrito.route('/eliminar/<int:id_detalle>')
@login_required
def eliminar(id_detalle):
    if current_user.rol != 'CLIENTE':
        return redirect('/')
        
    detalle = DetalleCarrito.query.get_or_404(id_detalle)
    db.session.delete(detalle) # Eliminación física
    db.session.commit()
    flash('Producto eliminado del carrito.', 'info')
    return redirect(url_for('carrito.ver_carrito'))

# --- CONFIRMAR PEDIDO (RF-23) ---
@bp_carrito.route('/confirmar')
@login_required
def confirmar_pedido():
    if current_user.rol != 'CLIENTE':
        return redirect(
    url_for("pagos.pagar", id_pedido=pedido.id_pedido)
)
        
    carrito = obtener_carrito()
    
    if not carrito.detalles:
        flash('Tu carrito está vacío.', 'warning')
        return redirect(url_for('carrito.ver_carrito'))
        
    # 1. Calcular el total real (con ofertas)
    hoy = date.today()
    ofertas_vigentes = Oferta.query.filter(Oferta.estado == True, Oferta.fecha_inicio <= hoy, Oferta.fecha_fin >= hoy).all()
    descuentos = {d.id_producto: d.precio_oferta for o in ofertas_vigentes for d in o.detalles}

    total = 0
    for detalle in carrito.detalles:
        precio = float(descuentos.get(detalle.id_producto, detalle.producto.precio))
        total += precio * detalle.cantidad

    # 2. Crear el Pedido
    nuevo_pedido = Pedido(
        id_cliente=current_user.cliente.id_cliente,
        total=total,
        estado='PENDIENTE'
    )
    db.session.add(nuevo_pedido)
    db.session.flush() # Para obtener el ID del pedido

    # 3. Pasar los productos del carrito al detalle del pedido
    for detalle in carrito.detalles:
        precio_unitario = float(descuentos.get(detalle.id_producto, detalle.producto.precio))
        nuevo_detalle = DetallePedido(
            id_pedido=nuevo_pedido.id_pedido,
            id_producto=detalle.id_producto,
            cantidad=detalle.cantidad,
            precio_unitario=precio_unitario,
            subtotal=precio_unitario * detalle.cantidad
        )
        db.session.add(nuevo_detalle)

    # 4. Marcar el carrito como procesado (para que se cree uno nuevo la próxima vez)
    carrito.estado = 'PROCESADO'
    db.session.commit()

    flash('¡Pedido registrado exitosamente! Por favor, procede con el pago.', 'success')
    # Lo mandamos a la vista de "Mis Pedidos" (que crearemos ahora)
    return redirect(url_for('carrito.mis_pedidos'))

# --- VER MIS PEDIDOS (RF-24) ---

@bp_carrito.route('/mis-pedidos')
@login_required
def mis_pedidos():
    if current_user.rol != 'CLIENTE':
        return redirect('/')

    return redirect(url_for('pagos.mis_pedidos'))


# --- CANCELAR PEDIDO (Lógica de arrepentimiento) ---
@bp_carrito.route('/pedido/<int:id_pedido>/cancelar')
@login_required
def cancelar_pedido(id_pedido):
    if current_user.rol != 'CLIENTE':
        return redirect('/')
        
    pedido = Pedido.query.get_or_404(id_pedido)
    
    # Seguridad: Verificar que el pedido sea del cliente logueado
    if pedido.id_cliente != current_user.cliente.id_cliente:
        flash('No tienes permiso para cancelar este pedido.', 'danger')
        return redirect(url_for('carrito.mis_pedidos'))
        
    # Solo se puede cancelar si está PENDIENTE
    if pedido.estado == 'PENDIENTE':
        pedido.estado = 'CANCELADO'
        db.session.commit()
        flash('El pedido ha sido cancelado correctamente.', 'info')
    else:
        flash('Este pedido ya no se puede cancelar.', 'warning')
        
    return redirect(url_for('carrito.mis_pedidos'))