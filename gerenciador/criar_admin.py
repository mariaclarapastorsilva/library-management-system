"""Cria um administrador do painel ou troca a senha de um existente.

Uso: python criar_admin.py <usuario>
"""
import getpass
import os
import sys

from werkzeug.security import generate_password_hash

from app.db import CAMINHO_PADRAO, conectar, criar_banco

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    usuario = sys.argv[1].strip()
    senha = getpass.getpass('Senha: ')
    if len(senha) < 8:
        sys.exit('A senha precisa ter pelo menos 8 caracteres.')
    if senha != getpass.getpass('Repita a senha: '):
        sys.exit('As senhas não conferem.')

    caminho = os.environ.get('DATABASE', CAMINHO_PADRAO)
    criar_banco(caminho)
    con = conectar(caminho)
    con.execute('''INSERT INTO administradores (usuario, senha_hash) VALUES (?, ?)
                   ON CONFLICT(usuario) DO UPDATE SET senha_hash = excluded.senha_hash''',
                (usuario, generate_password_hash(senha)))
    con.commit()
    con.close()
    print(f'Administrador "{usuario}" salvo.')
