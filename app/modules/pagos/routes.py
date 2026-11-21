import os
import uuid
from datetime import datetime

from app.models.pedido import DetallePedido
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_from_directory,
    abort
)
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from werkzeug.utils import secure_filename

from app.modules.pagos import bp_pagos
from app.extensions import db
from app.models import Pedido
from app.models.pago import Pago, Venta


# --- CONFIGURACIÓN DE PAGOS ---

DATOS_BANCARIOS = {
    'Banco': 'Nombre del banco',
    'Titular': 'Titan Computers',
    'Nro. de cuenta': '000-0000000-0-00',
    'Tipo de cuenta': 'Caja de ahorros',
    'Moneda': 'Bolivianos (Bs.)',
}

ARCHIVO_QR = 'qr_pago.png'

EXTENSIONES_OK = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_BYTES = 5 * 1024 * 1024
ESTADOS_PAGO = ('PENDIENTE', 'VALIDADO', 'RECHAZADO')


# --- CARPETA DE COMPROBANTES ---

def carpeta_comprobantes():
    ruta = os.path.join(
        current_app.root_path,
        'uploads',
        'comprobantes'
    )
    os.makedirs(ruta, exist_ok=True)
    return ruta


# --- GUARDAR COMPROBANTE ---

def guardar_comprobante(archivo):
    nombre = secure_filename(archivo.filename or '')

    ext = nombre.rsplit('.', 1)[-1].lower() if '.' in nombre else ''

    if ext not in EXTENSIONES_OK:
        raise ValueError(
            'Formato no permitido. Sube una imagen JPG o PNG, o un PDF.'
        )

    archivo.seek(0, os.SEEK_END)
    tamano = archivo.tell()
    archivo.seek(0)

    if tamano == 0:
        raise ValueError('El archivo está vacío.')

    if tamano > MAX_BYTES:
        raise ValueError('El archivo supera el límite de 5 MB.')

    nuevo = f'{uuid.uuid4().hex}.{ext}'
    ruta = os.path.join(carpeta_comprobantes(), nuevo)
    archivo.save(ruta)

    return nuevo


# --- CONSULTAR PEDIDO DEL CLIENTE ---

def pedido_del_cliente(id_pedido):
    cliente = getattr(current_user, 'cliente', None)
    pedido = db.session.get(Pedido, id_pedido)

    if (
        pedido is None
        or cliente is None
        or pedido.id_cliente != cliente.id_cliente
    ):
        abort(404)

    return pedido


# --- CONSULTAR ÚLTIMO PAGO ---

def ultimo_pago(id_pedido):
    return (
        Pago.query
        .filter_by(id_pedido=id_pedido)
        .order_by(Pago.id_pago.desc())
        .first()
    )


# --- LISTAR PEDIDOS Y PAGOS DEL CLIENTE ---

@bp_pagos.route('/mis-pedidos')
@login_required
def mis_pedidos():
    cliente = current_user.cliente
    filas = []
    if cliente:
        pedidos = (Pedido.query
                   .options(selectinload(Pedido.detalles).joinedload(DetallePedido.producto))
                   .filter_by(id_cliente=cliente.id_cliente)
                   .order_by(Pedido.fecha.desc()).all())

        ultimos = {}
        ids = [p.id_pedido for p in pedidos]
        if ids:
            for pg in Pago.query.filter(Pago.id_pedido.in_(ids)).order_by(Pago.id_pago).all():
                ultimos[pg.id_pedido] = pg

        for p in pedidos:
            pago = ultimos.get(p.id_pedido)
            puede_pagar = (p.estado != 'CANCELADO'
                           and (pago is None or pago.estado == 'RECHAZADO'))
            filas.append({'pedido': p, 'pago': pago, 'puede_pagar': puede_pagar})

    hay_qr = os.path.exists(os.path.join(current_app.static_folder, 'img', ARCHIVO_QR))
    return render_template('pagos/mis_pedidos.html', filas=filas,
                           datos_bancarios=DATOS_BANCARIOS, hay_qr=hay_qr,
                           archivo_qr=ARCHIVO_QR)
    
    
# --- REGISTRAR PAGO Y SUBIR COMPROBANTE ---

@bp_pagos.route(
    '/pedido/<int:id_pedido>/pagar',
    methods=['GET', 'POST']
)
@login_required
def pagar(id_pedido):
    cliente = getattr(current_user, 'cliente', None)

    if current_user.rol != 'CLIENTE' or cliente is None:
        return redirect('/')

    pedido = pedido_del_cliente(id_pedido)
    pago_previo = ultimo_pago(pedido.id_pedido)

    if pedido.estado == 'CANCELADO':
        flash(
            'Este pedido está cancelado y no se puede pagar.',
            'warning'
        )
        return redirect(url_for('pagos.mis_pedidos'))

    if pago_previo and pago_previo.estado in ('PENDIENTE', 'VALIDADO'):
        flash(
            'Este pedido ya tiene un pago registrado.',
            'warning'
        )
        return redirect(url_for('pagos.mis_pedidos'))

    if request.method == 'POST':
        metodo = request.form.get('metodo', '')
        referencia = request.form.get('referencia', '').strip()[:60]
        archivo = request.files.get('comprobante')

        if metodo not in ('TRANSFERENCIA', 'QR'):
            flash('Selecciona un método de pago.', 'danger')

        elif not archivo or not archivo.filename:
            flash('Debes subir el comprobante de pago.', 'danger')

        else:
            try:
                nombre = guardar_comprobante(archivo)

            except ValueError as error:
                flash(str(error), 'danger')

            else:
                nuevo_pago = Pago(
                    id_pedido=pedido.id_pedido,
                    metodo=metodo,
                    monto=pedido.total,
                    referencia=referencia or None,
                    comprobante=nombre,
                    estado='PENDIENTE'
                )

                db.session.add(nuevo_pago)
                db.session.commit()

                flash(
                    'Comprobante enviado. Un administrador lo revisará pronto.',
                    'success'
                )
                return redirect(url_for('pagos.mis_pedidos'))


    hay_qr = os.path.exists(
        os.path.join(current_app.static_folder, 'img', ARCHIVO_QR)
    )

    return render_template(
        'pagos/mis_pedidos.html',
        filas=[pedido],
        pedido=pedido,
        datos_bancarios=DATOS_BANCARIOS,
        hay_qr=hay_qr,
        archivo_qr=ARCHIVO_QR
    )


# --- CONSULTAR COMPROBANTE ---

@bp_pagos.route('/comprobante/<int:id_pago>')
@login_required
def comprobante(id_pago):
    pago = db.session.get(Pago, id_pago)

    if pago is None or not pago.comprobante:
        abort(404)

    if current_user.rol != 'ADMIN':
        cliente = getattr(current_user, 'cliente', None)

        if (
            cliente is None
            or pago.pedido.id_cliente != cliente.id_cliente
        ):
            abort(403)

    return send_from_directory(
        carpeta_comprobantes(),
        pago.comprobante
    )


# --- LISTAR PAGOS PARA EL ADMINISTRADOR ---

@bp_pagos.route('/admin')
@login_required
def admin_lista():
    if current_user.rol != 'ADMIN':
        return redirect('/')

    estado = request.args.get('estado', 'PENDIENTE')
    consulta = Pago.query

    if estado in ESTADOS_PAGO:
        consulta = consulta.filter_by(estado=estado)

    pagos = consulta.order_by(Pago.fecha_pago.desc()).all()

    conteos = dict(
        db.session.query(
            Pago.estado,
            func.count(Pago.id_pago)
        )
        .group_by(Pago.estado)
        .all()
    )

    return render_template(
        'pagos/admin_lista.html',
        pagos=pagos,
        estado=estado,
        conteos=conteos,
        estados=ESTADOS_PAGO
    )


# --- VALIDAR PAGO Y REGISTRAR VENTA ---

@bp_pagos.route(
    '/admin/<int:id_pago>/validar',
    methods=['POST']
)
@login_required
def validar(id_pago):
    if current_user.rol != 'ADMIN':
        return redirect('/')

    pago = db.session.get(Pago, id_pago)

    if pago is None:
        abort(404)

    if pago.estado != 'PENDIENTE':
        flash('Este pago ya fue revisado.', 'warning')
        return redirect(
            url_for('pagos.admin_lista', id_pago=id_pago)
        )

    pedido = pago.pedido

    if pedido.estado == 'CANCELADO':
        flash(
            'No se puede validar un pago de un pedido cancelado.',
            'warning'
        )
        return redirect(
            url_for('pagos.admin_lista', id_pago=id_pago)
        )

    ahora = datetime.utcnow()

    pago.estado = 'VALIDADO'
    pago.fecha_validacion = ahora
    pago.id_validador = current_user.id_usuario
    pago.observacion = None

    if pedido.venta is None:
        nueva_venta = Venta(
            id_pedido=pedido.id_pedido,
            id_pago=pago.id_pago,
            fecha=ahora,
            total=pedido.total
        )
        db.session.add(nueva_venta)

    db.session.commit()

    flash(
        f'Pago validado para el pedido #{pedido.id_pedido}.',
        'success'
    )
    return redirect(url_for('pagos.admin_lista'))


# --- RECHAZAR PAGO ---

@bp_pagos.route(
    '/admin/<int:id_pago>/rechazar',
    methods=['POST']
)
@login_required
def rechazar(id_pago):
    if current_user.rol != 'ADMIN':
        return redirect('/')

    pago = db.session.get(Pago, id_pago)

    if pago is None:
        abort(404)

    if pago.estado != 'PENDIENTE':
        flash('Este pago ya fue revisado.', 'warning')
        return redirect(
            url_for('pagos.admin_lista', id_pago=id_pago)
        )

    motivo = request.form.get('observacion', '').strip()

    if not motivo:
        flash(
            'Escribe el motivo del rechazo para que el cliente sepa qué corregir.',
            'danger'
        )
        return redirect(
            url_for('pagos.admin_lista', id_pago=id_pago)
        )

    pago.estado = 'RECHAZADO'
    pago.fecha_validacion = datetime.utcnow()
    pago.id_validador = current_user.id_usuario
    pago.observacion = motivo[:255]

    db.session.commit()

    flash(
        'Pago rechazado. El cliente podrá subir un nuevo comprobante.',
        'success'
    )
    return redirect(url_for('pagos.admin_lista'))