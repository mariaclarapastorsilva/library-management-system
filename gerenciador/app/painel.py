"""Painel web do administrador."""
from functools import wraps

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import agora, get_db

bp = Blueprint('painel', __name__, url_prefix='/painel')

CONSULTA_SESSOES = '''
    SELECT s.id, s.entrada, s.saida, u.prontuario, u.nome, u.curso,
           m.identificador AS maquina, m.descricao AS maquina_descricao,
           CASE WHEN s.saida IS NULL THEN NULL
                ELSE CAST(round((julianday(s.saida) - julianday(s.entrada)) * 1440) AS INTEGER)
           END AS minutos
    FROM sessoes s
    JOIN usuarios u ON u.id = s.usuario_id
    JOIN maquinas m ON m.id = s.maquina_id
'''


def consultar_historico(args, limite=None):
    """Sessões filtradas pelos parâmetros da URL (usado também pelos relatórios)."""
    where, params = [], []
    if args.get('inicio'):
        where.append('s.entrada >= ?')
        params.append(args['inicio'] + ' 00:00:00')
    if args.get('fim'):
        where.append('s.entrada <= ?')
        params.append(args['fim'] + ' 23:59:59')
    if args.get('busca'):
        where.append('(u.prontuario LIKE ? OR u.nome LIKE ?)')
        params += ['%' + args['busca'] + '%'] * 2
    if args.get('curso'):
        where.append('u.curso = ?')
        params.append(args['curso'])
    if args.get('maquina'):
        where.append('m.identificador = ?')
        params.append(args['maquina'])

    sql = CONSULTA_SESSOES
    if where:
        sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY s.entrada DESC'
    if limite:
        sql += f' LIMIT {int(limite)}'
    return get_db().execute(sql, params).fetchall()


def login_obrigatorio(view):
    @wraps(view)
    def interna(*args, **kwargs):
        if g.admin is None:
            return redirect(url_for('painel.login', proximo=request.path))
        return view(*args, **kwargs)
    return interna


@bp.before_app_request
def carregar_admin():
    admin_id = session.get('admin_id')
    g.admin = None
    if admin_id is not None:
        g.admin = get_db().execute('SELECT id, usuario FROM administradores WHERE id = ?',
                                   (admin_id,)).fetchone()


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        admin = get_db().execute('SELECT * FROM administradores WHERE usuario = ?',
                                 (request.form.get('usuario', '').strip(),)).fetchone()
        if admin and check_password_hash(admin['senha_hash'], request.form.get('senha', '')):
            session.clear()
            session['admin_id'] = admin['id']
            proximo = request.args.get('proximo', '')
            # Só redireciona para caminhos internos do painel.
            if not proximo.startswith('/painel/'):
                proximo = url_for('painel.ativas')
            return redirect(proximo)
        flash('Usuário ou senha inválidos.', 'erro')
    return render_template('login.html')


@bp.route('/senha', methods=['GET', 'POST'])
@login_obrigatorio
def trocar_senha():
    if request.method == 'POST':
        db = get_db()
        atual = db.execute('SELECT senha_hash FROM administradores WHERE id = ?',
                           (g.admin['id'],)).fetchone()['senha_hash']
        nova = request.form.get('nova', '')
        if not check_password_hash(atual, request.form.get('atual', '')):
            flash('A senha atual está incorreta.', 'erro')
        elif len(nova) < 8:
            flash('A nova senha precisa ter pelo menos 8 caracteres.', 'erro')
        elif nova != request.form.get('confirmacao', ''):
            flash('A confirmação não confere com a nova senha.', 'erro')
        else:
            db.execute('UPDATE administradores SET senha_hash = ? WHERE id = ?',
                       (generate_password_hash(nova), g.admin['id']))
            db.commit()
            flash('Senha alterada.', 'ok')
            return redirect(url_for('painel.ativas'))
    return render_template('senha.html')


@bp.post('/sair')
def sair():
    session.clear()
    return redirect(url_for('painel.login'))


@bp.route('/')
@login_obrigatorio
def ativas():
    sessoes = get_db().execute(CONSULTA_SESSOES + ' WHERE s.saida IS NULL ORDER BY s.entrada').fetchall()
    return render_template('ativas.html', sessoes=sessoes)


@bp.post('/sessoes/<int:sessao_id>/encerrar')
@login_obrigatorio
def encerrar_sessao(sessao_id):
    db = get_db()
    db.execute('UPDATE sessoes SET saida = ? WHERE id = ? AND saida IS NULL', (agora(), sessao_id))
    db.commit()
    flash('Sessão encerrada.', 'ok')
    return redirect(url_for('painel.ativas'))


@bp.route('/historico')
@login_obrigatorio
def historico():
    db = get_db()
    limite = 500
    sessoes = consultar_historico(request.args, limite=limite)
    cursos = [r[0] for r in db.execute('SELECT DISTINCT curso FROM usuarios ORDER BY curso')]
    maquinas = [r[0] for r in db.execute('SELECT identificador FROM maquinas ORDER BY identificador')]
    return render_template('historico.html', sessoes=sessoes, cursos=cursos, maquinas=maquinas,
                           filtros=request.args, limite=limite)


@bp.route('/maquinas', methods=['GET', 'POST'])
@login_obrigatorio
def maquinas():
    db = get_db()
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        descricao = request.form.get('descricao', '').strip()
        if not identificador:
            flash('Informe o identificador (hostname) da máquina.', 'erro')
        else:
            db.execute('''INSERT INTO maquinas (identificador, descricao) VALUES (?, ?)
                          ON CONFLICT(identificador) DO UPDATE SET descricao = excluded.descricao''',
                       (identificador, descricao))
            db.commit()
            flash(f'Máquina {identificador} salva.', 'ok')
        return redirect(url_for('painel.maquinas'))

    lista = db.execute('''
        SELECT m.*, COUNT(s.id) AS total_sessoes,
               SUM(CASE WHEN s.id IS NOT NULL AND s.saida IS NULL THEN 1 ELSE 0 END) AS em_uso
        FROM maquinas m LEFT JOIN sessoes s ON s.maquina_id = m.id
        GROUP BY m.id ORDER BY m.identificador''').fetchall()
    return render_template('maquinas.html', maquinas=lista)


@bp.post('/maquinas/<int:maquina_id>/alternar')
@login_obrigatorio
def alternar_maquina(maquina_id):
    db = get_db()
    db.execute('UPDATE maquinas SET ativa = 1 - ativa WHERE id = ?', (maquina_id,))
    db.commit()
    return redirect(url_for('painel.maquinas'))
