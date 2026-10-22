import os
import secrets

from flask import Flask, redirect, url_for

from . import db


def _chave_secreta():
    """Usa SECRET_KEY do ambiente ou gera uma e guarda em instance/secret.key."""
    if os.environ.get('SECRET_KEY'):
        return os.environ['SECRET_KEY']
    caminho = os.path.join(db.BASE, 'instance', 'secret.key')
    if not os.path.exists(caminho):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w') as f:
            f.write(secrets.token_hex(32))
    with open(caminho) as f:
        return f.read().strip()


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=_chave_secreta(),
        DATABASE=os.environ.get('DATABASE', db.CAMINHO_PADRAO),
        # Se definido, os clientes precisam enviar o cabeçalho X-Token com este valor.
        API_TOKEN=os.environ.get('API_TOKEN', ''),
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_HTTPONLY=True,
    )
    if config:
        app.config.update(config)

    db.init_app(app)

    from .api import bp as api_bp
    from .painel import bp as painel_bp
    from .relatorios import bp as relatorios_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(painel_bp)
    app.register_blueprint(relatorios_bp)

    @app.template_filter('duracao')
    def duracao(minutos):
        if minutos is None:
            return '—'
        return f'{minutos // 60}h {minutos % 60:02d}min'

    @app.route('/')
    def inicio():
        return redirect(url_for('painel.ativas'))

    return app
