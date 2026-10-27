"""Apaga sessões mais antigas que o prazo de guarda dos dados (LGPD).

Uso:
    python limpar_registros.py --meses 12              (só mostra o que faria)
    python limpar_registros.py --meses 12 --confirmar

Cada registro é mantido completo (nome, curso, prontuário, máquina e horários) ou
apagado por inteiro: não há guarda parcial. Só afeta sessões já encerradas com
entrada anterior ao prazo; sessões abertas há mais tempo que o prazo geram um aviso
para serem encerradas no painel. Alunos que ficarem sem nenhuma sessão também são
apagados. Rode um backup antes da primeira execução real.
"""
import argparse
import os

from app.db import CAMINHO_PADRAO, conectar

ANTIGAS = "FROM sessoes WHERE saida IS NOT NULL AND entrada < ?"


def limpar(con, meses, confirmar):
    corte = con.execute("SELECT date('now', 'localtime', ?)", (f'-{meses} months',)).fetchone()[0]
    total, alunos = con.execute('SELECT COUNT(*), COUNT(DISTINCT usuario_id) ' + ANTIGAS,
                                (corte,)).fetchone()
    print(f'Prazo: {meses} meses. Sessões encerradas com entrada antes de {corte}: '
          f'{total} sessões de {alunos} alunos.')
    abandonadas = con.execute('SELECT COUNT(*) FROM sessoes WHERE saida IS NULL AND entrada < ?',
                              (corte,)).fetchone()[0]
    if abandonadas:
        print(f'Atenção: {abandonadas} sessões continuam abertas desde antes de {corte} e não serão '
              'apagadas. Encerre-as no painel (Sessões ativas) e rode a limpeza de novo.')
    if not total:
        return
    if not confirmar:
        print('Nada foi alterado. Para apagar de verdade, rode de novo com --confirmar.')
        return

    con.execute('DELETE ' + ANTIGAS, (corte,))
    removidos = con.execute('DELETE FROM usuarios WHERE id NOT IN (SELECT usuario_id FROM sessoes)').rowcount
    con.commit()
    # Reescreve o arquivo para que os dados apagados não fiquem em páginas livres do banco.
    con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    con.execute('VACUUM')
    print(f'Feito: {total} sessões apagadas, {removidos} alunos removidos do cadastro.')


if __name__ == '__main__':
    args = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    args.add_argument('--meses', type=int, required=True, help='prazo de guarda em meses')
    args.add_argument('--confirmar', action='store_true', help='apaga de verdade (sem isso, só mostra)')
    opcoes = args.parse_args()
    if opcoes.meses < 1:
        args.error('--meses precisa ser pelo menos 1')

    con = conectar(os.environ.get('DATABASE', CAMINHO_PADRAO))
    try:
        limpar(con, opcoes.meses, opcoes.confirmar)
    finally:
        con.close()
