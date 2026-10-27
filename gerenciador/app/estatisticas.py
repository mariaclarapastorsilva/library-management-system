"""Página de estatísticas de uso do painel."""
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request

from .db import get_db
from .painel import login_obrigatorio

bp = Blueprint('estatisticas', __name__, url_prefix='/painel/estatisticas')

DIAS_SEMANA = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
MINUTOS = "(julianday(s.saida) - julianday(s.entrada)) * 1440"


def _data(texto, padrao):
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return padrao


@bp.route('/')
@login_obrigatorio
def pagina():
    hoje = date.today()
    fim = _data(request.args.get('fim'), hoje)
    inicio = _data(request.args.get('inicio'), fim - timedelta(days=29))
    if inicio > fim:
        inicio, fim = fim, inicio
    periodo = (f'{inicio} 00:00:00', f'{fim} 23:59:59')
    onde = 'WHERE s.entrada BETWEEN ? AND ?'
    db = get_db()

    def consulta(sql):
        return db.execute(sql, periodo).fetchall()

    totais = consulta(f'''SELECT COUNT(*) AS sessoes, COUNT(DISTINCT s.usuario_id) AS alunos,
                                 SUM({MINUTOS}) AS minutos, AVG({MINUTOS}) AS media
                          FROM sessoes s {onde}''')[0]

    por_dia = {r[0]: r[1] for r in consulta(
        f'SELECT substr(s.entrada, 1, 10), COUNT(*) FROM sessoes s {onde} GROUP BY 1')}
    dias = [inicio + timedelta(days=i) for i in range((fim - inicio).days + 1)]
    serie_dias = [(d.strftime('%d/%m'), por_dia.get(d.isoformat(), 0)) for d in dias]

    por_hora = {r[0]: r[1] for r in consulta(
        f"SELECT CAST(substr(s.entrada, 12, 2) AS INTEGER), COUNT(*) FROM sessoes s {onde} GROUP BY 1")}
    horas = range(min(por_hora, default=8), max(por_hora, default=21) + 1)
    serie_horas = [(f'{h}h', por_hora.get(h, 0)) for h in horas]

    por_semana = {int(r[0]): r[1] for r in consulta(
        f"SELECT strftime('%w', s.entrada), COUNT(*) FROM sessoes s {onde} GROUP BY 1")}
    # Segunda primeiro, domingo por último, como na rotina da biblioteca.
    serie_semana = [(DIAS_SEMANA[d], por_semana.get(d, 0)) for d in (1, 2, 3, 4, 5, 6, 0)]

    cursos = consulta(f'''SELECT u.curso AS nome, COUNT(*) AS sessoes, COUNT(DISTINCT u.id) AS alunos,
                                 COALESCE(SUM({MINUTOS}), 0) / 60.0 AS horas
                          FROM sessoes s JOIN usuarios u ON u.id = s.usuario_id {onde}
                          GROUP BY u.curso ORDER BY horas DESC''')
    maquinas = consulta(f'''SELECT m.identificador AS nome, COUNT(*) AS sessoes,
                                   COALESCE(SUM({MINUTOS}), 0) / 60.0 AS horas
                            FROM sessoes s JOIN maquinas m ON m.id = s.maquina_id {onde}
                            GROUP BY m.id ORDER BY horas DESC''')

    return render_template('estatisticas.html', inicio=inicio, fim=fim, totais=totais,
                           serie_dias=serie_dias, serie_horas=serie_horas, serie_semana=serie_semana,
                           cursos=cursos, maquinas=maquinas)
