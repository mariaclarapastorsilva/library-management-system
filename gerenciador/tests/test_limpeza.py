from datetime import datetime, timedelta

import pytest

from app.db import conectar, criar_banco
from limpar_registros import limpar


def dias_atras(dias):
    return (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d %H:%M:%S')


@pytest.fixture
def con(tmp_path):
    caminho = str(tmp_path / 'limpeza.db')
    criar_banco(caminho)
    con = conectar(caminho)
    novo_usuario = lambda p, n: con.execute(  # noqa: E731
        "INSERT INTO usuarios (prontuario, nome, curso) VALUES (?, ?, 'Info')", (p, n)).lastrowid
    antiga, mista, recente = novo_usuario('JC1', 'Antiga'), novo_usuario('JC2', 'Mista'), novo_usuario('JC3', 'Recente')
    maquina = con.execute("INSERT INTO maquinas (identificador) VALUES ('PC')").lastrowid
    for usuario, dias in [(antiga, 500), (mista, 450), (mista, 30), (recente, 10)]:
        con.execute('INSERT INTO sessoes (usuario_id, maquina_id, entrada, saida) VALUES (?, ?, ?, ?)',
                    (usuario, maquina, dias_atras(dias), dias_atras(dias - 0.1)))
    con.commit()
    yield con
    con.close()


def nomes(con):
    return {r[0] for r in con.execute('SELECT nome FROM usuarios')}


def test_sem_confirmar_nao_altera_nada(con):
    limpar(con, 12, confirmar=False)
    assert con.execute('SELECT COUNT(*) FROM sessoes').fetchone()[0] == 4


def test_apaga_sessoes_antigas_e_alunos_sem_sessao(con):
    limpar(con, 12, confirmar=True)
    assert con.execute('SELECT COUNT(*) FROM sessoes').fetchone()[0] == 2
    assert nomes(con) == {'Mista', 'Recente'}


def test_sessao_aberta_antiga_gera_aviso_e_nao_e_apagada(con, capsys):
    usuario = con.execute("SELECT id FROM usuarios WHERE nome = 'Antiga'").fetchone()[0]
    con.execute("INSERT INTO sessoes (usuario_id, maquina_id, entrada) VALUES (?, 1, ?)",
                (usuario, dias_atras(400)))
    con.commit()
    limpar(con, 12, confirmar=True)
    assert 'continuam abertas' in capsys.readouterr().out
    assert 'Antiga' in nomes(con)


def test_rodar_de_novo_nao_faz_nada(con, capsys):
    limpar(con, 12, confirmar=True)
    limpar(con, 12, confirmar=True)
    assert ': 0 sessões de 0 alunos.' in capsys.readouterr().out.splitlines()[-1]
