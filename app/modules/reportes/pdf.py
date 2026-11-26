"""Genera el PDF de un reporte con reportlab."""
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer


def generar_pdf(rep, usuario=''):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1.5 * cm,
                            rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            title=rep['titulo'])
    estilos = getSampleStyleSheet()
    celda = ParagraphStyle('celda', parent=estilos['BodyText'], fontSize=8, leading=10)
    celda_num = ParagraphStyle('celda_num', parent=celda, alignment=2)
    cabecera = ParagraphStyle('cab', parent=celda, textColor=colors.white,
                              fontName='Helvetica-Bold')

    def p(texto, estilo=celda):
        return Paragraph(escape(str(texto)), estilo)

    elementos = [
        Paragraph(escape('Titan Computers'), estilos['Heading3']),
        Paragraph(escape(rep['titulo']), estilos['Title']),
        Paragraph(escape(f"Filtros: {rep['filtros']}"), estilos['Normal']),
        Paragraph(escape(f"Generado el {datetime.now():%d/%m/%Y %H:%M}"
                         + (f' por {usuario}' if usuario else '')), estilos['Normal']),
        Spacer(1, 0.4 * cm),
    ]

    headers, rows, num_cols = rep['headers'], rep['rows'], rep.get('num_cols', set())
    if rows:
        datos = [[p(h, cabecera) for h in headers]]
        for fila in rows:
            datos.append([p(v, celda_num if i in num_cols else celda) for i, v in enumerate(fila)])
        # ancho de columnas proporcional al contenido
        pesos = []
        for i, h in enumerate(headers):
            largo = max([len(str(h))] + [len(str(f[i])) for f in rows[:80]])
            pesos.append(min(max(largo, 6), 40))
        ancho = doc.width
        anchos = [ancho * w / sum(pesos) for w in pesos]
        tabla = Table(datos, colWidths=anchos, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b3a4a')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f6f9')]),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#c8ced6')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elementos.append(tabla)
    else:
        elementos.append(Paragraph('No hay datos para los filtros seleccionados.', estilos['Normal']))

    elementos.append(Spacer(1, 0.5 * cm))
    for etiqueta, valor in rep['totales']:
        elementos.append(Paragraph(f'<b>{escape(str(etiqueta))}:</b> {escape(str(valor))}',
                                   estilos['Normal']))

    def pie(canvas, documento):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(landscape(A4)[0] - 1.5 * cm, 0.8 * cm, f'Página {documento.page}')
        canvas.restoreState()

    doc.build(elementos, onFirstPage=pie, onLaterPages=pie)
    return buffer.getvalue()
