# 🖥️ Library Management System — Controle de Acesso às Máquinas

Sistema para registrar o login dos usuários nos computadores da biblioteca e gerar relatórios de uso para o gerenciador.

Desenvolvido com **Python**, **Flask** e **SQL**.

## Sobre o projeto

Ao usar uma máquina, o usuário faz login informando seus dados. O sistema registra automaticamente o **horário de entrada** e, ao encerrar a sessão, o **horário de saída**. O gerenciador acessa um painel para consultar e exportar relatórios.

## Dados registrados

| Campo | Descrição |
|---|---|
| Nome | Nome completo do usuário |
| Curso | Curso do usuário |
| Prontuário | Número de prontuário (identificação no IFSP) |
| Máquina | Identificação do computador utilizado |
| Entrada | Data e hora do login |
| Saída | Data e hora do logout |

## Funcionalidades planejadas

### Usuário
- [ ] Tela de login na máquina (nome, curso, prontuário)
- [ ] Registro automático do horário de entrada
- [ ] Botão de logout com registro do horário de saída

### Gerenciador
- [ ] Login do gerenciador (acesso restrito)
- [ ] Visualizar sessões ativas (quem está usando cada máquina agora)
- [ ] Histórico de acessos com filtros (data, curso, prontuário, máquina)
- [ ] Gerar relatório com nome, curso, prontuário, entrada e saída
- [ ] Exportar relatório em PDF / CSV / Excel

## Tecnologias

- Python 3
- Flask
- SQL (SQLite / MySQL)
- HTML, CSS e Jinja2

## Banco de dados (previsto)

```sql
CREATE TABLE usuarios (
    prontuario  VARCHAR(20) PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    curso       VARCHAR(100) NOT NULL
);

CREATE TABLE sessoes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prontuario  VARCHAR(20) NOT NULL REFERENCES usuarios(prontuario),
    maquina     VARCHAR(50) NOT NULL,
    entrada     DATETIME NOT NULL,
    saida       DATETIME
);
```

## Estrutura (prevista)

```
library-management-system/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── relatorios.py
│   ├── templates/
│   └── static/
├── database/
│   └── schema.sql
├── requirements.txt
├── run.py
└── README.md
```

## Como executar

```bash
git clone https://github.com/mariaclarapastorsilva/library-management-system.git
cd library-management-system
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

## Autora

**Maria Clara Pastor** — Análise e Desenvolvimento de Sistemas, IFSP Campus Jacareí
