"""Consultas de los reportes. Cada funcion devuelve un diccionario:
   titulo, filtros (texto), headers, rows, totales [(etiqueta, valor)], num_cols
Con eso se dibuja el HTML y se exporta a CSV y PDF sin repetir logica."""
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import (Producto, Categoria, Marca, Pedido, DetallePedido,
                        Cliente, Promocion, Oferta)
from app.models.pago import Pago, Venta


def _dinero(valor):
    return f'{float(valor or 0):.2f}'


def _f(valor, con_hora=False):
    if not valor:
        return '-'
    return valor.strftime('%d/%m/%Y %H:%M' if con_hora else '%d/%m/%Y')


def _fecha(texto):
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def _rango_dt(desde, hasta):
    ini = datetime.combine(desde, datetime.min.time()) if desde else None
    fin = datetime.combine(hasta + timedelta(days=1), datetime.min.time()) if hasta else None
    return ini, fin


def _texto_rango(desde, hasta):
    if desde and hasta:
        return f'Del {_f(desde)} al {_f(hasta)}'
    if desde:
        return f'Desde el {_f(desde)}'
    if hasta:
        return f'Hasta el {_f(hasta)}'
    return 'Todo el periodo'


def _cliente(c):
    return f'{c.nombres} {c.apellidos}'


# ---------------------------------------------------------------- RF-33
def reporte_productos(args):
    id_cat = args.get('categoria', type=int)
    id_marca = args.get('marca', type=int)
    estado = args.get('estado', '')
    stock_max = args.get('stock_max', type=int)

    q = Producto.query.options(joinedload(Producto.categoria), joinedload(Producto.marca))
    filtros = []
    if id_cat:
        q = q.filter(Producto.id_categoria == id_cat)
        c = db.session.get(Categoria, id_cat)
        filtros.append(f'Categoría: {c.nombre}' if c else 'Categoría')
    if id_marca:
        q = q.filter(Producto.id_marca == id_marca)
        m = db.session.get(Marca, id_marca)
        filtros.append(f'Marca: {m.nombre}' if m else 'Marca')
    if estado == 'activo':
        q = q.filter(Producto.estado.is_(True)); filtros.append('Solo activos')
    elif estado == 'inactivo':
        q = q.filter(Producto.estado.is_(False)); filtros.append('Solo inactivos')
    if stock_max is not None:
        q = q.filter(Producto.stock <= stock_max); filtros.append(f'Stock hasta {stock_max}')

    vendidas = dict(
        db.session.query(DetallePedido.id_producto, func.sum(DetallePedido.cantidad))
        .join(Venta, Venta.id_pedido == DetallePedido.id_pedido)
        .group_by(DetallePedido.id_producto).all())

    productos = q.order_by(Producto.nombre).all()
    rows = [[p.codigo, p.nombre, p.categoria.nombre, p.marca.nombre,
             _dinero(p.precio), p.stock, int(vendidas.get(p.id_producto, 0) or 0),
             'Activo' if p.estado else 'Inactivo'] for p in productos]
    valor_inv = sum(float(p.precio) * p.stock for p in productos)
    return {
        'titulo': 'Reporte de productos',
        'filtros': ' | '.join(filtros) or 'Sin filtros',
        'headers': ['Código', 'Producto', 'Categoría', 'Marca', 'Precio (Bs.)',
                    'Stock', 'Unid. vendidas', 'Estado'],
        'rows': rows,
        'totales': [('Productos listados', len(productos)),
                    ('Unidades en stock', sum(p.stock for p in productos)),
                    ('Valor del inventario (Bs.)', f'{valor_inv:.2f}')],
        'num_cols': {4, 5, 6},
    }


# ---------------------------------------------------------------- RF-34
def reporte_ventas(args):
    desde, hasta = _fecha(args.get('desde')), _fecha(args.get('hasta'))
    ini, fin = _rango_dt(desde, hasta)
    q = (Venta.query.options(joinedload(Venta.pedido).joinedload(Pedido.cliente),
                             joinedload(Venta.pago)))
    if ini:
        q = q.filter(Venta.fecha >= ini)
    if fin:
        q = q.filter(Venta.fecha < fin)
    ventas = q.order_by(Venta.fecha.desc()).all()

    rows = [[f'#{v.id_venta}', _f(v.fecha, True), f'#{v.id_pedido}',
             _cliente(v.pedido.cliente), v.pedido.cliente.ci or '-',
             'Transferencia' if v.pago.metodo == 'TRANSFERENCIA' else 'QR',
             _dinero(v.total)] for v in ventas]
    total = sum(float(v.total) for v in ventas)
    promedio = total / len(ventas) if ventas else 0
    return {
        'titulo': 'Reporte de ventas',
        'filtros': _texto_rango(desde, hasta),
        'headers': ['Venta', 'Fecha', 'Pedido', 'Cliente', 'CI', 'Método de pago', 'Total (Bs.)'],
        'rows': rows,
        'totales': [('Ventas realizadas', len(ventas)),
                    ('Monto total (Bs.)', f'{total:.2f}'),
                    ('Venta promedio (Bs.)', f'{promedio:.2f}')],
        'num_cols': {6},
    }


# ---------------------------------------------------------------- RF-35
def reporte_pagos(args):
    desde, hasta = _fecha(args.get('desde')), _fecha(args.get('hasta'))
    estado, metodo = args.get('estado', ''), args.get('metodo', '')
    ini, fin = _rango_dt(desde, hasta)

    q = Pago.query.options(joinedload(Pago.pedido).joinedload(Pedido.cliente),
                           joinedload(Pago.validador))
    filtros = [_texto_rango(desde, hasta)]
    if ini:
        q = q.filter(Pago.fecha_pago >= ini)
    if fin:
        q = q.filter(Pago.fecha_pago < fin)
    if estado in ('PENDIENTE', 'VALIDADO', 'RECHAZADO'):
        q = q.filter(Pago.estado == estado); filtros.append(f'Estado: {estado.capitalize()}')
    if metodo in ('TRANSFERENCIA', 'QR'):
        q = q.filter(Pago.metodo == metodo)
        filtros.append('Método: ' + ('Transferencia' if metodo == 'TRANSFERENCIA' else 'QR'))
    pagos = q.order_by(Pago.fecha_pago.desc()).all()

    rows = [[p.id_pago, _f(p.fecha_pago, True), f'#{p.id_pedido}', _cliente(p.pedido.cliente),
             'Transferencia' if p.metodo == 'TRANSFERENCIA' else 'QR',
             p.referencia or '-', _dinero(p.monto), p.estado.capitalize(),
             p.validador.nombre_usuario if p.validador else '-'] for p in pagos]
    def suma(est):
        return f"{sum(float(p.monto) for p in pagos if p.estado == est):.2f}"
    def cuenta(est):
        return sum(1 for p in pagos if p.estado == est)
    return {
        'titulo': 'Reporte de pagos',
        'filtros': ' | '.join(filtros),
        'headers': ['ID', 'Fecha', 'Pedido', 'Cliente', 'Método', 'Referencia',
                    'Monto (Bs.)', 'Estado', 'Validado por'],
        'rows': rows,
        'totales': [('Pagos listados', len(pagos)),
                    ('Pendientes', cuenta('PENDIENTE')),
                    ('Rechazados', cuenta('RECHAZADO')),
                    ('Validados', cuenta('VALIDADO')),
                    ('Monto validado (Bs.)', suma('VALIDADO'))],
        'num_cols': {6},
    }


# ---------------------------------------------------------------- RF-36
def _vigencia(activo, inicio, fin, hoy):
    if not activo:
        return 'Inactiva'
    if hoy < inicio:
        return 'Programada'
    if hoy > fin:
        return 'Vencida'
    return 'Vigente'


def reporte_promociones(args):
    filtro = args.get('vigencia', '')
    hoy = date.today()
    items = []
    for o in Oferta.query.all():
        items.append(('Oferta', o.nombre, o.fecha_inicio, o.fecha_fin,
                      _vigencia(o.estado, o.fecha_inicio, o.fecha_fin, hoy),
                      ', '.join(p.nombre for p in o.productos) or '-',
                      f'{float(o.porcentaje_descuento):.0f}% de descuento'))
    for pr in Promocion.query.all():
        items.append(('Promoción', pr.titulo, pr.fecha_inicio, pr.fecha_fin,
                      _vigencia(pr.estado, pr.fecha_inicio, pr.fecha_fin, hoy),
                      ', '.join(p.nombre for p in pr.productos) or '-',
                      pr.condiciones or pr.descripcion or '-'))
    if filtro:
        items = [i for i in items if i[4].lower() == filtro]
    items.sort(key=lambda i: i[2], reverse=True)

    rows = [[t, n, _f(i), _f(f), v, prod, det] for t, n, i, f, v, prod, det in items]
    return {
        'titulo': 'Reporte de ofertas y promociones',
        'filtros': f'Vigencia: {filtro.capitalize()}' if filtro else 'Todas',
        'headers': ['Tipo', 'Nombre', 'Inicio', 'Fin', 'Vigencia', 'Productos', 'Detalle'],
        'rows': rows,
        'totales': [('Registros listados', len(items)),
                    ('Vigentes', sum(1 for i in items if i[4] == 'Vigente')),
                    ('Vencidas', sum(1 for i in items if i[4] == 'Vencida'))],
        'num_cols': set(),
    }


REPORTES = {
    'productos': reporte_productos,
    'ventas': reporte_ventas,
    'pagos': reporte_pagos,
    'promociones': reporte_promociones,
}
DESCRIPCIONES = {
    'productos': (
        'Reporte de productos',
        'Inventario con precio, stock y unidades vendidas.'
    ),
    'ventas': (
        'Reporte de ventas',
        'Ventas confirmadas por rango de fechas.'
    ),
    'pagos': (
        'Reporte de pagos',
        'Pagos por estado y método, con su validación.'
    ),
    'promociones': (
        'Reporte de promociones',
        'Ofertas y promociones con su vigencia.'
    ),
}