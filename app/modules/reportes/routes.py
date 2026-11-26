"""Incremento VI: reportes de productos, ventas, pagos y promociones.
RF-33, RF-34, RF-35 y RF-36. Salida: pantalla, CSV y PDF."""

import csv
import io
from datetime import date

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    abort,
    send_file
)
from flask_login import login_required, current_user

from app.models import Categoria, Marca
from app.extensions import db
from app.modules.reportes import reportes_bp
from . import services
from .pdf import generar_pdf


# --- LISTAR REPORTES ---

@reportes_bp.route('/')
@login_required
def index():
    if current_user.rol != 'ADMIN':
        return redirect('/')

    return render_template(
        'reportes/index.html',
        descripciones=services.DESCRIPCIONES
    )


# --- VER / EXPORTAR REPORTE ---

@reportes_bp.route('/<tipo>')
@login_required
def ver(tipo):
    if current_user.rol != 'ADMIN':
        return redirect('/')

    if tipo not in services.REPORTES:
        abort(404)

    reporte = services.REPORTES[tipo](request.args)
    formato = request.args.get('formato', 'html')
    sello = date.today().strftime('%Y%m%d')

    if formato == 'csv':
        return _descargar_csv(tipo, sello, reporte)

    if formato == 'pdf':
        return _descargar_pdf(tipo, sello, reporte)

    args = request.args.to_dict()
    args.pop('formato', None)

    extra = {}

    if tipo == 'productos':
        extra = {
            'categorias': Categoria.query
                .order_by(Categoria.nombre)
                .all(),
            'marcas': Marca.query
                .order_by(Marca.nombre)
                .all()
        }

    return render_template(
        'reportes/reporte.html',
        tipo=tipo,
        rep=reporte,
        args=args,
        **extra
    )


# --- DESCARGAR CSV ---

def _descargar_csv(tipo, sello, reporte):
    buffer = io.StringIO()

    escritor = csv.writer(buffer, delimiter=';')

    escritor.writerow([reporte['titulo']])
    escritor.writerow([reporte['filtros']])
    escritor.writerow([])
    escritor.writerow(reporte['headers'])
    escritor.writerows(reporte['rows'])
    escritor.writerow([])

    for etiqueta, valor in reporte['totales']:
        escritor.writerow([etiqueta, valor])

    contenido = '\ufeff' + buffer.getvalue()

    return send_file(
        io.BytesIO(contenido.encode('utf-8-sig')),
        mimetype='text/csv; charset=utf-8',
        as_attachment=True,
        download_name=f'reporte_{tipo}_{sello}.csv'
    )


# --- DESCARGAR PDF ---

def _descargar_pdf(tipo, sello, reporte):
    contenido = generar_pdf(
        reporte,
        current_user.nombre_usuario
    )

    return send_file(
        io.BytesIO(contenido),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'reporte_{tipo}_{sello}.pdf'
    )