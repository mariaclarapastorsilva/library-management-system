"""API usada pelos clientes das máquinas."""
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from .db import FORMATO_DATA, agora, get_db

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.before_request
def verificar_token():
    token = current_app.config['API_TOKEN']
    if token and request.headers.get('X-Token') != token:
        return jsonify(erro='token inválido'), 401


def _campos(dados, *nomes):
    return {n: str(dados.get(n) or '').strip() for n in nomes}


def _horario(valor):
    """Horário enviado pelo cliente (eventos da fila offline) ou o horário atual.

    Retorna None se o valor vier num formato inválido.
    """
    if not valor:
        return agora()
    try:
        return datetime.strptime(str(valor), FORMATO_DATA).strftime(FORMATO_DATA)
    except ValueError:
        return None


@bp.post('/login')
def login():
    dados = request.get_json(silent=True) or {}
    campos = _campos(dados, 'prontuario', 'nome', 'curso', 'maquina')
    faltando = [n for n, v in campos.items() if not v]
    if faltando:
        return jsonify(erro='campos obrigatórios: ' + ', '.join(faltando)), 400
    entrada = _horario(dados.get('horario'))
    if entrada is None:
        return jsonify(erro='horario deve estar no formato AAAA-MM-DD HH:MM:SS'), 400

    db = get_db()
    maquina = db.execute('SELECT id, ativa FROM maquinas WHERE identificador = ?',
                         (campos['maquina'],)).fetchone()
    if maquina is None:
        # Máquina nova se cadastra sozinha; o admin pode desativá-la no painel.
        maquina_id = db.execute('INSERT INTO maquinas (identificador) VALUES (?)',
                                (campos['maquina'],)).lastrowid
    elif not maquina['ativa']:
        return jsonify(erro='máquina desativada no painel'), 403
    else:
        maquina_id = maquina['id']

    prontuario = campos['prontuario'].upper()
    db.execute('''INSERT INTO usuarios (prontuario, nome, curso) VALUES (?, ?, ?)
                  ON CONFLICT(prontuario) DO UPDATE
                  SET nome = excluded.nome, curso = excluded.curso''',
               (prontuario, campos['nome'], campos['curso']))
    usuario_id = db.execute('SELECT id FROM usuarios WHERE prontuario = ?',
                            (prontuario,)).fetchone()['id']

    # Sessão que ficou aberta nesta máquina (ex.: queda de energia) é fechada agora.
    db.execute('''UPDATE sessoes SET saida = ?
                  WHERE maquina_id = ? AND saida IS NULL AND entrada <= ?''',
               (entrada, maquina_id, entrada))
    sessao_id = db.execute('INSERT INTO sessoes (usuario_id, maquina_id, entrada) VALUES (?, ?, ?)',
                           (usuario_id, maquina_id, entrada)).lastrowid
    db.commit()
    return jsonify(sessao_id=sessao_id, entrada=entrada), 201


@bp.post('/logout')
def logout():
    dados = request.get_json(silent=True) or {}
    maquina = _campos(dados, 'maquina')['maquina']
    if not maquina:
        return jsonify(erro='campo obrigatório: maquina'), 400
    saida = _horario(dados.get('horario'))
    if saida is None:
        return jsonify(erro='horario deve estar no formato AAAA-MM-DD HH:MM:SS'), 400

    db = get_db()
    cur = db.execute('''UPDATE sessoes SET saida = ?
                        WHERE saida IS NULL AND entrada <= ?
                          AND maquina_id = (SELECT id FROM maquinas WHERE identificador = ?)''',
                     (saida, saida, maquina))
    db.commit()
    if cur.rowcount == 0:
        return jsonify(erro='nenhuma sessão aberta nesta máquina'), 404
    return jsonify(saida=saida, encerradas=cur.rowcount)
