# 🖥️ Library Management System — Controle de Acesso às Máquinas

Sistema para registrar o login dos usuários nos computadores da biblioteca e gerar relatórios de uso para o gerenciador.

Desenvolvido com **Python**, **Flask** e **SQL**.

## Sobre o projeto

Ao usar uma máquina, o usuário faz login informando seus dados. O sistema registra automaticamente o **horário de entrada** e, ao encerrar a sessão, o **horário de saída**. O gerenciador acessa um painel para consultar e exportar relatórios.

## Arquitetura

O projeto é dividido em **duas partes** que se comunicam pela rede:

```
┌──────────────────────────┐            ┌──────────────────────────────┐
│  CLIENTE (máquina 01)    │──┐         │        GERENCIADOR           │
├──────────────────────────┤  │  HTTP   │  (servidor central)          │
│  CLIENTE (máquina 02)    │──┼───────▶ │  - API Flask                 │
├──────────────────────────┤  │  (API)  │  - Banco de dados SQL        │
│  CLIENTE (máquina N)     │──┘         │  - Painel web + relatórios   │
└──────────────────────────┘            └──────────────────────────────┘
```

### 1. Gerenciador (servidor)

Roda em um computador central da biblioteca/CTI. É responsável por:

- [ ] API que recebe os registros de entrada e saída enviados pelos clientes
- [ ] Banco de dados com usuários, máquinas e sessões
- [ ] Login do gerenciador (acesso restrito)
- [ ] Painel com as sessões ativas (quem está usando cada máquina agora)
- [ ] Cadastro das máquinas gerenciadas
- [ ] Histórico de acessos com filtros (data, curso, prontuário, máquina)
- [ ] Relatório com nome, curso, prontuário, máquina, entrada e saída
- [ ] Exportar relatório em PDF / CSV / Excel

### 2. Cliente (máquina gerenciada)

Programa instalado em cada computador de uso dos usuários. É responsável por:

- [ ] Abrir automaticamente ao iniciar a sessão do computador
- [ ] Tela de login em que o usuário informa nome, curso e prontuário
- [ ] Bloquear o uso da máquina até o login ser feito
- [ ] Enviar ao gerenciador o login (prontuário + identificação da máquina + horário de entrada)
- [ ] Botão de logout que envia o horário de saída
- [ ] Registrar a saída também ao desligar/reiniciar ou encerrar a sessão do Windows/Linux
- [ ] Guardar os registros localmente se o servidor estiver fora do ar e enviar depois

## Dados registrados

| Campo | Descrição |
|---|---|
| Nome | Nome completo do usuário |
| Curso | Curso do usuário |
| Prontuário | Número de prontuário (identificação no IFSP) |
| Máquina | Identificação do computador utilizado |
| Entrada | Data e hora do login |
| Saída | Data e hora do logout |

## Tecnologias

| Parte | Tecnologias |
|---|---|
| Gerenciador | Python 3, Flask, SQL (SQLite / MySQL), HTML, CSS, Jinja2 |
| Cliente | Python 3 (interface com Tkinter), requests |

## Banco de dados (previsto)

```sql
CREATE TABLE usuarios (
    prontuario  VARCHAR(20) PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    curso       VARCHAR(100) NOT NULL
);

CREATE TABLE maquinas (
    id          VARCHAR(50) PRIMARY KEY,   -- ex.: hostname
    descricao   VARCHAR(100)
);

CREATE TABLE sessoes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prontuario  VARCHAR(20) NOT NULL REFERENCES usuarios(prontuario),
    maquina_id  VARCHAR(50) NOT NULL REFERENCES maquinas(id),
    entrada     DATETIME NOT NULL,
    saida       DATETIME
);
```

## Estrutura (prevista)

```
library-management-system/
├── gerenciador/            # servidor central
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── api.py          # rotas que recebem dados dos clientes
│   │   ├── painel.py       # rotas do painel web
│   │   ├── relatorios.py
│   │   ├── templates/
│   │   └── static/
│   ├── database/
│   │   └── schema.sql
│   ├── requirements.txt
│   └── run.py
├── cliente/                # programa das máquinas gerenciadas
│   ├── cliente.py          # tela de login e comunicação com a API
│   ├── config.ini          # endereço do servidor e ID da máquina
│   └── requirements.txt
└── README.md
```

## Como executar

### Gerenciador

```bash
git clone https://github.com/mariaclarapastorsilva/library-management-system.git
cd library-management-system/gerenciador
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### Cliente (em cada máquina)

```bash
cd library-management-system/cliente
pip install -r requirements.txt
# configure o endereço do gerenciador em config.ini
python cliente.py
```

## Autora

**Maria Clara Pastor** — Análise e Desenvolvimento de Sistemas, IFSP Campus Jacareí
