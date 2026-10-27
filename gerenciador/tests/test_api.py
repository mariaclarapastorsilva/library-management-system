from conftest import api_login, api_logout


def test_login_cria_usuario_maquina_e_sessao(client, db):
    r = api_login(client)
    assert r.status_code == 201
    assert tuple(db.execute('SELECT prontuario, nome, curso FROM usuarios').fetchone()) == \
        ('JC123', 'Ana', 'Informática')
    assert db.execute('SELECT identificador FROM maquinas').fetchone()[0] == 'PC-01'
    assert db.execute('SELECT saida FROM sessoes').fetchone()[0] is None


def test_login_exige_todos_os_campos(client):
    r = client.post('/api/login', json={})
    assert r.status_code == 400
    for campo in ('prontuario', 'nome', 'curso', 'maquina'):
        assert campo in r.get_json()['erro']


def test_login_recusa_horario_invalido(client):
    assert api_login(client, horario='ontem').status_code == 400


def test_login_atualiza_nome_e_curso(client, db):
    api_login(client)
    api_login(client, nome='Ana Souza', curso='Mecânica', maquina='PC-02')
    assert db.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0] == 1
    assert tuple(db.execute('SELECT nome, curso FROM usuarios').fetchone()) == ('Ana Souza', 'Mecânica')


def test_novo_login_fecha_sessao_aberta_na_mesma_maquina(client, db):
    api_login(client, horario='2026-01-10 08:00:00')
    api_login(client, prontuario='JC999', nome='Bruno', horario='2026-01-10 09:00:00')
    sessoes = db.execute('SELECT entrada, saida FROM sessoes ORDER BY id').fetchall()
    assert tuple(sessoes[0]) == ('2026-01-10 08:00:00', '2026-01-10 09:00:00')
    assert sessoes[1]['saida'] is None


def test_maquina_desativada_recusa_login(client, db):
    api_login(client)
    db.execute('UPDATE maquinas SET ativa = 0')
    db.commit()
    assert api_login(client).status_code == 403


def test_logout_fecha_a_sessao(client, db):
    api_login(client)
    assert api_logout(client).status_code == 200
    assert db.execute('SELECT saida FROM sessoes').fetchone()[0] is not None


def test_logout_sem_sessao_aberta(client):
    assert api_logout(client).status_code == 404


def test_logout_exige_maquina(client):
    assert client.post('/api/logout', json={}).status_code == 400


def test_eventos_da_fila_offline_guardam_o_horario_real(client, db):
    api_login(client, horario='2026-01-10 08:00:00')
    api_logout(client, horario='2026-01-10 09:30:00')
    assert tuple(db.execute('SELECT entrada, saida FROM sessoes').fetchone()) == \
        ('2026-01-10 08:00:00', '2026-01-10 09:30:00')


def test_logout_anterior_a_entrada_nao_fecha_a_sessao(client):
    api_login(client, horario='2026-01-10 08:00:00')
    assert api_logout(client, horario='2026-01-10 07:00:00').status_code == 404


def test_token_da_api(criar):
    client = criar(API_TOKEN='segredo').test_client()
    assert api_login(client).status_code == 401
    assert client.post('/api/login', json={}, headers={'X-Token': 'errado'}).status_code == 401
    r = client.post('/api/login', json={'prontuario': 'JC1', 'nome': 'A', 'curso': 'B', 'maquina': 'C'},
                    headers={'X-Token': 'segredo'})
    assert r.status_code == 201
