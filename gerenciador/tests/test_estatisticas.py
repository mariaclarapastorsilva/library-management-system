import re

from app.db import conectar
from conftest import api_login, api_logout
from demo import gerar


def test_estatisticas_exige_login(client):
    assert client.get('/painel/estatisticas/').headers['Location'].startswith('/painel/login')


def test_periodo_sem_sessoes(admin):
    html = admin.get('/painel/estatisticas/?inicio=2020-01-01&fim=2020-01-31').get_data(as_text=True)
    assert 'Nenhuma sessão entre 01/01/2020 e 31/01/2020' in html


def test_totais_e_agrupamentos(admin):
    # Segunda, 12/01/2026: Ana usa 90 min às 8h; terça: Bruno usa 30 min às 14h e ainda há uma sessão aberta.
    api_login(admin, horario='2026-01-12 08:00:00')
    api_logout(admin, horario='2026-01-12 09:30:00')
    api_login(admin, prontuario='JC2', nome='Bruno', curso='Mecânica', maquina='PC-02', horario='2026-01-13 14:00:00')
    api_logout(admin, maquina='PC-02', horario='2026-01-13 14:30:00')
    api_login(admin, prontuario='JC2', nome='Bruno', curso='Mecânica', maquina='PC-02', horario='2026-01-13 15:00:00')

    html = admin.get('/painel/estatisticas/?inicio=2026-01-12&fim=2026-01-13').get_data(as_text=True)
    cartoes = re.findall(r'<div class="valor">([^<]+)</div><div class="rotulo">([^<]+)</div>', html)
    assert cartoes == [('3', 'sessões'), ('2', 'alunos diferentes'), ('2 h', 'de uso no total'),
                       ('60 min', 'duração média por sessão')]
    assert 'title="12/01: 1 sessões"' in html and 'title="13/01: 2 sessões"' in html
    assert 'title="8h: 1 sessões iniciadas"' in html and 'title="14h: 1 sessões iniciadas"' in html
    assert 'title="Seg: 1 sessões"' in html and 'title="Ter: 2 sessões"' in html
    assert '<td>Informática</td><td>1</td><td>1</td><td>2</td>' in html  # 90 min arredonda para 2 h
    assert '<td>Mecânica</td><td>2</td><td>1</td><td>0</td>' in html


def test_datas_invalidas_usam_o_padrao(admin):
    assert admin.get('/painel/estatisticas/?inicio=abc&fim=').status_code == 200


def test_gerador_da_demonstracao(tmp_path):
    caminho = str(tmp_path / 'demo.db')
    total = gerar(caminho, semanas=2)
    con = conectar(caminho)
    assert total > 100
    assert con.execute('SELECT COUNT(*) FROM sessoes').fetchone()[0] == total
    assert con.execute("SELECT COUNT(*) FROM administradores WHERE usuario = 'demo'").fetchone()[0] == 1
    # Ninguém usa duas máquinas ao mesmo tempo entre as sessões em andamento.
    abertas = [r[0] for r in con.execute('SELECT usuario_id FROM sessoes WHERE saida IS NULL')]
    assert len(abertas) == len(set(abertas))
    # Nenhuma sessão começa no futuro nem termina antes de começar.
    assert con.execute("SELECT COUNT(*) FROM sessoes WHERE entrada > datetime('now', 'localtime') "
                       "OR saida < entrada").fetchone()[0] == 0
    # Domingo não tem uso.
    assert con.execute("SELECT COUNT(*) FROM sessoes WHERE strftime('%w', entrada) = '0'").fetchone()[0] == 0
