"""Servidor de produção (waitress). Uso: python servir.py

Variáveis de ambiente opcionais: HOST (padrão 0.0.0.0), PORT (5000),
DATABASE, SECRET_KEY e API_TOKEN.
"""
import os

from waitress import serve

from app import create_app

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    porta = int(os.environ.get('PORT', 5000))
    print(f'Servindo em http://{host}:{porta}')
    serve(create_app(), host=host, port=porta, threads=8)
