"""Cópia consistente do banco (funciona com o servidor rodando).

Uso: python backup.py [pasta_destino] [quantidade_a_manter]
Agende no Agendador de Tarefas do Windows (ver README).
"""
import glob
import os
import sqlite3
import sys
from datetime import datetime

from app.db import BASE, CAMINHO_PADRAO

if __name__ == '__main__':
    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, 'backups')
    manter = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    os.makedirs(destino, exist_ok=True)

    origem = sqlite3.connect(os.environ.get('DATABASE', CAMINHO_PADRAO))
    arquivo = os.path.join(destino, f'biblioteca_{datetime.now():%Y%m%d_%H%M%S}.db')
    copia = sqlite3.connect(arquivo)
    origem.backup(copia)
    copia.close()
    origem.close()
    print(f'Backup salvo em {arquivo}')

    for antigo in sorted(glob.glob(os.path.join(destino, 'biblioteca_*.db')))[:-manter]:
        os.remove(antigo)
