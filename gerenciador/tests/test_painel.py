import pytest

from conftest import SENHA_ADMIN, api_login


@pytest.mark.parametrize('url', ['/painel/', '/painel/historico', '/painel/maquinas', '/painel/senha',
                                 '/painel/relatorios/historico.csv'])
def test_paginas_exigem_login(client, url):
    r = client.get(url)
    assert r.status_code == 302
    assert r.headers['Location'].startswith('/painel/login')


def test_login_do_admin(client, criar_admin):
    criar_admin()
    r = client.post('/painel/login', data={'usuario': 'admin', 'senha': 'errada'})
    assert 'inválidos' in r.get_data(as_text=True)
    r = client.post('/painel/login', data={'usuario': 'admin', 'senha': SENHA_ADMIN})
    assert r.headers['Location'] == '/painel/'


def test_login_so_redireciona_para_dentro_do_painel(client, criar_admin):
    criar_admin()
    r = client.post('/painel/login?proximo=https://site-externo.com/',
                    data={'usuario': 'admin', 'senha': SENHA_ADMIN})
    assert r.headers['Location'] == '/painel/'


def test_sessoes_ativas_e_encerrar(admin, db):
    api_login(admin)
    assert 'Sessões ativas (1)' in admin.get('/painel/').get_data(as_text=True)
    sessao_id = db.execute('SELECT id FROM sessoes').fetchone()[0]
    admin.post(f'/painel/sessoes/{sessao_id}/encerrar')
    assert 'Sessões ativas (0)' in admin.get('/painel/').get_data(as_text=True)


def test_filtros_do_historico(admin):
    api_login(admin, nome='Ana', curso='Informática', maquina='PC-01', horario='2026-01-10 08:00:00')
    api_login(admin, prontuario='JC2', nome='Bruno', curso='Mecânica', maquina='PC-02',
              horario='2026-02-20 08:00:00')

    def nomes(filtros):
        html = admin.get('/painel/historico', query_string=filtros).get_data(as_text=True)
        return {n for n in ('Ana', 'Bruno') if f'<td>{n}</td>' in html}

    assert nomes({}) == {'Ana', 'Bruno'}
    assert nomes({'inicio': '2026-02-01'}) == {'Bruno'}
    assert nomes({'fim': '2026-01-31'}) == {'Ana'}
    assert nomes({'busca': 'bru'}) == {'Bruno'}
    assert nomes({'curso': 'Informática'}) == {'Ana'}
    assert nomes({'maquina': 'PC-02'}) == {'Bruno'}


def test_texto_dos_alunos_e_escapado(admin):
    api_login(admin, nome='<script>alert(1)</script>')
    html = admin.get('/painel/historico').get_data(as_text=True)
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html


def test_cadastro_e_desativacao_de_maquina(admin, db):
    admin.post('/painel/maquinas', data={'identificador': 'PC-10', 'descricao': 'Bancada 1'})
    maquina = db.execute("SELECT id, descricao, ativa FROM maquinas WHERE identificador = 'PC-10'").fetchone()
    assert (maquina['descricao'], maquina['ativa']) == ('Bancada 1', 1)
    admin.post(f'/painel/maquinas/{maquina["id"]}/alternar')
    assert db.execute('SELECT ativa FROM maquinas WHERE id = ?', (maquina['id'],)).fetchone()[0] == 0


def test_trocar_senha(admin, criar_admin, app):
    criar_admin('outro')

    def trocar(atual, nova, confirmacao):
        return admin.post('/painel/senha', data={'atual': atual, 'nova': nova, 'confirmacao': confirmacao},
                          follow_redirects=True).get_data(as_text=True)

    assert 'incorreta' in trocar('errada', 'nova-senha-1', 'nova-senha-1')
    assert 'pelo menos 8' in trocar(SENHA_ADMIN, 'curta', 'curta')
    assert 'não confere' in trocar(SENHA_ADMIN, 'nova-senha-1', 'outra-senha-1')
    assert 'Senha alterada' in trocar(SENHA_ADMIN, 'nova-senha-1', 'nova-senha-1')

    def entra(usuario, senha):
        r = app.test_client().post('/painel/login', data={'usuario': usuario, 'senha': senha})
        return r.status_code == 302

    assert not entra('admin', SENHA_ADMIN)
    assert entra('admin', 'nova-senha-1')
    assert entra('outro', SENHA_ADMIN)
