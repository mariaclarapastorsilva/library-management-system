import io

from openpyxl import load_workbook

from conftest import api_login, api_logout


def preparar(admin):
    api_login(admin, horario='2026-01-10 08:00:00')
    api_logout(admin, horario='2026-01-10 09:30:00')
    api_login(admin, prontuario='JC2', nome='Bruno', curso='Mecânica', maquina='PC-02',
              horario='2026-02-20 08:00:00')


def test_csv(admin):
    preparar(admin)
    r = admin.get('/painel/relatorios/historico.csv')
    assert r.data.startswith('﻿'.encode())  # BOM: o Excel abre com acentos
    linhas = r.data.decode('utf-8-sig').splitlines()
    assert linhas[0].startswith('Prontuário;Nome;Curso')
    assert 'JC123;Ana;Informática;PC-01;2026-01-10 08:00:00;2026-01-10 09:30:00;90' in linhas
    assert len(linhas) == 3


def test_csv_respeita_filtros(admin):
    preparar(admin)
    r = admin.get('/painel/relatorios/historico.csv', query_string={'curso': 'Mecânica'})
    linhas = r.data.decode('utf-8-sig').splitlines()
    assert len(linhas) == 2 and 'Bruno' in linhas[1]


def test_xlsx(admin):
    preparar(admin)
    planilha = load_workbook(io.BytesIO(admin.get('/painel/relatorios/historico.xlsx').data)).active
    linhas = list(planilha.values)
    assert linhas[0][0] == 'Prontuário'
    assert ('JC123', 'Ana', 'Informática', 'PC-01', '2026-01-10 08:00:00', '2026-01-10 09:30:00', 90) in linhas


def test_pdf(admin):
    preparar(admin)
    r = admin.get('/painel/relatorios/historico.pdf')
    assert r.mimetype == 'application/pdf'
    assert r.data.startswith(b'%PDF')


def test_formato_desconhecido(admin):
    assert admin.get('/painel/relatorios/historico.doc').status_code == 404
