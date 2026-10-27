import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.db import conectar

SENHA_ADMIN = 'senha-de-teste'


@pytest.fixture
def caminho_db(tmp_path):
    return str(tmp_path / 'teste.db')


@pytest.fixture
def criar(monkeypatch, caminho_db):
    """Fábrica de apps de teste; cada teste usa um banco novo e vazio."""
    # Sem isso, create_app gravaria uma chave em gerenciador/instance/.
    monkeypatch.setenv('SECRET_KEY', 'teste')

    def _criar(**config):
        return create_app({'TESTING': True, 'DATABASE': caminho_db, 'API_TOKEN': '', **config})
    return _criar


@pytest.fixture
def app(criar):
    return criar()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app, caminho_db):
    con = conectar(caminho_db)
    yield con
    con.close()


@pytest.fixture
def criar_admin(db):
    def _criar(usuario='admin', senha=SENHA_ADMIN):
        db.execute('INSERT INTO administradores (usuario, senha_hash) VALUES (?, ?)',
                   (usuario, generate_password_hash(senha)))
        db.commit()
    return _criar


@pytest.fixture
def admin(client, criar_admin):
    """Cliente HTTP já logado no painel."""
    criar_admin()
    client.post('/painel/login', data={'usuario': 'admin', 'senha': SENHA_ADMIN})
    return client


DADOS_LOGIN = {'prontuario': 'jc123', 'nome': 'Ana', 'curso': 'Informática', 'maquina': 'PC-01'}


def api_login(client, **extra):
    return client.post('/api/login', json={**DADOS_LOGIN, **extra})


def api_logout(client, **extra):
    return client.post('/api/logout', json={'maquina': 'PC-01', **extra})
