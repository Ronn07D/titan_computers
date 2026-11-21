from datetime import date, datetime, timedelta

from flask import (
    render_template,
    request,
    redirect,
    abort
)
from flask_login import login_required, current_user
from sqlalchemy import func, or_

from app.modules.ventas import bp_ventas
from app.extensions import db
from app.models import Pedido, Cliente
from app.models.pago import Venta


POR_PAGINA = 15


# --- CONVERTIR FECHA ---

def _fecha(texto):
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


# --- CONSULTA DE VENTAS CON FILTROS ---

def _consulta_filtrada(desde, hasta, texto):
    consulta = (
        Venta.query
        .join(Pedido, Venta.id_pedido == Pedido.id_pedido)
        .join(Cliente, Pedido.id_cliente == Cliente.id_cliente)
    )

    if desde:
        inicio = datetime.combine(
            desde,
            datetime.min.time()
        )
        consulta = consulta.filter(Venta.fecha >= inicio)

    if hasta:
        fin = datetime.combine(
            hasta + timedelta(days=1),
            datetime.min.time()
        )
        consulta = consulta.filter(Venta.fecha < fin)

    if texto:
        patron = f'%{texto}%'

        condiciones = [
            Cliente.nombres.ilike(patron),
            Cliente.apellidos.ilike(patron),
            Cliente.ci.ilike(patron)
        ]

        if texto.isdigit():
            condiciones.append(Venta.id_venta == int(texto))

        consulta = consulta.filter(or_(*condiciones))

    return consulta


# --- LISTAR VENTAS CON FILTROS ---

@bp_ventas.route('/')
@login_required
def lista():
    if current_user.rol != 'ADMIN':
        return redirect('/')

    desde = _fecha(request.args.get('desde'))
    hasta = _fecha(request.args.get('hasta'))
    texto = request.args.get('q', '').strip()
    pagina = request.args.get('page', 1, type=int)

    consulta = _consulta_filtrada(desde, hasta, texto)

    total_monto = consulta.with_entities(
        func.coalesce(func.sum(Venta.total), 0)
    ).scalar()

    cantidad = consulta.count()

    paginacion = (
        consulta
        .order_by(Venta.fecha.desc())
        .paginate(
            page=pagina,
            per_page=POR_PAGINA,
            error_out=False
        )
    )

    return render_template(
        'ventas/lista.html',
        paginacion=paginacion,
        total_monto=total_monto,
        cantidad=cantidad,
        desde=request.args.get('desde', ''),
        hasta=request.args.get('hasta', ''),
        q=texto
    )
