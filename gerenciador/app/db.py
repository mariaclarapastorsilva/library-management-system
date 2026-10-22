import os
import sqlite3
from datetime import datetime

from flask import current_app, g

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCHEMA = os.path.join(BASE, 'database', 'schema.sql')
CAMINHO_PADRAO = os.path.join(BASE, 'database', 'biblioteca.db')
FORMATO_DATA = '%Y-%m-%d %H:%M:%S'


def conectar(caminho):
    con = sqlite3.connect(caminho, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con


def criar_banco(caminho):
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    con = conectar(caminho)
    try:
        with open(SCHEMA, encoding='utf-8') as f:
            con.executescript(f.read())
    finally:
        con.close()


def get_db():
    if 'db' not in g:
        g.db = conectar(current_app.config['DATABASE'])
    return g.db


def close_db(_erro=None):
    con = g.pop('db', None)
    if con is not None:
        con.close()


def agora():
    return datetime.now().strftime(FORMATO_DATA)


def init_app(app):
    criar_banco(app.config['DATABASE'])
    app.teardown_appcontext(close_db)
