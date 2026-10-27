"""Painel de demonstração com dados fictícios, para apresentar o sistema.

Uso:
    python demo.py             cria database/demo.db (se ainda não existir) e abre o painel
    python demo.py --recriar   gera os dados de novo

O painel abre em http://127.0.0.1:5001/painel/ com o usuário "demo" e a senha "demo1234".
Os alunos e sessões são inventados; o banco real (biblioteca.db) não é tocado.
"""
import argparse
import os
import random
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import BASE, CAMINHO_PADRAO, FORMATO_DATA, conectar, criar_banco

CAMINHO_DEMO = os.path.join(BASE, 'database', 'demo.db')
PORTA_DEMO = 5001

NOMES = ['Ana', 'Beatriz', 'Bruno', 'Camila', 'Carlos', 'Daniel', 'Eduarda', 'Felipe', 'Gabriela',
         'Gustavo', 'Helena', 'Igor', 'Isabela', 'João', 'Júlia', 'Larissa', 'Lucas', 'Mariana',
         'Mateus', 'Natália', 'Pedro', 'Rafaela', 'Rodrigo', 'Sofia', 'Thiago', 'Vinícius', 'Yasmin']
SOBRENOMES = ['Almeida', 'Barbosa', 'Cardoso', 'Costa', 'Dias', 'Ferreira', 'Gomes', 'Lima',
              'Martins', 'Melo', 'Moreira', 'Oliveira', 'Pereira', 'Ribeiro', 'Rocha', 'Santos',
              'Silva', 'Souza', 'Teixeira']
CURSOS = [('Técnico em Informática', 30), ('Engenharia', 20), ('Licenciatura em Matemática', 15),
          ('Tecnologia em Sistemas', 20), ('Pedagogia', 15)]

# Chance de uma máquina livre receber um aluno a cada 15 minutos, por hora do dia.
PROCURA = {7: .03, 8: .08, 9: .12, 10: .2, 11: .2, 12: .1, 13: .12, 14: .2, 15: .2, 16: .18,
           17: .12, 18: .14, 19: .2, 20: .18, 21: .06}
PROCURA_DIA = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: .8, 5: .3, 6: 0}  # segunda = 0


def gerar(caminho, semanas=6, maquinas=12, alunos=90, semente=42):
    sorteio = random.Random(semente)
    criar_banco(caminho)
    con = conectar(caminho)

    con.execute("INSERT INTO administradores (usuario, senha_hash) VALUES ('demo', ?)",
                (generate_password_hash('demo1234'),))
    ids_maquinas = [con.execute('INSERT INTO maquinas (identificador, descricao) VALUES (?, ?)',
                                (f'BIB-{n:02d}', f'Bancada {(n + 1) // 2}')).lastrowid
                    for n in range(1, maquinas + 1)]
    nomes_cursos, pesos = zip(*CURSOS)
    prontuarios = sorted(sorteio.sample(range(3000000, 3100000), alunos))
    ids_alunos = [con.execute('INSERT INTO usuarios (prontuario, nome, curso) VALUES (?, ?, ?)',
                              (f'JC{p}', f'{sorteio.choice(NOMES)} {sorteio.choice(SOBRENOMES)}',
                               sorteio.choices(nomes_cursos, pesos)[0])).lastrowid
                  for p in prontuarios]

    agora = datetime.now()
    sessoes = []
    usando_agora = set()
    for dia in range(semanas * 7, -1, -1):
        data = date.today() - timedelta(days=dia)
        for maquina in ids_maquinas:
            momento = datetime.combine(data, datetime.min.time()).replace(hour=7, minute=30)
            while momento.hour < 22 and momento < agora:
                if sorteio.random() < PROCURA.get(momento.hour, 0) * PROCURA_DIA[data.weekday()]:
                    duracao = timedelta(minutes=max(10, sorteio.gauss(65, 35)))
                    saida = min(momento + duracao, momento.replace(hour=22, minute=0))
                    aluno = sorteio.choice(ids_alunos)
                    if saida > agora:
                        # Sessão em andamento: aparece em "Sessões ativas", sem repetir aluno.
                        aluno = sorteio.choice([a for a in ids_alunos if a not in usando_agora])
                        usando_agora.add(aluno)
                    sessoes.append((aluno, maquina, momento.strftime(FORMATO_DATA),
                                    None if saida > agora else saida.strftime(FORMATO_DATA)))
                    momento = saida + timedelta(minutes=sorteio.choice([5, 10, 15, 30]))
                else:
                    momento += timedelta(minutes=15)
    con.executemany('INSERT INTO sessoes (usuario_id, maquina_id, entrada, saida) VALUES (?, ?, ?, ?)', sessoes)
    con.commit()
    con.close()
    return len(sessoes)


if __name__ == '__main__':
    args = argparse.ArgumentParser(description='Painel de demonstração com dados fictícios.')
    args.add_argument('--recriar', action='store_true', help='apaga a demonstração e gera de novo')
    opcoes = args.parse_args()

    if os.path.abspath(CAMINHO_DEMO) == os.path.abspath(CAMINHO_PADRAO):
        raise SystemExit('O banco de demonstração não pode ser o banco real.')
    if opcoes.recriar:
        for sufixo in ('', '-wal', '-shm'):
            if os.path.exists(CAMINHO_DEMO + sufixo):
                os.remove(CAMINHO_DEMO + sufixo)
    if not os.path.exists(CAMINHO_DEMO):
        print(f'Gerando dados fictícios... {gerar(CAMINHO_DEMO)} sessões criadas.')

    print(f'\nPainel de demonstração: http://127.0.0.1:{PORTA_DEMO}/painel/')
    print('Usuário: demo   Senha: demo1234   (Ctrl+C para encerrar)\n')
    create_app({'DATABASE': CAMINHO_DEMO}).run(host='127.0.0.1', port=PORTA_DEMO)
