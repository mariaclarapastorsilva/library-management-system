# 📚 Library Management System

Sistema de gerenciamento de biblioteca desenvolvido com **Python**, **Flask** e **SQL**.

## Sobre o projeto

Aplicação web para controlar o acervo de uma biblioteca: cadastro de livros, usuários, empréstimos e devoluções.

## Funcionalidades planejadas

- [ ] Cadastro, edição e remoção de livros (título, autor, ISBN, editora, ano, categoria, quantidade)
- [ ] Cadastro de usuários/leitores
- [ ] Registro de empréstimos e devoluções
- [ ] Controle de disponibilidade de exemplares
- [ ] Cálculo de atrasos e multas
- [ ] Busca e filtros no acervo
- [ ] Autenticação de bibliotecários (login)
- [ ] Relatórios (livros mais emprestados, empréstimos em atraso)

## Tecnologias

- Python 3
- Flask
- SQL (SQLite / MySQL)
- HTML, CSS e Jinja2

## Estrutura (prevista)

```
library-management-system/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
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
