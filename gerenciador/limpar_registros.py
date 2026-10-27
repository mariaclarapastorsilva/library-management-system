"""Remove dados pessoais de sessões antigas (prazo de guarda da LGPD).

Uso:
    python limpar_registros.py --meses 12 --modo anonimizar             (só mostra o que faria)
    python limpar_registros.py --meses 12 --modo anonimizar --confirmar

Modos:
    anonimizar  mantém as sessões (curso, máquina, horários) para estatísticas,
                mas troca o aluno por um registro "Anônimo" do mesmo curso.
    apagar      apaga as sessões por completo.

Só afeta sessões já encerradas com entrada anterior ao prazo; sessões abertas há
mais tempo que o prazo geram um aviso para serem encerradas no painel. Alunos que
ficarem sem nenhuma sessão são apagados. Rode um backup antes da primeira execução real.
"""
import argparse
import os

from app.db import CAMINHO_PADRAO, conectar

PREFIXO_ANONIMO = 'ANONIMO:'

FILTRO_ANTIGAS = "saida IS NOT NULL AND entrada < date('now', 'localtime', ?)"


def limpar(con, meses, modo, confirmar):
    prazo = f'-{meses} months'
    corte = con.execute("SELECT date('now', 'localtime', ?)", (prazo,)).fetchone()[0]
    # Sessões já anonimizadas não contam: não há mais dado pessoal nelas.
    antigas = f'''FROM sessoes WHERE {FILTRO_ANTIGAS}
                  AND usuario_id NOT IN (SELECT id FROM usuarios WHERE prontuario LIKE '{PREFIXO_ANONIMO}%')'''
    total = con.execute('SELECT COUNT(*) ' + antigas, (prazo,)).fetchone()[0]
    alunos = con.execute('SELECT COUNT(DISTINCT usuario_id) ' + antigas, (prazo,)).fetchone()[0]
    print(f'Prazo: {meses} meses. Sessões encerradas com entrada antes de {corte}: '
          f'{total} sessões de {alunos} alunos.')
    abandonadas = con.execute("SELECT COUNT(*) FROM sessoes WHERE saida IS NULL AND entrada < ?",
                              (corte,)).fetchone()[0]
    if abandonadas:
        print(f'Atenção: {abandonadas} sessões continuam abertas desde antes de {corte} e não serão '
              'tratadas. Encerre-as no painel (Sessões ativas) e rode a limpeza de novo.')
    if not total:
        return
    if not confirmar:
        print(f'Nada foi alterado. Para {modo} de verdade, rode de novo com --confirmar.')
        return

    if modo == 'anonimizar':
        con.execute(f'''INSERT OR IGNORE INTO usuarios (prontuario, nome, curso)
                        SELECT DISTINCT '{PREFIXO_ANONIMO}' || u.curso, 'Anônimo', u.curso
                        FROM usuarios u
                        WHERE u.id IN (SELECT usuario_id FROM sessoes WHERE {FILTRO_ANTIGAS})''', (prazo,))
        con.execute(f'''UPDATE sessoes SET usuario_id = (
                            SELECT a.id FROM usuarios a, usuarios u
                            WHERE u.id = sessoes.usuario_id AND a.prontuario = '{PREFIXO_ANONIMO}' || u.curso)
                        WHERE {FILTRO_ANTIGAS}''', (prazo,))
    else:
        con.execute(f'DELETE FROM sessoes WHERE {FILTRO_ANTIGAS}', (prazo,))

    removidos = con.execute(f'''DELETE FROM usuarios
                               WHERE prontuario NOT LIKE '{PREFIXO_ANONIMO}%'
                                 AND id NOT IN (SELECT usuario_id FROM sessoes)''').rowcount
    con.commit()
    # Reescreve o arquivo para que os dados apagados não fiquem em páginas livres do banco.
    con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    con.execute('VACUUM')
    print(f'Feito ({modo}): {total} sessões tratadas, {removidos} alunos removidos do cadastro.')


if __name__ == '__main__':
    args = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    args.add_argument('--meses', type=int, required=True, help='prazo de guarda em meses')
    args.add_argument('--modo', choices=['anonimizar', 'apagar'], required=True)
    args.add_argument('--confirmar', action='store_true', help='aplica a limpeza (sem isso, só mostra)')
    opcoes = args.parse_args()
    if opcoes.meses < 1:
        args.error('--meses precisa ser pelo menos 1')

    con = conectar(os.environ.get('DATABASE', CAMINHO_PADRAO))
    try:
        limpar(con, opcoes.meses, opcoes.modo, opcoes.confirmar)
    finally:
        con.close()
