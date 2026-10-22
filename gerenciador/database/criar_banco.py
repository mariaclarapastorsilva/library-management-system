"""Cria (ou atualiza) o banco SQLite a partir de schema.sql.

Uso: python database/criar_banco.py [caminho_do_banco]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app.db import CAMINHO_PADRAO, criar_banco  # noqa: E402

if __name__ == '__main__':
    caminho = sys.argv[1] if len(sys.argv) > 1 else CAMINHO_PADRAO
    criar_banco(caminho)
    print(f'Banco pronto em {os.path.abspath(caminho)}')
