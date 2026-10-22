"""Exportação do histórico (mesmos filtros da tela de histórico)."""
import csv
import io
from datetime import datetime

from flask import Blueprint, Response, abort, request

from .painel import consultar_historico, login_obrigatorio

bp = Blueprint('relatorios', __name__, url_prefix='/painel/relatorios')

CABECALHO = ['Prontuário', 'Nome', 'Curso', 'Máquina', 'Entrada', 'Saída', 'Duração (min)']


def _linhas():
    for s in consultar_historico(request.args):
        yield [s['prontuario'], s['nome'], s['curso'], s['maquina'],
               s['entrada'], s['saida'] or '', s['minutos'] if s['minutos'] is not None else '']


def _download(conteudo, mimetype, extensao):
    nome = f'historico_{datetime.now():%Y%m%d_%H%M}.{extensao}'
    return Response(conteudo, mimetype=mimetype,
                    headers={'Content-Disposition': f'attachment; filename={nome}'})


def gerar_csv():
    saida = io.StringIO()
    # ';' e BOM UTF-8 para o Excel em português abrir direto, com acentos.
    escritor = csv.writer(saida, delimiter=';')
    escritor.writerow(CABECALHO)
    escritor.writerows(_linhas())
    return _download('﻿' + saida.getvalue(), 'text/csv; charset=utf-8', 'csv')


def gerar_xlsx():
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = 'Histórico'
    ws.append(CABECALHO)
    for celula in ws[1]:
        celula.font = Font(bold=True)
    for linha in _linhas():
        ws.append(linha)
    for coluna, largura in zip('ABCDEFG', (14, 32, 24, 16, 20, 20, 14)):
        ws.column_dimensions[coluna].width = largura
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions

    saida = io.BytesIO()
    wb.save(saida)
    return _download(saida.getvalue(),
                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx')


def gerar_pdf():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape

    linhas = list(_linhas())
    saida = io.BytesIO()
    doc = SimpleDocTemplate(saida, pagesize=landscape(A4), title='Histórico de uso',
                            leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    estilos = getSampleStyleSheet()
    filtros = ', '.join(f'{k}: {v}' for k, v in request.args.items() if v) or 'nenhum'
    tabela = Table([CABECALHO] + linhas, repeatRows=1)
    tabela.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dfe6ee')),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f7fa')]),
    ]))
    doc.build([
        Paragraph('Histórico de uso das máquinas', estilos['Title']),
        Paragraph(escape(f'Gerado em {datetime.now():%d/%m/%Y %H:%M} · Filtros: {filtros} · '
                         f'{len(linhas)} sessões'), estilos['Normal']),
        Spacer(1, 12),
        tabela,
    ])
    return _download(saida.getvalue(), 'application/pdf', 'pdf')


FORMATOS = {'csv': gerar_csv, 'xlsx': gerar_xlsx, 'pdf': gerar_pdf}


@bp.route('/historico.<formato>')
@login_obrigatorio
def historico(formato):
    if formato not in FORMATOS:
        abort(404)
    return FORMATOS[formato]()
